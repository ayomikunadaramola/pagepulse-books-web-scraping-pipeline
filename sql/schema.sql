DROP TABLE IF EXISTS public.book_listings;
CREATE TABLE public.book_listings (
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    price_gbp NUMERIC(8,2) NOT NULL,
    price_display TEXT,
    availability TEXT,
    rating INTEGER,
    product_url TEXT NOT NULL UNIQUE,
    image_url TEXT,
    source_website VARCHAR(100) NOT NULL,
    source_page TEXT,
    scraped_at TIMESTAMPTZ NOT NULL

);