"""PagePulse Books: reusable static scraping and transformation functions."""
from __future__ import annotations
import os
from dotenv import load_dotenv
from psycopg2.extras import execute_values
import psycopg2

import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
START_URL = urljoin(BASE_URL, "catalogue/page-1.html")
USER_AGENT = "PagePulseStudentBot/1.0 (educational web-scraping project)"
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
FINAL_COLUMNS = [
    "title", "category", "price_gbp", "price_display", "availability",
    "rating", "product_url", "image_url", "source_website",
    "source_page", "scraped_at",
]
LOG = logging.getLogger(__name__)


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def check_robots_txt(session: requests.Session, target_url: str = START_URL) -> float:
    """Check published crawl rules; fail closed if rules cannot be assessed."""
    robots_url = urljoin(BASE_URL, "robots.txt")
    response = session.get(robots_url, timeout=30)
    if response.status_code == 404:
        LOG.info("No robots.txt published; applying a polite request delay.")
        return 1.0
    response.raise_for_status()
    parser = RobotFileParser()
    parser.parse(response.text.splitlines())
    if not parser.can_fetch(USER_AGENT, target_url):
        raise PermissionError(f"robots.txt disallows fetching {target_url}")
    return max(float(parser.crawl_delay(USER_AGENT) or 0), 1.0)


def scrape_catalogue_page(
    page_url: str, session: requests.Session
) -> tuple[list[dict], str | None]:
    response = session.get(page_url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    records = []
    for book in soup.select("article.product_pod"):
        title = book.select_one("h3 a")
        price = book.select_one("p.price_color")
        availability = book.select_one("p.instock.availability")
        rating = book.select_one("p.star-rating")
        image = book.select_one("img.thumbnail")
        rating_classes = rating.get("class", []) if rating else []
        rating_raw = next(
            (x for x in rating_classes if x != "star-rating"), None)
        records.append({
            "title": title.get("title") if title else None,
            "price_raw": price.get_text(strip=True) if price else None,
            "availability_raw": availability.get_text(" ", strip=True) if availability else None,
            "rating_raw": rating_raw,
            "product_url": urljoin(page_url, title.get("href")) if title else None,
            "image_url": urljoin(page_url, image.get("src")) if image else None,
            "source_page": page_url,
            "scraped_at": datetime.now(timezone.utc),
        })
    if not records:
        raise ValueError(
            f"No book cards found at {page_url}; check page structure.")
    next_link = soup.select_one("li.next a")
    return records, urljoin(page_url, next_link.get("href")) if next_link else None


def scrape_all_pages(
    session: requests.Session, start_url: str = START_URL,
    max_pages: int | None = None, delay: float = 1.0
) -> list[dict]:
    if max_pages is not None and max_pages < 1:
        raise ValueError("max_pages must be at least 1")
    records, seen, page_url = [], set(), start_url
    while page_url and (max_pages is None or len(seen) < max_pages):
        if page_url in seen:
            raise ValueError(f"Pagination loop detected at {page_url}")
        if urlparse(page_url).netloc != urlparse(BASE_URL).netloc:
            raise ValueError(f"Unexpected pagination host: {page_url}")
        seen.add(page_url)
        page_records, page_url = scrape_catalogue_page(page_url, session)
        records.extend(page_records)
        LOG.info("Scraped page %d; total books: %d", len(seen), len(records))
        if page_url and (max_pages is None or len(seen) < max_pages):
            time.sleep(delay)
    return records


def scrape_book_category(product_url: str, session: requests.Session) -> str | None:
    if urlparse(product_url).netloc != urlparse(BASE_URL).netloc:
        raise ValueError(f"Unexpected product host: {product_url}")
    response = session.get(product_url, timeout=30)
    response.raise_for_status()
    crumbs = BeautifulSoup(response.text, "lxml").select("ul.breadcrumb li")
    return crumbs[2].get_text(strip=True) if len(crumbs) >= 3 else None


def transform_books(
    raw_records: list[dict], session: requests.Session,
    category_delay: float = 0.5
) -> pd.DataFrame:
    if not raw_records:
        raise ValueError("No raw records to transform.")
    df = pd.DataFrame(raw_records).copy()
    df["title"] = df["title"].astype("string").str.strip()
    df["price_gbp"] = pd.to_numeric(
        df["price_raw"]
        .astype("string")
        .str.replace(r"[^\d.]", "", regex=True),
        errors="coerce",
    )
    df["availability"] = (
        df["availability_raw"].astype("string")
        .str.replace(r"\\s+", " ", regex=True).str.strip().str.title()
    )
    df["rating"] = df["rating_raw"].map(RATING_MAP).astype("Int64")
    df["scraped_at"] = pd.to_datetime(
        df["scraped_at"], utc=True, errors="coerce")
    df["source_website"] = "Books to Scrape"
    df["price_display"] = df["price_gbp"].map(
        lambda x: f"£{x:.2f}" if pd.notna(x) else None
    )
    categories = []
    for i, product_url in enumerate(df["product_url"], start=1):
        categories.append(scrape_book_category(
            product_url, session) if pd.notna(product_url) else None)
        if i < len(df):
            time.sleep(category_delay)
    df["category"] = categories
    return df[FINAL_COLUMNS]


def validate_books(df: pd.DataFrame) -> None:
    missing = set(FINAL_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if df.empty:
        raise ValueError("Cleaned dataset is empty.")
    required = ["title", "category", "price_gbp", "price_display",
                "availability", "rating", "product_url", "scraped_at"]
    if df[required].isna().any().any():
        raise ValueError(
            f"Missing required values: {df[required].isna().sum().to_dict()}")
    if df["title"].astype(str).str.strip().eq("").any():
        raise ValueError("Blank book titles found.")
    if df["product_url"].duplicated().any():
        raise ValueError("Duplicate product URLs found.")
    if not df["price_gbp"].gt(0).all():
        raise ValueError("Invalid book prices found.")
    if not df["rating"].between(1, 5).all():
        raise ValueError("Invalid book ratings found.")
    if not df["product_url"].map(
        lambda u: urlparse(str(u)).scheme in ("http", "https")
    ).all():
        raise ValueError("Invalid product URLs found.")


def save_raw_data(records: list[dict], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / \
        f"books_raw_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}.csv"
    pd.DataFrame(records).to_csv(path, index=False)
    return path


def save_cleaned_data(df: pd.DataFrame, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "books_cleaned.csv"
    df.to_csv(path, index=False)
    return path


def load_to_postgres(df: pd.DataFrame) -> int:
    """
    Load validated book records into PostgreSQL.

    Uses product_url as the unique identifier to prevent
    duplicate records when the pipeline is executed again.

    Returns the number of records inserted or updated.
    """

    load_dotenv()

    validate_books(df)

    required_env = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]

    missing_env = [
        key for key in required_env
        if not os.getenv(key)
    ]

    if missing_env:
        raise ValueError(
            f"Missing database configuration: {missing_env}"
        )

    columns = [
        "title",
        "category",
        "price_gbp",
        "price_display",
        "availability",
        "rating",
        "product_url",
        "image_url",
        "source_website",
        "source_page",
        "scraped_at",
    ]

    records = []

    for row in df[columns].itertuples(
        index=False,
        name=None,
    ):
        records.append(
            tuple(
                value.item()
                if hasattr(value, "item")
                else value
                for value in row
            )
        )

    insert_query = """
    INSERT INTO public.book_listings (
        title,
        category,
        price_gbp,
        price_display,
        availability,
        rating,
        product_url,
        image_url,
        source_website,
        source_page,
        scraped_at
    )
    VALUES %s

    ON CONFLICT (product_url)
    DO UPDATE SET
    title = EXCLUDED.title,
    category = EXCLUDED.category,
    price_gbp = EXCLUDED.price_gbp,
    price_display = EXCLUDED.price_display,
    availability = EXCLUDED.availability,
    rating = EXCLUDED.rating,
    image_url = EXCLUDED.image_url,
    source_website = EXCLUDED.source_website,
    source_page = EXCLUDED.source_page,
    scraped_at = EXCLUDED.scraped_at;
    """

    connection = None

    try:
        connection = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )

        with connection.cursor() as cursor:
            execute_values(
                cursor,
                insert_query,
                records,
                page_size=100,
            )

        connection.commit()

        LOG.info(
            "Successfully loaded %d book records into PostgreSQL",
            len(records),
        )

        return len(records)

    except Exception:

        if connection is not None:
            connection.rollback()

            LOG.exception(
                "Failed to load book records into PostgreSQL"
            )

            raise

    finally:

        if connection is not None:
            connection.close()
