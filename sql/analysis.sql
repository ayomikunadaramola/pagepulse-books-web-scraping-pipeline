-- Total Number of Books
SELECT COUNT(*) AS total_books
FROM book_listings;

-- Average book price
SELECT
    ROUND(AVG(price_gbp)::numeric, 2) AS average_price_gbp
FROM book_listings;

-- Minimum and Maximum Prices
SELECT
    MIN(price_gbp) AS lowest_price_gbp,
    MAX(price_gbp) AS highest_price_gbp
FROM book_listings;

-- Number of Books by Rating
SELECT
    rating,
    COUNT(*) AS number_of_books
FROM book_listings
GROUP BY rating
ORDER BY rating DESC;

-- Ten most expensive books 
SELECT
    title,
    price_gbp,
    rating
FROM book_listings
ORDER BY price_gbp DESC
LIMIT 10;

-- Ten cheapest books
SELECT
    title,
    price_gbp,
    rating
FROM book_listings
ORDER BY price_gbp 
LIMIT 10;

-- High-rated affordable books
SELECT
    title,
    price_gbp,
    rating
FROM book_listings
WHERE rating >= 4
  AND price_gbp <= 30
ORDER BY rating DESC, price_gbp;

-- Availability summary 
SELECT
    availability,
    COUNT(*) AS number_of_books
FROM book_listings
GROUP BY availability
ORDER BY number_of_books DESC; 

-- Average Price by Rating 
SELECT
    rating,
    ROUND(AVG(price_gbp)::numeric, 2) AS average_price_gbp
FROM book_listings
GROUP BY rating
ORDER BY rating DESC;

-- Books above the overall average price
SELECT
    title,
    price_gbp,
    rating
FROM book_listings
WHERE price_gbp > (
    SELECT AVG(price_gbp)
    FROM book_listings
)
ORDER BY price_gbp DESC;

