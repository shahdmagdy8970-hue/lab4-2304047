-- Lab 4 - Part II - Problem 2: the SQL of the new website pages (database: library)
-- Run:  mysql -u root -p library < problem2_Queries.sql
USE library;

-- F2.1 Search books: title keyword (LIKE), price range (BETWEEN), category; cheapest first
SELECT b.book_id, b.title, a.name AS author, c.name AS category, b.price
FROM book b
JOIN author a   ON b.author_id   = a.author_id
JOIN category c ON b.category_id = c.category_id
WHERE b.title LIKE '%the%'
  AND b.price BETWEEN 10 AND 20
  AND b.category_id IN (1, 2, 3)
ORDER BY b.price ASC;

-- F2.2 Catalogue: author, publisher and category names instead of the ids
SELECT b.book_id, b.title, a.name AS author, p.name AS publisher, c.name AS category,
       b.publish_year, b.price
FROM book b
JOIN author a    ON b.author_id    = a.author_id
JOIN publisher p ON b.publisher_id = p.publisher_id
JOIN category c  ON b.category_id  = c.category_id
ORDER BY b.book_id;

-- F2.3 (a) Number of books and average price of each category
SELECT c.name AS category, COUNT(b.book_id) AS books, ROUND(AVG(b.price), 2) AS average_price
FROM category c
LEFT JOIN book b ON b.category_id = c.category_id
GROUP BY c.category_id, c.name
ORDER BY c.name;

-- F2.3 (b) Authors who wrote at least 2 books
SELECT a.name AS author, COUNT(*) AS books
FROM author a
JOIN book b ON b.author_id = a.author_id
GROUP BY a.author_id, a.name
HAVING COUNT(*) >= 2
ORDER BY books DESC, a.name;

-- F2.3 (c) Total, smallest and largest price of the whole library
SELECT SUM(price) AS total_price, MIN(price) AS smallest_price, MAX(price) AS largest_price
FROM book;

-- F2.4 (a) Loans not returned yet, with the book title and the member name
SELECT l.loan_id, b.title AS book, m.name AS member, l.loan_date
FROM loan l
JOIN book b   ON l.book_id   = b.book_id
JOIN member m ON l.member_id = m.member_id
WHERE l.return_date IS NULL
ORDER BY l.loan_date;

-- F2.4 (b) Members who never borrowed a book
SELECT m.member_id, m.name, m.email
FROM member m
LEFT JOIN loan l ON l.member_id = m.member_id
WHERE l.loan_id IS NULL;

-- F2.4 (c) Books that were never borrowed
SELECT b.book_id, b.title
FROM book b
LEFT JOIN loan l ON l.book_id = b.book_id
WHERE l.loan_id IS NULL;

-- F2.5 (a) The 3 books with the most loans
SELECT b.title, COUNT(*) AS loans
FROM loan l
JOIN book b ON l.book_id = b.book_id
GROUP BY b.book_id, b.title
ORDER BY loans DESC, b.title
LIMIT 3;

-- F2.5 (b) The member with the most loans
SELECT m.name, COUNT(*) AS loans
FROM loan l
JOIN member m ON l.member_id = m.member_id
GROUP BY m.member_id, m.name
ORDER BY loans DESC, m.name
LIMIT 1;

-- F2.6 (a) Every author with the number of books (0 included)
SELECT a.name AS author, COUNT(b.book_id) AS books
FROM author a
LEFT JOIN book b ON b.author_id = a.author_id
GROUP BY a.author_id, a.name
ORDER BY books DESC, a.name;

-- F2.6 (b) Books whose author and publisher come from the same country
SELECT b.title, a.name AS author, p.name AS publisher, a.country
FROM book b
JOIN author a    ON b.author_id    = a.author_id
JOIN publisher p ON b.publisher_id = p.publisher_id
WHERE a.country = p.country
ORDER BY b.title;
