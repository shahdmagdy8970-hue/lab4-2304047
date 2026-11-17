import os
import bcrypt
import pymysql
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, session, url_for, flash, abort
from werkzeug.utils import secure_filename
from uuid import uuid4

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "images")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024
app.config["MAX_CONTENT_LENGTH"] = MAX_IMAGE_SIZE


def get_db(database):
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", ""),
        database=database,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def users_db():
    return get_db(os.getenv("DB_NAME_USERS", "registration"))


def library_db():
    return get_db(os.getenv("DB_NAME_LIBRARY", "library"))


def is_admin():
    admin_emails = {
        email.strip().lower()
        for email in os.getenv("ADMIN_EMAILS", "").split(",")
        if email.strip()
    }
    email = (session.get("email") or "").strip().lower()
    return bool(email and email in admin_emails)


def login_required():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return None


def save_image(field_name):
    image = request.files.get(field_name)
    if not image or image.filename == "":
        return None, None

    filename = secure_filename(image.filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        return None, "Image must be PNG, JPG, JPEG, or WEBP"

    unique_name = f"{uuid4().hex}.{extension}"
    image.save(os.path.join(UPLOAD_FOLDER, unique_name))
    return unique_name, None


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("todos"))
    return redirect(url_for("login"))


# ---------- Register ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    errors = []
    name = ""
    email = ""

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not name:
            errors.append("Name is required")
        if not email:
            errors.append("Email is required")
        if not password:
            errors.append("Password is required")
        if not confirm:
            errors.append("Confirm password is required")
        if password and confirm and password != confirm:
            errors.append("Passwords do not match")

        if not errors:
            hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            conn = users_db()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)",
                        (email, name, hashed),
                    )
                    new_id = cur.lastrowid
                conn.commit()
                session.clear()
                session["user_id"] = new_id
                session["name"] = name
                session["email"] = email
                return redirect(url_for("todos"))
            except pymysql.err.IntegrityError as exc:
                conn.rollback()
                if exc.args and exc.args[0] == 1062:
                    errors.append("Email Already Exists")
                else:
                    errors.append("Something went wrong. Please try again.")
            finally:
                conn.close()

    return render_template("register.html", errors=errors, name=name, email=email)


# ---------- Login ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    errors = []
    email = ""

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email:
            errors.append("Email is required")
        if not password:
            errors.append("Password is required")

        if not errors:
            conn = users_db()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT user_id, name, email, password_hash FROM users WHERE email = %s",
                        (email,),
                    )
                    user = cur.fetchone()
            finally:
                conn.close()

            if user and bcrypt.checkpw(
                password.encode("utf-8"), user["password_hash"].encode("utf-8")
            ):
                session.clear()
                session["user_id"] = user["user_id"]
                session["name"] = user["name"]
                session["email"] = user["email"]
                return redirect(url_for("books"))
            errors.append("Invalid email or password")

    return render_template("login.html", errors=errors, email=email)


# ---------- Logout ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- To-do list ----------
def valid_title(title):
    if title == "":
        return "Title is required"
    if len(title) > 200:
        return "Title is too long (200 characters at most)"
    return None


@app.route("/todos", methods=["GET", "POST"])
def todos():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    errors = []

    if request.method == "POST":
        action = request.form.get("action", "")
        todo_id = request.form.get("todo_id", type=int, default=0)
        title = request.form.get("title", "").strip()

        conn = users_db()
        try:
            with conn.cursor() as cur:
                if action == "add":
                    err = valid_title(title)
                    if err:
                        errors.append(err)
                    else:
                        cur.execute(
                            "INSERT INTO todos (user_id, title) VALUES (%s, %s)",
                            (user_id, title),
                        )
                elif action == "edit":
                    err = valid_title(title)
                    if err:
                        errors.append(err)
                    else:
                        cur.execute(
                            "UPDATE todos SET title = %s WHERE todo_id = %s AND user_id = %s",
                            (title, todo_id, user_id),
                        )
                elif action == "toggle":
                    is_done = 1 if request.form.get("is_done") == "1" else 0
                    cur.execute(
                        "UPDATE todos SET is_done = %s WHERE todo_id = %s AND user_id = %s",
                        (is_done, todo_id, user_id),
                    )
                elif action == "delete":
                    cur.execute(
                        "DELETE FROM todos WHERE todo_id = %s AND user_id = %s",
                        (todo_id, user_id),
                    )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        if not errors:
            return redirect(url_for("todos"))

    conn = users_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT todo_id, title, is_done, created_at "
                "FROM todos WHERE user_id = %s ORDER BY todo_id DESC",
                (user_id,),
            )
            items = cur.fetchall()
    finally:
        conn.close()

    return render_template("todos.html", errors=errors, items=items, name=session.get("name", ""))


# ---------- Library helpers ----------
def author_errors(name, country):
    errors = []
    if not name:
        errors.append("Name is required")
    elif len(name) > 100:
        errors.append("Name is too long (100 characters at most)")
    if len(country) > 50:
        errors.append("Country is too long (50 characters at most)")
    return errors


def book_errors(title, price, author_id, publisher_id=1, category_id=1, publish_year=""):
    errors = []
    if not title:
        errors.append("Title is required")
    elif len(title) > 200:
        errors.append("Title is too long (200 characters at most)")
    try:
        value = float(price)
        if value < 0:
            errors.append("Price must not be negative")
    except (ValueError, TypeError):
        errors.append("Price must be a number")
    if not author_id or author_id < 1:
        errors.append("Author is required")
    if not publisher_id or publisher_id < 1:
        errors.append("Publisher is required")
    if not category_id or category_id < 1:
        errors.append("Category is required")
    if publish_year:
        if not publish_year.isdigit() or not 1901 <= int(publish_year) <= 2155:
            errors.append("Publish year must be between 1901 and 2155")
    return errors


# ---------- Books, dashboard stats, search and filters ----------
@app.route("/books", methods=["GET", "POST"])
def books():
    if "user_id" not in session:
        return redirect(url_for("login"))

    errors = []
    form = {}

    if request.method == "POST":
        form = request.form
        kind = form.get("kind", "")
        # Only admins can create/edit/delete library records or change the featured book.
        # Any signed-in user may manage their own favorites.
        if kind != "toggle_favorite" and not is_admin():
            abort(403)

        conn = library_db()
        try:
            with conn.cursor() as cur:
                if kind == "author":
                    name = form.get("name", "").strip()
                    country = form.get("country", "").strip()
                    errors = author_errors(name, country)
                    photo = None
                    if not errors:
                        photo, image_error = save_image("photo")
                        if image_error:
                            errors.append(image_error)
                    if not errors:
                        cur.execute(
                            "INSERT INTO author (name, country, photo) VALUES (%s, %s, %s)",
                            (name, country or None, photo),
                        )

                elif kind == "edit_author":
                    aid = form.get("author_id", type=int, default=0)
                    name = form.get("name", "").strip()
                    country = form.get("country", "").strip()
                    errors = author_errors(name, country)
                    if not errors and aid:
                        cur.execute(
                            "UPDATE author SET name = %s, country = %s WHERE author_id = %s",
                            (name, country or None, aid),
                        )

                elif kind == "edit_book":
                    bid = form.get("book_id", type=int, default=0)
                    title = form.get("title", "").strip()
                    price = form.get("price", "").strip()
                    author_id = form.get("author_id", type=int, default=0)
                    publisher_id = form.get("publisher_id", type=int, default=0)
                    category_id = form.get("category_id", type=int, default=0)
                    publish_year = form.get("publish_year", "").strip()
                    errors = book_errors(title, price, author_id, publisher_id, category_id, publish_year)
                    if not errors:
                        try:
                            cur.execute(
                                "UPDATE book SET title = %s, price = %s, publish_year = %s, "
                                "author_id = %s, publisher_id = %s, category_id = %s "
                                "WHERE book_id = %s",
                                (title, float(price), publish_year or None,
                                 author_id, publisher_id, category_id, bid),
                            )
                        except pymysql.err.IntegrityError:
                            errors.append("This author, publisher or category does not exist")

                elif kind == "delete_book":
                    bid = form.get("book_id", type=int, default=0)
                    if bid:
                        cur.execute("DELETE FROM favorites WHERE book_id = %s", (bid,))
                        cur.execute(
                            "UPDATE library_settings SET setting_value = NULL "
                            "WHERE setting_key = 'featured_book_id' AND setting_value = %s",
                            (str(bid),),
                        )
                        cur.execute("DELETE FROM book WHERE book_id = %s", (bid,))

                elif kind == "delete_author":
                    aid = form.get("author_id", type=int, default=0)
                    if aid:
                        cur.execute(
                            "SELECT book_id FROM book WHERE author_id = %s", (aid,)
                        )
                        linked_books = cur.fetchall()
                        for item in linked_books:
                            cur.execute(
                                "DELETE FROM favorites WHERE book_id = %s",
                                (item["book_id"],),
                            )
                            cur.execute(
                                "UPDATE library_settings SET setting_value = NULL "
                                "WHERE setting_key = 'featured_book_id' AND setting_value = %s",
                                (str(item["book_id"]),),
                            )
                        cur.execute("DELETE FROM book WHERE author_id = %s", (aid,))
                        cur.execute("DELETE FROM author WHERE author_id = %s", (aid,))

                elif kind == "book":
                    title = form.get("title", "").strip()
                    price = form.get("price", "").strip()
                    author_id = form.get("author_id", type=int, default=0)
                    publisher_id = form.get("publisher_id", type=int, default=0)
                    category_id = form.get("category_id", type=int, default=0)
                    publish_year = form.get("publish_year", "").strip()
                    errors = book_errors(title, price, author_id, publisher_id, category_id, publish_year)
                    cover = None
                    if not errors:
                        cover, image_error = save_image("cover")
                        if image_error:
                            errors.append(image_error)
                    if not errors:
                        try:
                            cur.execute(
                                "INSERT INTO book (title, price, publish_year, author_id, "
                                "publisher_id, category_id, cover) "
                                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                (title, float(price), publish_year or None, author_id,
                                 publisher_id, category_id, cover),
                            )
                        except pymysql.err.IntegrityError:
                            errors.append("This author, publisher or category does not exist")

                elif kind == "set_featured":
                    bid = form.get("book_id", type=int, default=0)
                    cur.execute("SELECT book_id FROM book WHERE book_id = %s", (bid,))
                    if not cur.fetchone():
                        errors.append("Book not found")
                    else:
                        cur.execute(
                            "INSERT INTO library_settings (setting_key, setting_value) "
                            "VALUES ('featured_book_id', %s) "
                            "ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)",
                            (str(bid),),
                        )

                elif kind == "toggle_favorite":
                    bid = form.get("book_id", type=int, default=0)
                    cur.execute("SELECT book_id FROM book WHERE book_id = %s", (bid,))
                    if not cur.fetchone():
                        errors.append("Book not found")
                    else:
                        cur.execute(
                            "SELECT favorite_id FROM favorites WHERE user_id = %s AND book_id = %s",
                            (session["user_id"], bid),
                        )
                        existing = cur.fetchone()
                        if existing:
                            cur.execute("DELETE FROM favorites WHERE favorite_id = %s", (existing["favorite_id"],))
                        else:
                            cur.execute(
                                "INSERT INTO favorites (user_id, book_id) VALUES (%s, %s)",
                                (session["user_id"], bid),
                            )
                else:
                    errors.append("Unknown action")

            if errors:
                conn.rollback()
            else:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        if not errors:
            return redirect(request.referrer if request.referrer and request.referrer.startswith(request.host_url) else url_for("books"))

    search = request.args.get("search", "").strip()
    selected_author = request.args.get("author_id", "").strip()
    min_price = request.args.get("min_price", "").strip()
    max_price = request.args.get("max_price", "").strip()
    favorites_only = request.args.get("favorites") == "1"

    conditions = []
    params = []
    if search:
        conditions.append("b.title LIKE %s")
        params.append(f"%{search}%")

    if selected_author:
        try:
            conditions.append("b.author_id = %s")
            params.append(int(selected_author))
        except ValueError:
            selected_author = ""

    if min_price:
        try:
            value = float(min_price)
            if value >= 0:
                conditions.append("b.price >= %s")
                params.append(value)
            else:
                min_price = ""
        except ValueError:
            min_price = ""

    if max_price:
        try:
            value = float(max_price)
            if value >= 0:
                conditions.append("b.price <= %s")
                params.append(value)
            else:
                max_price = ""
        except ValueError:
            max_price = ""

    if favorites_only:
        conditions.append(
            "EXISTS (SELECT 1 FROM favorites f WHERE f.book_id = b.book_id AND f.user_id = %s)"
        )
        params.append(session["user_id"])

    where_sql = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    conn = library_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS total_books, COALESCE(AVG(price), 0) AS average_price, "
                "COALESCE(MAX(price), 0) AS highest_price FROM book"
            )
            stats = cur.fetchone()
            cur.execute("SELECT COUNT(*) AS total_authors FROM author")
            stats["total_authors"] = cur.fetchone()["total_authors"]

            cur.execute(
                "SELECT b.book_id, b.title, b.price, b.cover, a.name AS author_name "
                "FROM book b LEFT JOIN author a ON a.author_id = b.author_id "
                "ORDER BY b.price DESC, b.book_id LIMIT 1"
            )
            stats["most_expensive_book"] = cur.fetchone()

            cur.execute(
                "SELECT author_id, name, country, photo FROM author ORDER BY name"
            )
            author_rows = cur.fetchall()

            cur.execute("SELECT publisher_id, name FROM publisher ORDER BY name")
            publisher_rows = cur.fetchall()
            cur.execute("SELECT category_id, name FROM category ORDER BY name")
            category_rows = cur.fetchall()

            cur.execute(
                "SELECT b.book_id, b.title, b.price, b.author_id, b.cover, "
                "b.publisher_id, b.category_id, b.publish_year, "
                "a.name AS author_name, "
                "EXISTS (SELECT 1 FROM favorites f WHERE f.book_id = b.book_id "
                "AND f.user_id = %s) AS is_favorite, "
                "EXISTS (SELECT 1 FROM library_settings s WHERE s.setting_key = 'featured_book_id' "
                "AND s.setting_value = CAST(b.book_id AS CHAR)) AS is_featured "
                "FROM book b LEFT JOIN author a ON a.author_id = b.author_id"
                + where_sql
                + " ORDER BY b.book_id",
                [session["user_id"]] + params,
            )
            book_rows = cur.fetchall()

            cur.execute(
                "SELECT b.book_id, b.title, b.price, b.cover, a.name AS author_name "
                "FROM library_settings s JOIN book b "
                "ON s.setting_value = CAST(b.book_id AS CHAR) "
                "LEFT JOIN author a ON a.author_id = b.author_id "
                "WHERE s.setting_key = 'featured_book_id' LIMIT 1"
            )
            featured_book = cur.fetchone()
    finally:
        conn.close()

    return render_template(
        "books.html",
        books=book_rows,
        authors=author_rows,
        publishers=publisher_rows,
        categories=category_rows,
        errors=errors,
        form=form,
        stats=stats,
        search=search,
        selected_author=selected_author,
        min_price=min_price,
        max_price=max_price,
        favorites_only=favorites_only,
        featured_book=featured_book,
        is_admin=is_admin(),
    )


# ---------- Book detail ----------
@app.route("/book/<int:book_id>")
def book_detail(book_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = library_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT b.book_id, b.title, b.price, b.author_id, b.cover, "
                "a.name AS author_name, a.country AS author_country, a.photo AS author_photo, "
                "EXISTS (SELECT 1 FROM favorites f WHERE f.book_id = b.book_id "
                "AND f.user_id = %s) AS is_favorite, "
                "EXISTS (SELECT 1 FROM library_settings s WHERE s.setting_key = 'featured_book_id' "
                "AND s.setting_value = CAST(b.book_id AS CHAR)) AS is_featured "
                "FROM book b LEFT JOIN author a ON a.author_id = b.author_id "
                "WHERE b.book_id = %s",
                (session["user_id"], book_id),
            )
            book = cur.fetchone()
    finally:
        conn.close()

    if not book:
        abort(404)
    return render_template("book_detail.html", book=book, is_admin=is_admin())



# ---------- Admin dashboard ----------
@app.route("/admin")
def admin_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if not is_admin():
        abort(403)

    conn = library_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) AS total_books,
                    COALESCE(AVG(price), 0) AS average_price,
                    COALESCE(MAX(price), 0) AS highest_price
                FROM book
            """)
            stats = cur.fetchone()

            cur.execute("SELECT COUNT(*) AS total_authors FROM author")
            stats["total_authors"] = cur.fetchone()["total_authors"]

            cur.execute("""
                SELECT b.book_id, b.title, b.price, a.name AS author_name
                FROM book b
                LEFT JOIN author a ON a.author_id = b.author_id
                ORDER BY b.price DESC, b.book_id
                LIMIT 1
            """)
            stats["most_expensive_book"] = cur.fetchone()

            cur.execute("""
                SELECT b.book_id, b.title, b.price, a.name AS author_name
                FROM book b
                LEFT JOIN author a ON a.author_id = b.author_id
                ORDER BY b.book_id DESC
                LIMIT 10
            """)
            recent_books = cur.fetchall()

    finally:
        conn.close()

    return render_template(
        "admin.html",
        stats=stats,
        recent_books=recent_books,
        is_admin=True
    )


# =====================================================================
# Lab 4 - Part II: search pages (F2.1 - F2.6)
# Every page is one simple SELECT per table; the same SQL is in problem2_Queries.sql.
# =====================================================================
def run_select(sql, params=()):
    """Run a SELECT with placeholders (%s) and return (column names, rows)."""
    conn = library_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            columns = [col[0] for col in cur.description]
            return columns, cur.fetchall()
    finally:
        conn.close()


def report(title, sql, note="", params=()):
    columns, rows = run_select(sql, params)
    return {"title": title, "note": note, "columns": columns, "rows": rows}


def report_page(page_title, subtitle, sections):
    return render_template(
        "report.html",
        page_title=page_title,
        subtitle=subtitle,
        sections=sections,
        is_admin=is_admin(),
    )


# ---------- F2.1 Search books (WHERE, LIKE, BETWEEN) ----------
@app.route("/search")
def search_books():
    if "user_id" not in session:
        return redirect(url_for("login"))

    keyword = request.args.get("keyword", "").strip()
    min_price = request.args.get("min_price", "").strip()
    max_price = request.args.get("max_price", "").strip()
    category_id = request.args.get("category_id", "").strip()
    errors = []

    low, high = 0.0, 99999999.99
    try:
        if min_price:
            low = float(min_price)
        if max_price:
            high = float(max_price)
    except ValueError:
        errors.append("Prices must be numbers")
    if low < 0 or high < 0:
        errors.append("Prices must not be negative")
    if low > high:
        errors.append("The minimum price must not be larger than the maximum price")

    sql = (
        "SELECT b.book_id, b.title, a.name AS author, c.name AS category, b.price "
        "FROM book b "
        "JOIN author a ON b.author_id = a.author_id "
        "JOIN category c ON b.category_id = c.category_id "
        "WHERE b.title LIKE %s AND b.price BETWEEN %s AND %s"
    )
    params = [f"%{keyword}%", low, high]
    if category_id.isdigit():
        sql += " AND b.category_id = %s"
        params.append(int(category_id))
    else:
        category_id = ""
    sql += " ORDER BY b.price ASC"

    rows = []
    if not errors:
        # placeholders: the text typed by the user is sent as data, never pasted into the SQL
        _, rows = run_select(sql, params)
    _, categories = run_select("SELECT category_id, name FROM category ORDER BY name")

    return render_template(
        "search.html",
        rows=rows,
        errors=errors,
        categories=categories,
        keyword=keyword,
        min_price=min_price,
        max_price=max_price,
        category_id=category_id,
        is_admin=is_admin(),
    )


# ---------- F2.2 Catalogue (JOIN) ----------
@app.route("/catalogue")
def catalogue():
    if "user_id" not in session:
        return redirect(url_for("login"))
    sections = [report(
        "All books",
        "SELECT b.book_id AS id, b.title, a.name AS author, p.name AS publisher, "
        "c.name AS category, b.publish_year AS year, b.price "
        "FROM book b "
        "JOIN author a ON b.author_id = a.author_id "
        "JOIN publisher p ON b.publisher_id = p.publisher_id "
        "JOIN category c ON b.category_id = c.category_id "
        "ORDER BY b.book_id",
    )]
    return report_page("Catalogue", "Every book with the names of its author, publisher and category.", sections)


# ---------- F2.3 Reports (GROUP BY, HAVING) ----------
@app.route("/reports")
def reports():
    if "user_id" not in session:
        return redirect(url_for("login"))
    sections = [
        report(
            "Books and average price of each category",
            "SELECT c.name AS category, COUNT(b.book_id) AS books, ROUND(AVG(b.price), 2) AS average_price "
            "FROM category c LEFT JOIN book b ON b.category_id = c.category_id "
            "GROUP BY c.category_id, c.name ORDER BY c.name",
        ),
        report(
            "Authors who wrote at least 2 books",
            "SELECT a.name AS author, COUNT(*) AS books "
            "FROM author a JOIN book b ON b.author_id = a.author_id "
            "GROUP BY a.author_id, a.name HAVING COUNT(*) >= 2 "
            "ORDER BY books DESC, a.name",
        ),
        report(
            "The whole library: total, smallest and largest price",
            "SELECT SUM(price) AS total_price, MIN(price) AS smallest_price, "
            "MAX(price) AS largest_price FROM book",
        ),
    ]
    return report_page("Reports", "Numbers about the books of the library.", sections)


# ---------- F2.4 Loans (JOIN, LEFT JOIN) ----------
@app.route("/loans")
def loans():
    if "user_id" not in session:
        return redirect(url_for("login"))
    sections = [
        report(
            "Loans not returned yet",
            "SELECT l.loan_id, b.title AS book, m.name AS member, l.loan_date "
            "FROM loan l "
            "JOIN book b ON l.book_id = b.book_id "
            "JOIN member m ON l.member_id = m.member_id "
            "WHERE l.return_date IS NULL ORDER BY l.loan_date",
        ),
        report(
            "Members who never borrowed a book",
            "SELECT m.member_id, m.name, m.email "
            "FROM member m LEFT JOIN loan l ON l.member_id = m.member_id "
            "WHERE l.loan_id IS NULL",
        ),
        report(
            "Books that were never borrowed",
            "SELECT b.book_id, b.title "
            "FROM book b LEFT JOIN loan l ON l.book_id = b.book_id "
            "WHERE l.loan_id IS NULL",
        ),
    ]
    return report_page("Loans", "Who has a book, who has never borrowed, and which books stay on the shelf.", sections)


# ---------- F2.5 Most borrowed (GROUP BY, ORDER BY, LIMIT) ----------
@app.route("/most-borrowed")
def most_borrowed():
    if "user_id" not in session:
        return redirect(url_for("login"))
    sections = [
        report(
            "The 3 most borrowed books",
            "SELECT b.title, COUNT(*) AS loans "
            "FROM loan l JOIN book b ON l.book_id = b.book_id "
            "GROUP BY b.book_id, b.title ORDER BY loans DESC, b.title LIMIT 3",
        ),
        report(
            "The member with the most loans",
            "SELECT m.name, COUNT(*) AS loans "
            "FROM loan l JOIN member m ON l.member_id = m.member_id "
            "GROUP BY m.member_id, m.name ORDER BY loans DESC, m.name LIMIT 1",
        ),
    ]
    return report_page("Most borrowed", "The books and the member with the most loans.", sections)


# ---------- F2.6 Authors and books (LEFT JOIN, JOIN) ----------
@app.route("/authors-books")
def authors_books():
    if "user_id" not in session:
        return redirect(url_for("login"))
    sections = [
        report(
            "Every author with the number of books",
            "SELECT a.name AS author, COUNT(b.book_id) AS books "
            "FROM author a LEFT JOIN book b ON b.author_id = a.author_id "
            "GROUP BY a.author_id, a.name ORDER BY books DESC, a.name",
            note="Authors with 0 books are included.",
        ),
        report(
            "Books whose author and publisher come from the same country",
            "SELECT b.title, a.name AS author, p.name AS publisher, a.country "
            "FROM book b "
            "JOIN author a ON b.author_id = a.author_id "
            "JOIN publisher p ON b.publisher_id = p.publisher_id "
            "WHERE a.country = p.country ORDER BY b.title",
        ),
    ]
    return report_page("Authors and books", "Authors with their number of books, and local publishing.", sections)


@app.errorhandler(403)
def forbidden(_error):
    return "403 - You do not have permission to access this page.", 403


if __name__ == "__main__":
    app.run(debug=True)
