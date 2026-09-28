"""PagePulse Books end-to-end ETL pipeline."""

from src.dynamic_scraper import scrape_dynamic_books

import logging
from pathlib import Path

from src.static_scraper import (
    create_session,
    scrape_all_pages,
    transform_books,
    validate_books,
    load_to_postgres,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

LOG = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "cleaned_data"
OUTPUT_FILE = OUTPUT_DIR / "books.csv"

MAX_PAGES = 3


def save_cleaned_data(df) -> Path:
    """Save the validated dataset as a CSV file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    LOG.info("Saved cleaned dataset to %s", OUTPUT_FILE)

    return OUTPUT_FILE


def run_dynamic_pipeline(max_pages: int = 3) -> None:
    """Run the PagePulse ETL pipeline using Selenium extraction."""

    LOG.info("Starting PagePulse dynamic ETL pipeline")

    # EXTRACT
    LOG.info("Extracting book listings with Selenium...")
    books = scrape_dynamic_books(max_pages=max_pages)

    LOG.info(
        "Extracted and enriched %d dynamic book records",
        len(books),
    )

    # VALIDATE
    LOG.info("Validating dynamic dataset...")

    if books.empty:
        raise ValueError("Dynamic scraper returned an empty dataset")

    if books["product_url"].duplicated().any():
        raise ValueError("Duplicate product URLs detected")

    missing_values = int(books.isnull().sum().sum())

    if missing_values > 0:
        raise ValueError(
            f"Dynamic dataset contains {missing_values} missing values"
        )

    LOG.info("Dynamic dataset validation successful")

    # SAVE
    csv_path = save_cleaned_data(books)

    # LOAD
    LOG.info("Loading dynamic records into PostgreSQL...")
    processed = load_to_postgres(books)

    LOG.info("----------------------------------------")
    LOG.info("PagePulse dynamic ETL pipeline completed")
    LOG.info("Records extracted: %d", len(books))
    LOG.info("Unique URLs: %d", books["product_url"].nunique())
    LOG.info("Categories: %d", books["category"].nunique())
    LOG.info("PostgreSQL rows processed: %d", processed)
    LOG.info("CSV output: %s", csv_path)
    LOG.info("----------------------------------------")


def main() -> None:
    """Run the PagePulse Books ETL pipeline."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    LOG.info("Starting PagePulse Books ETL pipeline")

    session = create_session()

    # EXTRACT
    LOG.info("Extracting book listings...")
    books = scrape_all_pages(
        session,
        max_pages=MAX_PAGES,
    )

    if not books:
        raise RuntimeError("No books were extracted.")

    LOG.info("Extracted %d raw book records", len(books))

    # TRANSFORM
    LOG.info("Transforming book records...")
    df = transform_books(books, session)

    # VALIDATE
    LOG.info("Validating transformed dataset...")
    validate_books(df)

    # SAVE
    csv_path = save_cleaned_data(df)

    # LOAD
    LOG.info("Loading records into PostgreSQL...")
    processed = load_to_postgres(df)

    LOG.info("----------------------------------------")
    LOG.info("PagePulse ETL pipeline completed")
    LOG.info("Raw records extracted: %d", len(books))
    LOG.info("Validated records: %d", len(df))
    LOG.info("PostgreSQL rows processed: %d", processed)
    LOG.info("CSV output: %s", csv_path)
    LOG.info("----------------------------------------")


if __name__ == "__main__":
    main()
