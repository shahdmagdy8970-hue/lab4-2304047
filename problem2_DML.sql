-- Lab 4 - Part II - Problem 2: seed data
USE library;

-- Five authors: two Egyptian authors; Jane Austen intentionally has no books.
INSERT INTO author (author_id, name, country, photo) VALUES
(1, 'Naguib Mahfouz', 'Egypt', 'naguib.jpg'),
(2, 'Agatha Christie', 'United Kingdom', 'agatha.jpg'),
(3, 'Paulo Coelho', 'Brazil', 'paulo.jpg'),
(4, 'Ahmed Khaled Tawfik', 'Egypt', NULL),
(5, 'Jane Austen', 'United Kingdom', NULL);

INSERT INTO publisher (publisher_id, name, country) VALUES
(1, 'Dar El Shorouk', 'Egypt'),
(2, 'HarperCollins', 'United Kingdom'),
(3, 'Planeta', 'Brazil');

INSERT INTO category (category_id, name) VALUES
(1, 'Fiction'),
(2, 'Mystery'),
(3, 'Science Fiction');

-- Ten books. Book 10 is intentionally never borrowed.
INSERT INTO book
(book_id, title, price, publish_year, author_id, publisher_id, category_id, cover)
VALUES
(1, 'Palace Walk', 15.50, 1956, 1, 1, 1, 'palace_walk.jpg'),
(2, 'Midaq Alley', 12.00, 1947, 1, 1, 1, 'midaq_alley.jpg'),
(3, 'Murder on the Orient Express', 18.75, 1934, 2, 2, 2, 'orient_express.jpg'),
(4, 'And Then There Were None', 16.00, 1939, 2, 2, 2, 'and_then_there_were_none.jpg'),
(5, 'The Alchemist', 14.25, 1988, 3, 3, 1, 'the_alchemist.jpg'),
(6, 'Eleven Minutes', 13.00, 2003, 3, 3, 1, 'eleven_minutes.jpg'),
(7, 'Utopia', 19.00, 2008, 4, 1, 3, NULL),
(8, 'The Blue Elephant', 17.50, 2012, 4, 1, 3, NULL),
(9, 'The Land of Zikola', 18.00, 2010, 4, 1, 1, NULL),
(10, 'The Unborrowed Story', 20.50, 2020, 1, 1, 1, NULL);

INSERT INTO member (member_id, name, email, join_date) VALUES
(1, 'Mariam Hassan', 'mariam@example.com', '2026-09-01'),
(2, 'Omar Ali', 'omar@example.com', '2026-09-03'),
(3, 'Salma Nabil', 'salma@example.com', '2026-09-05'),
(4, 'Youssef Adel', 'youssef@example.com', '2026-09-08'),
(5, 'Nour Samir', 'nour@example.com', '2026-09-10');

-- 12 loans. Member 5 has no loans; loan 12 is still active (return_date IS NULL).
INSERT INTO loan (loan_id, book_id, member_id, loan_date, return_date) VALUES
(1, 1, 1, '2026-10-01', '2026-10-08'),
(2, 1, 2, '2026-10-09', '2026-10-15'),
(3, 1, 1, '2026-10-16', '2026-10-22'),
(4, 2, 1, '2026-10-02', '2026-10-09'),
(5, 3, 2, '2026-10-03', '2026-10-10'),
(6, 4, 2, '2026-10-11', '2026-10-18'),
(7, 4, 3, '2026-10-19', '2026-10-25'),
(8, 5, 3, '2026-10-04', '2026-10-11'),
(9, 6, 4, '2026-10-05', '2026-10-12'),
(10, 7, 4, '2026-10-13', '2026-10-20'),
(11, 8, 1, '2026-10-23', '2026-10-29'),
(12, 9, 1, '2026-11-10', NULL);
