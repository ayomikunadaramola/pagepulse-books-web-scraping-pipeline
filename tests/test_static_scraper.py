import pandas as pd
import pytest
from unittest.mock import patch

from src.static_scraper import (
    FINAL_COLUMNS,
    transform_books,
    validate_books,
)


@pytest.fixture
def raw_books():
    """Sample raw records resembling data returned by the scraper."""
    return [
        {
            "title": "  Test Book One  ",
            "price_raw": "£51.77",
            "availability_raw": "In stock",
            "rating_raw": "Three",
            "product_url": "https://books.toscrape.com/catalogue/test-book-one_1/index.html",
            "image_url": "https://books.toscrape.com/media/test-book-one.jpg",
            "source_page": 1,
            "scraped_at": "2026-09-28T10:00:00",
        },
        {
            "title": "Test Book Two",
            "price_raw": "£25.50",
            "availability_raw": "In stock",
            "rating_raw": "Five",
            "product_url": "https://books.toscrape.com/catalogue/test-book-two_2/index.html",
            "image_url": "https://books.toscrape.com/media/test-book-two.jpg",
            "source_page": 1,
            "scraped_at": "2026-09-28T10:01:00",
        },
    ]


def make_valid_dataframe():
    """Create a minimal valid cleaned dataset for validation tests."""
    data = [
        {
            "title": "Test Book One",
            "category": "Fiction",
            "price_gbp": 51.77,
            "price_display": "£51.77",
            "availability": "In Stock",
            "rating": 3,
            "product_url": "https://books.toscrape.com/book-one.html",
            "image_url": "https://books.toscrape.com/book-one.jpg",
            "source_website": "Books to Scrape",
            "source_page": 1,
            "scraped_at": pd.Timestamp("2026-09-28 10:00:00"),
        },
        {
            "title": "Test Book Two",
            "category": "History",
            "price_gbp": 25.50,
            "price_display": "£25.50",
            "availability": "In Stock",
            "rating": 5,
            "product_url": "https://books.toscrape.com/book-two.html",
            "image_url": "https://books.toscrape.com/book-two.jpg",
            "source_website": "Books to Scrape",
            "source_page": 1,
            "scraped_at": pd.Timestamp("2026-09-28 10:01:00"),
        },
    ]

    return pd.DataFrame(data)[FINAL_COLUMNS]


def test_transform_books(raw_books):
    """Test cleaning and transformation of raw scraped records."""

    with patch(
        "src.static_scraper.scrape_book_category",
        side_effect=["Fiction", "History"],
    ):
        result = transform_books(
            raw_books,
            session=None,
            category_delay=0,
        )

        assert len(result) == 2
        assert list(result.columns) == FINAL_COLUMNS

        # Title cleaning
        assert result.loc[0, "title"] == "Test Book One"

        # Price conversion
        assert result.loc[0, "price_gbp"] == pytest.approx(51.77)
        assert result.loc[0, "price_display"] == "£51.77"

        # Availability transformation
        assert result.loc[0, "availability"] == "In Stock"

        # Rating conversion
        assert result.loc[0, "rating"] == 3
        assert result.loc[1, "rating"] == 5

        # Metadata
        assert result.loc[0, "source_website"] == "Books to Scrape"

        # Category enrichment
        assert result.loc[0, "category"] == "Fiction"
        assert result.loc[1, "category"] == "History"


def test_transform_books_rejects_empty_input():
    """Empty extraction results should not enter the pipeline."""

    with pytest.raises(ValueError, match="No raw records to transform"):
        transform_books([], session=None, category_delay=0)


def test_validate_books_accepts_valid_dataframe():
    """A correctly cleaned dataset should pass validation."""

    df = make_valid_dataframe()

    # Successful validation returns None.
    assert validate_books(df) is None


def test_validate_books_rejects_empty_dataframe():
    """An empty cleaned dataset should fail validation."""

    df = pd.DataFrame(columns=FINAL_COLUMNS)

    with pytest.raises(ValueError, match="Cleaned dataset is empty"):
        validate_books(df)


def test_validate_books_rejects_missing_columns():
    """Required pipeline columns must be present."""

    df = make_valid_dataframe().drop(columns=["category"])

    with pytest.raises(ValueError, match="Missing columns"):
        validate_books(df)


def test_validate_books_rejects_missing_required_values():
    """Null values in required fields must fail validation."""

    df = make_valid_dataframe()
    df.loc[0, "category"] = None

    with pytest.raises(ValueError, match="Missing required values"):
        validate_books(df)


def test_validate_books_rejects_blank_titles():
    """Blank book titles must fail validation."""

    df = make_valid_dataframe()
    df.loc[0, "title"] = "   "

    with pytest.raises(ValueError, match="Blank book titles"):
        validate_books(df)


def test_validate_books_rejects_duplicate_urls():
    """Each product URL must uniquely identify a book."""

    df = make_valid_dataframe()
    df.loc[1, "product_url"] = df.loc[0, "product_url"]

    with pytest.raises(ValueError, match="Duplicate product URLs"):
        validate_books(df)


def test_validate_books_rejects_invalid_price():
    """Book prices must be greater than zero."""

    df = make_valid_dataframe()
    df.loc[0, "price_gbp"] = -10.00

    with pytest.raises(ValueError, match="Invalid book prices"):
        validate_books(df)


def test_validate_books_rejects_invalid_rating():
    """Ratings must remain within the Books to Scrape 1–5 range."""

    df = make_valid_dataframe()
    df.loc[0, "rating"] = 6

    with pytest.raises(ValueError, match="Invalid book ratings"):
        validate_books(df)


def test_validate_books_rejects_invalid_product_url():
    """Product URLs must use HTTP or HTTPS."""

    df = make_valid_dataframe()
    df.loc[0, "product_url"] = "not-a-valid-url"

    with pytest.raises(ValueError, match="Invalid product URLs"):
        validate_books(df)
