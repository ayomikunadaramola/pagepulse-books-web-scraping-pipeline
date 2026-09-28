import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from selenium.webdriver.common.by import By

from src.dynamic_scraper import (
    create_driver,
    extract_books,
    scrape_multiple_pages,
    enrich_books,
    scrape_dynamic_books,
)


def make_book_element(
    title="Test Book",
    price="£25.50",
    availability="In stock",
    rating="Three",
    product_url="catalogue/test-book_1/index.html",
    image_url="media/cache/test-book.jpg",
):
    """Create a mocked Selenium book element."""

    book = MagicMock()

    link = MagicMock()
    link.get_attribute.side_effect = lambda name: {
        "title": title,
        "href": product_url,
    }.get(name)

    price_element = MagicMock()
    price_element.text = price

    availability_element = MagicMock()
    availability_element.text = availability

    rating_element = MagicMock()
    rating_element.get_attribute.return_value = f"star-rating {rating}"

    image_element = MagicMock()
    image_element.get_attribute.return_value = image_url

    def find_element(by, selector):
        elements = {
            (By.CSS_SELECTOR, "h3 a"): link,
            (By.CSS_SELECTOR, "p.price_color"): price_element,
            (By.CSS_SELECTOR, "p.instock.availability"): availability_element,
            (By.CSS_SELECTOR, "p.star-rating"): rating_element,
            (By.CSS_SELECTOR, "div.image_container img"): image_element,
        }

        return elements[(by, selector)]

    book.find_element.side_effect = find_element

    return book


def make_books_dataframe():
    """Create a sample DataFrame representing catalogue extraction."""

    return pd.DataFrame(
        [
            {
                "title": "Test Book One",
                "price_gbp": 25.50,
                "price_display": "£25.50",
                "availability": "In stock",
                "rating": 3,
                "product_url": (
                    "https://books.toscrape.com/"
                    "catalogue/test-book-one_1/index.html"
                ),
                "image_url": (
                    "https://books.toscrape.com/"
                    "media/test-book-one.jpg"
                ),
            },
            {
                "title": "Test Book Two",
                "price_gbp": 40.00,
                "price_display": "£40.00",
                "availability": "In stock",
                "rating": 5,
                "product_url": (
                    "https://books.toscrape.com/"
                    "catalogue/test-book-two_2/index.html"
                ),
                "image_url": (
                    "https://books.toscrape.com/"
                    "media/test-book-two.jpg"
                ),
            },
        ]
    )


def test_create_driver_headless():
    """The scraper should create Chrome with configured options."""

    mock_driver = MagicMock()

    with patch(
        "src.dynamic_scraper.webdriver.Chrome",
        return_value=mock_driver,
    ) as chrome:
        result = create_driver()

        assert result is mock_driver
        chrome.assert_called_once()

        options = chrome.call_args.kwargs["options"]

        assert "--headless=new" in options.arguments
        assert "--window-size=1920,1080" in options.arguments
        assert "--disable-gpu" in options.arguments
        assert "--no-sandbox" in options.arguments


def test_extract_books():
    """Selenium elements should be converted into structured records."""

    book = make_book_element()

    result = extract_books([book])

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 1

    row = result.iloc[0]

    assert row["title"] == "Test Book"
    assert row["price_gbp"] == pytest.approx(25.50)
    assert row["price_display"] == "£25.50"
    assert row["availability"] == "In stock"
    assert row["rating"] == 3
    assert row["product_url"].startswith("https://")
    assert row["image_url"].startswith("https://")


def test_extract_books_multiple_records():
    """Multiple Selenium book elements should produce multiple rows."""

    books = [
        make_book_element(
            title="Book One",
            price="£10.00",
            rating="One",
        ),
        make_book_element(
            title="Book Two",
            price="£20.00",
            rating="Five",
        ),
    ]

    result = extract_books(books)

    assert len(result) == 2
    assert result.iloc[0]["title"] == "Book One"
    assert result.iloc[1]["title"] == "Book Two"
    assert result.iloc[0]["rating"] == 1
    assert result.iloc[1]["rating"] == 5


def test_extract_books_empty_input():
    """No Selenium elements should produce an empty DataFrame."""

    result = extract_books([])

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_scrape_multiple_pages():
    """The scraper should combine records from multiple pages."""

    driver = MagicMock()

    page_one = pd.DataFrame(
        [{"title": "Book One"}]
    )

    page_two = pd.DataFrame(
        [{"title": "Book Two"}]
    )

    next_link = MagicMock()
    next_link.get_attribute.return_value = (
        "https://books.toscrape.com/catalogue/page-2.html"
    )

    driver.find_element.return_value = next_link

    with (
        patch(
            "src.dynamic_scraper.load_catalogue",
            side_effect=[["element1"], ["element2"]],
        ),
        patch(
            "src.dynamic_scraper.extract_books",
            side_effect=[page_one, page_two],
        ),
    ):
        result = scrape_multiple_pages(
            driver,
            max_pages=2,
        )

        assert len(result) == 2
        assert result["title"].tolist() == [
            "Book One",
            "Book Two",
        ]


def test_scrape_multiple_pages_stops_when_no_next_page():
    """Pagination should stop gracefully if a next link is absent."""

    driver = MagicMock()
    driver.find_element.side_effect = Exception("No next page")

    page_one = pd.DataFrame(
        [{"title": "Book One"}]
    )

    with (
        patch(
            "src.dynamic_scraper.load_catalogue",
            return_value=["element1"],
        ),
        patch(
            "src.dynamic_scraper.extract_books",
            return_value=page_one,
        ),
    ):
        result = scrape_multiple_pages(
            driver,
            max_pages=3,
        )

        assert len(result) == 1
        assert result.iloc[0]["title"] == "Book One"


def test_enrich_books():
    """Product pages should enrich books with category metadata."""

    driver = MagicMock()
    df = make_books_dataframe()

    breadcrumb_one = [
        MagicMock(),
        MagicMock(),
        MagicMock(),
    ]
    breadcrumb_one[-2].text = "Fiction"

    breadcrumb_two = [
        MagicMock(),
        MagicMock(),
        MagicMock(),
    ]
    breadcrumb_two[-2].text = "History"

    mock_wait = MagicMock()
    mock_wait.until.side_effect = [
        breadcrumb_one,
        breadcrumb_two,
    ]

    driver.current_url = (
        "https://books.toscrape.com/catalogue/product.html"
    )

    with patch(
        "src.dynamic_scraper.WebDriverWait",
        return_value=mock_wait,
    ):
        result = enrich_books(driver, df)

        assert len(result) == 2

        assert result["category"].tolist() == [
            "Fiction",
            "History",
        ]

        assert (
            result["source_website"]
            == "Books to Scrape"
        ).all()

        assert "source_page" in result.columns
        assert "scraped_at" in result.columns

        assert driver.get.call_count == 2


def test_scrape_dynamic_books_complete_workflow():
    """The complete dynamic workflow should return enriched records."""

    driver = MagicMock()

    extracted = make_books_dataframe()

    enriched = extracted.copy()
    enriched["category"] = ["Fiction", "History"]
    enriched["source_website"] = "Books to Scrape"
    enriched["source_page"] = [
        "https://example.com/1",
        "https://example.com/2",
    ]
    enriched["scraped_at"] = [
        "2026-09-28T10:00:00+00:00",
        "2026-09-28T10:01:00+00:00",
    ]

    with (
        patch(
            "src.dynamic_scraper.create_driver",
            return_value=driver,
        ),
        patch(
            "src.dynamic_scraper.scrape_multiple_pages",
            return_value=extracted,
        ) as scrape_pages,
        patch(
            "src.dynamic_scraper.enrich_books",
            return_value=enriched,
        ) as enrich,
    ):
        result = scrape_dynamic_books(max_pages=2)

        assert len(result) == 2
        assert result["category"].tolist() == [
            "Fiction",
            "History",
        ]

        scrape_pages.assert_called_once_with(
            driver,
            max_pages=2,
        )

        enrich.assert_called_once_with(
            driver,
            extracted,
        )

        driver.quit.assert_called_once()


def test_scrape_dynamic_books_closes_driver_on_failure():
    """Chrome must still close if scraping fails."""

    driver = MagicMock()

    with (
        patch(
            "src.dynamic_scraper.create_driver",
            return_value=driver,
        ),
        patch(
            "src.dynamic_scraper.scrape_multiple_pages",
            side_effect=RuntimeError("Scraping failed"),
        ),
    ):
        with pytest.raises(
            RuntimeError,
            match="Scraping failed",
        ):
            scrape_dynamic_books(max_pages=1)

            driver.quit.assert_called_once()
