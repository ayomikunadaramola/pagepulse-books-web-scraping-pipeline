def main():

    books = scrape_books()

    books = clean_books(books)

    save_csv(books)

    load_postgres(books)

if __name__ == "__main__":
    main()