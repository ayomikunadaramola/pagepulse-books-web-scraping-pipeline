# 📚 PagePulse Books Limited – End-to-End Web Scraping Data Pipeline

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue?style=for-the-badge&logo=postgresql)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Processing-green?style=for-the-badge&logo=pandas)
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-Web%20Scraping-orange?style=for-the-badge)
![VS%20Code](https://img.shields.io/badge/VS_Code-IDE-blue?style=for-the-badge&logo=visualstudiocode)

---

# Project Overview

PagePulse Books Limited is a fictional online bookstore that wants to monitor book prices, stock availability and customer ratings from competitor websites.

To support pricing decisions and market research, the company requires an automated data pipeline capable of extracting book information from the web, cleaning and validating the data, and loading it into PostgreSQL for business analysis.

This project demonstrates a complete **Extract–Transform–Load (ETL)** workflow using Python, BeautifulSoup, Pandas and PostgreSQL.

The project was developed as a beginner-to-intermediate Data Engineering case study for teaching web scraping and data pipeline development.

---

# Business Problem

Book retailers continuously adjust their prices and inventory.

Manually collecting competitor information is:

- Slow
- Error-prone
- Difficult to scale
- Time-consuming

PagePulse Books Limited requires a repeatable process that automatically collects book information from competitor websites and stores it in a structured database for reporting and analysis.

---

# Project Objectives

The project aims to:

- Scrape book information from a public website
- Extract relevant business data
- Clean and standardise the dataset
- Validate the quality of the data
- Load the cleaned data into PostgreSQL
- Perform SQL analysis
- Demonstrate a complete ETL pipeline
- Showcase web scraping best practices

---

# Business Focus

Retail Analytics

---

# Industry

E-Commerce

---

# Project Type

End-to-End Web Scraping ETL Pipeline

---

# Website Scraped

Books to Scrape

https://books.toscrape.com

Books to Scrape is a publicly available website intentionally created for learning web scraping.

---

# Technologies Used

## Programming

- Python 3.12

## Development

- Visual Studio Code
- Jupyter Notebook

## Data Processing

- Pandas

## Web Scraping

- Requests
- BeautifulSoup4

## Database

- PostgreSQL
- pgAdmin 4
- SQLAlchemy
- psycopg2

## Environment Variables

- python-dotenv

## Version Control

- Git
- GitHub

---

# Project Structure

```
pagepulse-books-web-scraping-pipeline/

│
├── data/
│   ├── raw_data/
│   └── cleaned_data/
│
├── logs/
│
├── notebooks/
│   └── book_scraping_pipeline.ipynb
│
├── screenshots/
│
├── sql/
│   ├── schema.sql
│   └── analysis.sql
│
├── src/
│   ├── static_scraper.py
│   ├── dynamic_scraper.py
│   └── etl_pipeline.py
│
├── requirements.txt
├── README.md
├── .env
└── .gitignore
```

---

# ETL Pipeline Architecture

```
Books to Scrape Website

          │

          ▼

Python Requests

          │

          ▼

BeautifulSoup

          │

          ▼

HTML Parsing

          │

          ▼

Pandas DataFrame

          │

          ▼

Cleaning & Validation

          │

          ▼

CSV Export

          │

          ▼

PostgreSQL

          │

          ▼

SQL Business Analysis
```

---

# Project Workflow

## Phase 1 — Project Planning

- Define business problem
- Identify data source
- Design ETL workflow
- Create project structure

---

## Phase 2 — Environment Setup

Created a Python virtual environment.

Installed project dependencies.

Configured:

- Python
- VS Code
- PostgreSQL
- pgAdmin
- Git

---

## Phase 3 — Git & GitHub

Initialised Git.

Created:

- .gitignore
- .gitkeep files

Committed project versions throughout development.

---

## Phase 4 — Website Inspection

Inspected the website using browser developer tools.

Identified:

- Product cards
- HTML elements
- CSS classes
- Product URLs
- Image URLs

---

## Phase 5 — Robots.txt Inspection

Checked whether scraping was permitted.

The website returns HTTP 404 because it does not publish a robots.txt file.

The scraper proceeds responsibly using a polite request rate.

---

## Phase 6 — Static Web Scraping

Extracted:

- Book title
- Price
- Availability
- Rating
- Product URL
- Image URL

using:

- requests
- BeautifulSoup

---

## Phase 7 — Pagination

Implemented pagination.

Visited every catalogue page.

Collected information from:

100 pages

Result:

1000 books

---

## Phase 8 — Raw Dataset Creation

Stored the extracted data inside a Pandas DataFrame.

Saved:

Raw CSV

Timestamped HTML pages

---

## Phase 9 — Data Cleaning

Created a copy of the raw DataFrame.

Performed:

- whitespace removal
- datatype conversion
- price cleaning
- timestamp conversion
- rating mapping
- availability standardisation

---

## Phase 10 — Data Transformation

Created new columns:

- price_gbp
- availability
- rating
- source_website

Converted:

```
£51.77
```

into

```
51.77
```

Converted ratings:

```
One
```

↓

```
1
```

etc.

---

## Phase 11 — Data Validation

Validated:

- Missing values
- Duplicate products
- Invalid prices
- Blank titles
- Invalid URLs
- Rating range

No data quality issues were detected.

---

## Phase 12 — Export Clean Dataset

Saved the cleaned dataset into:

```
data/cleaned_data/
```

---

## Phase 13 — PostgreSQL

Connected Python to PostgreSQL using SQLAlchemy.

Loaded:

1000 records

into:

```
book_listings
```

table.

---

## Phase 14 — SQL Analysis

Performed business analysis using SQL.

Examples:

- Average price
- Highest priced books
- Lowest priced books
- Rating distribution
- Stock availability
- Top expensive books

---

# Dataset

The final dataset contains:

| Column | Description |
|----------|------------|
| title | Book title |
| price_gbp | Price in GBP |
| price_display | Formatted price |
| availability | Stock availability |
| rating | Rating (1–5) |
| product_url | Product page |
| image_url | Book image |
| source_website | Website name |
| source_page | Page scraped |
| scraped_at | Extraction timestamp |

---

# Data Quality Checks

The pipeline validates:

- Missing values
- Duplicate books
- Duplicate URLs
- Invalid prices
- Invalid ratings
- Blank titles
- URL format

---

# SQL Analysis

Example questions answered:

- Which books are the most expensive?
- What is the average book price?
- How many books have a 5-star rating?
- What percentage of books are in stock?
- What is the distribution of ratings?

---

# Skills Demonstrated

- Web Scraping
- ETL Development
- BeautifulSoup
- Requests
- Pandas
- Data Cleaning
- Data Validation
- PostgreSQL
- SQL
- SQLAlchemy
- Git
- GitHub
- Data Engineering
- Data Pipelines

---

# Future Improvements

Potential enhancements include:

- Selenium integration for dynamic websites
- Automatic scheduling
- Incremental loading
- Logging
- Error monitoring
- Docker containerisation
- Apache Airflow orchestration
- Data warehouse integration
- Cloud deployment
- Power BI or Tableau dashboard

---

# Learning Outcomes

Through this project, the following concepts were demonstrated:

- Ethical web scraping
- HTML inspection
- Pagination
- Data extraction
- Data transformation
- Data validation
- PostgreSQL integration
- SQL analysis
- Version control
- Professional project organisation

---

# Author

**Ayomikun Adaramola**

Senior Data Engineer

- Portfolio: [Ayomikun Adaramola](https://ayomikun-adaramola.netlify.app)
- GitHub: `https://github.com/ayomikunadaramola`
- LinkedIn: `https://www.linkedin.com/in/ayomikun-adaramola-/`
- Email: `ayomikunaj@gmail.com`

---

# Acknowledgements

This project uses the publicly available **Books to Scrape** website, which was specifically created for learning and practising web scraping techniques.