"""PagePulse Books: dynamic web scraping with Selenium."""

from datetime import datetime, timezone
from urllib.parse import urljoin

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


START_URL = "https://books.toscrape.com/"


def create_driver(headless: bool = True) -> webdriver.Chrome:
    """Create and configure a Chrome WebDriver."""

    options = Options()

    if headless:
        options.add_argument("--headless=new")

        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        driver = webdriver.Chrome(options=options)

        return driver


def load_catalogue(driver: webdriver.Chrome, url: str = START_URL):
    """Open the catalogue and wait until the book listings are available."""

    driver.get(url)

    wait = WebDriverWait(driver, 15)

    book_elements = wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "article.product_pod")
        )
    )

    return book_elements


def extract_books(book_elements, base_url: str = START_URL) -> pd.DataFrame:
    """Extract structured book data from Selenium catalogue elements."""

    records = []

    for book in book_elements:
        link = book.find_element(By.CSS_SELECTOR, "h3 a")

        title = link.get_attribute("title")
        product_url = urljoin(base_url, link.get_attribute("href"))

        price_text = book.find_element(
            By.CSS_SELECTOR, "p.price_color"
        ).text.strip()

        price_gbp = float(
            price_text.replace("£", "").replace("Â", "").strip()
        )

        availability = book.find_element(
            By.CSS_SELECTOR, "p.instock.availability"
        ).text.strip()

        rating_element = book.find_element(
            By.CSS_SELECTOR, "p.star-rating"
        )

        rating_word = rating_element.get_attribute("class").split()[-1]

        rating_map = {
            "One": 1,
            "Two": 2,
            "Three": 3,
            "Four": 4,
            "Five": 5,
        }

        rating = rating_map.get(rating_word)

        image_element = book.find_element(
            By.CSS_SELECTOR, "div.image_container img"
        )

        image_url = urljoin(
            base_url,
            image_element.get_attribute("src")
        )

        records.append(
            {
                "title": title,
                "price_gbp": price_gbp,
                "price_display": f"£{price_gbp:.2f}",
                "availability": availability,
                "rating": rating,
                "product_url": product_url,
                "image_url": image_url,
            }
        )

    return pd.DataFrame(records)


def scrape_multiple_pages(
    driver: webdriver.Chrome,
    start_url: str = START_URL,
    max_pages: int = 3,
) -> pd.DataFrame:
    """Scrape book listings across multiple catalogue pages with Selenium."""

    all_frames = []
    current_url = start_url

    for page_number in range(1, max_pages + 1):
        book_elements = load_catalogue(driver, current_url)

        page_df = extract_books(
            book_elements,
            base_url=current_url,
        )

        all_frames.append(page_df)

        print(
            f"Scraped page {page_number}: "
            f"{len(page_df)} books"
        )

        if page_number == max_pages:
            break

        try:
            next_link = driver.find_element(
                By.CSS_SELECTOR,
                "li.next a",
            )

            current_url = next_link.get_attribute("href")

        except Exception:
            print("No next page found.")
            break

        if not all_frames:
            return pd.DataFrame()

    return pd.concat(all_frames, ignore_index=True)


def enrich_books(
    driver: webdriver.Chrome,
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Enrich Selenium records using individual product pages."""

    enriched_df = df.copy()

    categories = []
    source_pages = []
    scraped_times = []

    for index, row in enriched_df.iterrows():
        driver.get(row["product_url"])

        wait = WebDriverWait(driver, 15)

        breadcrumb = wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "ul.breadcrumb li")
            )
        )

        category = breadcrumb[-2].text.strip()

        categories.append(category)
        source_pages.append(driver.current_url)
        scraped_times.append(
            datetime.now(timezone.utc).isoformat()
        )

        print(
            f"Enriched {index + 1}/{len(enriched_df)}: "
            f"{row['title']}"
        )

        # These lines MUST be outside the for-loop
    enriched_df["category"] = categories
    enriched_df["source_website"] = "Books to Scrape"
    enriched_df["source_page"] = source_pages
    enriched_df["scraped_at"] = scraped_times

    return enriched_df


def scrape_dynamic_books(max_pages: int = 3) -> pd.DataFrame:
    """
    Run the complete Selenium extraction workflow.

    The function:
    1. Starts Chrome WebDriver.
    2. Scrapes multiple catalogue pages.
    3. Visits individual product pages.
    4. Enriches the extracted records.
    5. Safely closes the browser.
    """

    driver = None

    try:
        print("Starting Selenium dynamic scraper...")

        driver = create_driver()

        # Extract catalogue records
        books_df = scrape_multiple_pages(
            driver,
            max_pages=max_pages,
        )

        print(
            f"Catalogue extraction complete: "
            f"{len(books_df)} books"
        )

        # Enrich using individual product pages
        enriched_df = enrich_books(
            driver,
            books_df,
        )

        print(
            f"Dynamic enrichment complete: "
            f"{len(enriched_df)} books"
        )

        return enriched_df

    finally:
        if driver is not None:
            driver.quit()
            print("Chrome WebDriver closed successfully")
