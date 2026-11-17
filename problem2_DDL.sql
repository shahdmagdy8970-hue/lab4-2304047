DROP DATABASE IF EXISTS library;
CREATE DATABASE library;
USE library;

CREATE TABLE author (
    author_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(50),
    photo VARCHAR(50),
    PRIMARY KEY (author_id)
);

CREATE TABLE publisher (
    publisher_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(50),
    PRIMARY KEY (publisher_id)
);

CREATE TABLE category (
    category_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(80) NOT NULL,
    PRIMARY KEY (category_id)
);

CREATE TABLE book (
    book_id INT NOT NULL AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    publish_year YEAR,
    author_id INT NOT NULL,
    publisher_id INT NOT NULL,
    category_id INT NOT NULL,
    cover VARCHAR(50),
    PRIMARY KEY (book_id),
    CONSTRAINT fk_book_author
        FOREIGN KEY (author_id) REFERENCES author(author_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_book_publisher
        FOREIGN KEY (publisher_id) REFERENCES publisher(publisher_id),
    CONSTRAINT fk_book_category
        FOREIGN KEY (category_id) REFERENCES category(category_id)
);

CREATE TABLE member (
    member_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    join_date DATE NOT NULL,
    PRIMARY KEY (member_id),
    UNIQUE KEY uq_member_email (email)
);

CREATE TABLE loan (
    loan_id INT NOT NULL AUTO_INCREMENT,
    book_id INT NOT NULL,
    member_id INT NOT NULL,
    loan_date DATE NOT NULL,
    return_date DATE NULL,
    PRIMARY KEY (loan_id),
    CONSTRAINT fk_loan_book
        FOREIGN KEY (book_id) REFERENCES book(book_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_loan_member
        FOREIGN KEY (member_id) REFERENCES member(member_id)
);
