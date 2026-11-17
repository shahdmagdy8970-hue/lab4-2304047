# Lab 4 – Search Queries in SQL

Introduction to Database Systems – Alexandria National University, Fall 2026

- Student: Shahd Magdy Abdelghany – ID: 2304047

## Repository content

```
lab4-2304047/
  problem1_DDL.sql       # Problem 1: COMPANY database, five tables (PKs, composite PKs, FKs)
  problem1_DML.sql       # Problem 1: INSERT queries (8 employees, 4 departments, 4 projects, 8 works_on, 4 dependents)
  problem1_Answers.txt   # Problem 1: SQL + output/error for Q1.1 - Q1.12
  problem2_DDL.sql       # Problem 2: LIBRARY database, six tables (ON DELETE CASCADE)
  problem2_DML.sql       # Problem 2: seed data (5 authors, 3 publishers, 3 categories, 10 books, 5 members, 12 loans)
  problem2_Queries.sql   # Problem 2: the SQL of the pages F2.1 - F2.6
  website/               # Flask website (Lab 2 + Lab 3 pages + the new search pages)
  README.md
```

## Requirements

- MySQL Server (the `mysql` client must work from the terminal)
- Python 3.10 or newer

## 1. Problem 1 – COMPANY database

Run from the repository folder (enter the MySQL root password when asked):

```
mysql -u root -p < problem1_DDL.sql
mysql -u root -p < problem1_DML.sql
mysql -u root -p company            # type queries by hand and read the result
```

Both scripts can be re-run at any time (the DDL starts with `DROP DATABASE IF EXISTS company;`).
`problem1_Answers.txt` has the SQL and the output (or error message) of Q1.1 – Q1.12. The questions are answered
in order, so every output shows the data after the previous changes.

## 2. Problem 2 – LIBRARY database

```
mysql -u root -p < problem2_DDL.sql
mysql -u root -p < problem2_DML.sql
mysql -u root -p < website/library_extra_tables.sql
mysql -u root -p library < problem2_Queries.sql
```

Tables: `author`, `publisher`, `category`, `book`, `member`, `loan`.
Deleting an author deletes all of the author's books, and deleting a book deletes its loans (`ON DELETE CASCADE`).
`loan.return_date` is `NULL` while the book is still borrowed.

> Re-running `problem2_DDL.sql` deletes the `library` database, so run `website/library_extra_tables.sql`
> (favorites and featured book) again after it.

`problem2_Queries.sql` contains the SQL of every new page, each one after a comment `-- F2.1`, `-- F2.2`, ... `-- F2.6`.

## 3. Run the website

The website also needs the Lab 2 database (`registration`: users and to-do list). Run these once, **after** step 2:

```
mysql -u root -p < website/lab2_schema.sql
mysql -u root -p < website/library_extra_tables.sql
```

Then, from the repository folder:

```
cd website

# create and activate a virtual environment
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # Linux / macOS

pip install -r requirements.txt

# create the settings file
copy .env.example .env           # Windows
# cp .env.example .env           # Linux / macOS
```

Open `.env` and fill it in:

```
DB_HOST=localhost
DB_USER=root
DB_PASS=<your MySQL password>
DB_NAME_USERS=registration
DB_NAME_LIBRARY=library
SECRET_KEY=<any long random text>
ADMIN_EMAILS=<the email you will register with>
```

Start the server:

```
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in the browser.

## 4. Using the website

1. Click **Register** and create an account. To get administrator rights, register with the same email you wrote in
   `ADMIN_EMAILS` (typed in English letters, exactly the same). Several admins can be separated by commas.
2. After login you land on the **Library** page (Lab 3): list, search, favorites, featured book, and for admins
   add / edit / delete of books and authors. A book now also has a **publisher**, a **category** and a **publish year**.
3. The new Lab 4 pages are in the top menu:

| Menu button | URL | Page | SQL features |
|---|---|---|---|
| Search | `/search` | **F2.1** title keyword, minimum and maximum price, category; cheapest first | `WHERE`, `LIKE`, `BETWEEN`, `ORDER BY` |
| Catalogue | `/catalogue` | **F2.2** all books with author, publisher and category names | `JOIN` |
| Reports | `/reports` | **F2.3** books and average price per category; authors with at least 2 books; total, smallest and largest price | `GROUP BY`, `HAVING`, aggregates |
| Loans | `/loans` | **F2.4** loans not returned yet; members who never borrowed; books never borrowed | `JOIN`, `LEFT JOIN` |
| Most borrowed | `/most-borrowed` | **F2.5** the 3 most borrowed books and the member with the most loans | `GROUP BY`, `ORDER BY`, `LIMIT` |
| Authors | `/authors-books` | **F2.6** every author with the number of books (0 included); books whose author and publisher are from the same country | `LEFT JOIN`, `JOIN` |

4. **Bonus (prepared statements):** the search form of F2.1 uses placeholders (`%s`), so the text typed by the user is
   sent to MySQL as data and is never pasted into the SQL text.
5. Administrators also have an **Admin** button (`/admin`). The **To-Do List** page (Lab 2) is in the top menu.

## Notes

- Only a user whose email is in `ADMIN_EMAILS` can add, edit or delete library data (checked in the Flask backend).
- The seed images used by `problem2_DML.sql` are in `website/static/images/`.
- Do not upload `.env` or `venv/` to GitHub (they are listed in `.gitignore`).

## Troubleshooting

| Problem | Fix |
|---|---|
| `Access denied for user 'root'` | `DB_PASS` in `.env` is wrong |
| `Unknown database 'library'` / `'registration'` | run the SQL scripts of steps 2 and 3 |
| `Table 'library.favorites' doesn't exist` | run `website/library_extra_tables.sql` |
| `403 - You do not have permission` | your login email is not exactly the one in `ADMIN_EMAILS`; fix `.env`, restart the server, log out and log in again |
