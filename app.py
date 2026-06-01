from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.utils import secure_filename
import os
from datetime import date
app = Flask(__name__)
app.secret_key = "bnm_secret_key"

# =========================
# MYSQL CONNECTION
# =========================

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Cherry1104!",
    database="bnmvault_db"
)

cursor = db.cursor(dictionary=True)

# =========================
# UPLOAD FOLDER
# =========================

UPLOAD_FOLDER = "static/uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# =========================
# HOME PAGE
# =========================

@app.route('/')
def home():

    # AUTO ARCHIVE ITEMS OLDER THAN 6 MONTHS

    cursor.execute("""
        UPDATE lost_items
        SET status='Archived'
        WHERE created_at < NOW() - INTERVAL 6 MONTH
        AND status != 'Claimed'
    """)

    cursor.execute("""
        UPDATE found_items
        SET status='Archived'
        WHERE created_at < NOW() - INTERVAL 6 MONTH
        AND status != 'Claimed'
    """)

    db.commit()

    # STATS

    cursor.execute("SELECT COUNT(*) AS total FROM users")
    total_users = cursor.fetchone()['total']

    cursor.execute("""
    SELECT COUNT(*) AS total
    FROM lost_items
    """)
    total_lost = cursor.fetchone()['total']

    cursor.execute("""
    SELECT COUNT(*) AS total
    FROM found_items
    WHERE status != 'Archived'
    """)
    total_found = cursor.fetchone()['total']

    cursor.execute("""
    SELECT COUNT(*) AS total
    FROM claims
    WHERE status='approved'
    """)
    total_claimed = cursor.fetchone()['total']

    return render_template(
        'index.html',
        total_users=total_users,
        total_lost=total_lost,
        total_found=total_found,
        total_claimed=total_claimed
    )

   

# =========================
# REGISTER
# =========================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        role = request.form.get('role')
        name = request.form.get('name')
        college_id = request.form.get('college_id')
        department = request.form.get('department')
        employee_id = request.form.get('employee_id')
        phone = request.form.get('phone')
        email = request.form.get('email')
        password = request.form.get('password')
        college_id = request.form.get("college_id")

        if college_id == "":
            college_id = None
        employee_id = request.form.get("employee_id")

        if employee_id == "":
            employee_id = None
        query = """
        INSERT INTO users
        (
            name,
            college_id,
            email,
            password,
            role,
            department,
            employee_id,
            phone
        )
        VALUES
        (
           %s,%s,%s,%s,%s,%s,%s,%s
        )
"""

        cursor.execute(
            query,
            (
                name,
                college_id,
                email,
                password,
                role,
                department,
                employee_id,
                phone
            )
        )

        db.commit()

        flash("Registration Successful")

        return redirect(url_for('login'))

    return render_template('register.html')
# =========================
# LOGIN
# =========================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password')

        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cursor.fetchone()

        if user:

            # Plain password check
            if user['password'] == password:

                session['user_id'] = user['user_id']
                session['name'] = user['name']

                flash("Login Successful")

                return redirect(url_for('home'))

        flash("Invalid Email or Password")

    return render_template('login.html')
@app.route('/forgot_password')
def forgot_password():
    return "<h1>Forgot Password feature coming soon.</h1>"
# =========================
# LOGOUT
# =========================

@app.route('/logout')
def logout():

    session.clear()

    flash("Logged Out")

    return redirect(url_for('login'))

# =========================
# ADD LOST ITEM
# =========================

@app.route('/add_lost_item', methods=['GET', 'POST'])
def add_lost_item():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':

        title = request.form.get('title')
        category = request.form.get('category')
        description = request.form.get('description')
        location = request.form.get('location')

        image = request.files.get('image')

        image_filename = ""

        if image and image.filename:

            image_filename = secure_filename(image.filename)

            image.save(
                os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    image_filename
                )
            )

        query = """
        INSERT INTO lost_items
        (
            user_id,
            title,
            category,
            description,
            location,
            date_lost,
            status,
            image
        )
        VALUES
        (
            %s,%s,%s,%s,%s,%s,%s,%s
        )
        """

        values = (
            session['user_id'],
            title,
            category,
            description,
            location,
            date.today(),
            "Lost",
            image_filename
        )

        cursor.execute(query, values)

        db.commit()

        flash("Lost item added successfully")

        return redirect(url_for('home'))

    return render_template('add_lost_item.html')

# =========================
# ADD FOUND ITEM
# =========================

@app.route('/add_found_item', methods=['GET', 'POST'])
def add_found_item():

    if 'user_id' not in session:
        flash("Please login first")
        return redirect(url_for('login'))

    if request.method == 'POST':

        title = request.form.get('title')
        category = request.form.get('category')
        description = request.form.get('description')
        location = request.form.get('location')
        date_found = request.form.get('date_found')

        image = request.files.get('image')

        image_filename = None

        if image and image.filename != "":
            image_filename = secure_filename(image.filename)

            image.save(
                os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    image_filename
                )
            )

        print("TITLE =", title)
        print("CATEGORY =", category)
        print("DESCRIPTION =", description)
        print("LOCATION =", location)
        print("DATE FOUND =", date_found)

        if not title:
            flash("Title is required")
            return redirect(url_for('add_found_item'))

        if not date_found:
            flash("Date Found is required")
            return redirect(url_for('add_found_item'))

        query = """
        INSERT INTO found_items
        (
            user_id,
            title,
            category,
            description,
            location_found,
            date_found,
            status,
            image
        )
        VALUES
        (
            %s,%s,%s,%s,%s,%s,%s,%s
        )
        """

        values = (
            session['user_id'],
            title,
            category,
            description,
            location,
            date_found,
            "Found",
            image_filename
        )

        cursor.execute(query, values)
        db.commit()

        flash("Found Item Added Successfully")

        return redirect(url_for('home'))

    return render_template('add_found_item.html')
# =========================
# VIEW LOST ITEMS
# =========================

@app.route('/lost_items')
def lost_items():

    cursor.execute("SELECT * FROM lost_items ORDER BY item_id DESC")

    items = cursor.fetchall()

    return render_template(
        'lost_items.html',
        items=items
    )
@app.route('/item/lost/<int:item_id>')
def lost_item_detail(item_id):

    query = """
    SELECT
        l.*,
        u.name,
        u.email,
        u.phone
    FROM lost_items l
    JOIN users u
        ON l.user_id = u.user_id
    WHERE l.item_id=%s
    """

    cursor.execute(query,(item_id,))

    item = cursor.fetchone()

    return render_template(
        "lost_item_detail.html",
        item=item
    )
# =========================
# VIEW FOUND ITEMS
# =========================

@app.route('/found_items')
def found_items():

    cursor.execute("SELECT * FROM found_items ORDER BY item_id DESC")

    items = cursor.fetchall()

    return render_template(
        'found_items.html',
        items=items
    )
@app.route('/archive_items')
def archive_items():

    cursor.execute("""
        SELECT *
        FROM lost_items
        WHERE status='Archived'
        ORDER BY item_id DESC
    """)
    lost_archive = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM found_items
        WHERE status='Archived'
        ORDER BY item_id DESC
    """)
    found_archive = cursor.fetchall()

    return render_template(
        'archive_items.html',
        lost_items=lost_archive,
        found_items=found_archive
    )


# =========================
# FOUND ITEM DETAIL
# =========================

@app.route('/item/found/<int:item_id>')
def found_item_detail(item_id):

    query = """
    SELECT
        f.*,
        u.name,
        u.email,
        u.phone
    FROM found_items f
    JOIN users u
        ON f.user_id = u.user_id
    WHERE f.item_id=%s
    """

    cursor.execute(query, (item_id,))
    item = cursor.fetchone()

    return render_template(
        "found_item_detail.html",
        item=item
    )
    # =========================
# CHAT PAGE
# =========================

@app.route('/chat/<int:user_id>')
def chat(user_id):

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE user_id=%s
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    if not user:
        return "User not found"

    return render_template(
        'chat.html',
        user=user
    )
    
    # =========================
# CLAIM ITEM
# =========================

@app.route('/claim/<int:item_id>', methods=['GET', 'POST'])
def claim_item(item_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':

        proof_message = request.form.get('proof_message')

        cursor.execute("""
            INSERT INTO claims
            (
                claimant_id,
                found_item_id,
                proof_message,
                status
            )
            VALUES
            (
                %s,%s,%s,'pending'
            )
        """,
        (
            session['user_id'],
            item_id,
            proof_message
        ))

        db.commit()

        flash("Claim submitted successfully!")
        return redirect(url_for('found_items'))

    cursor.execute(
        "SELECT * FROM found_items WHERE item_id=%s",
        (item_id,)
    )

    item = cursor.fetchone()

    return render_template(
        'claim_item.html',
        item=item
    )
    # =========================
# MY REPORTS
# =========================

@app.route('/my_reports')
def my_reports():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    cursor.execute("""
        SELECT *
        FROM lost_items
        WHERE user_id=%s
        ORDER BY item_id DESC
    """, (session['user_id'],))

    lost_reports = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM found_items
        WHERE user_id=%s
        ORDER BY item_id DESC
    """, (session['user_id'],))

    found_reports = cursor.fetchall()

    return render_template(
        'my_reports.html',
        lost_reports=lost_reports,
        found_reports=found_reports
    )
    # =========================
# MY CLAIMS
# =========================

@app.route('/my_claims')
def my_claims():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    cursor.execute("""
        SELECT c.*, f.title
        FROM claims c
        JOIN found_items f
        ON c.found_item_id = f.item_id
        WHERE c.claimant_id=%s
        ORDER BY c.claim_id DESC
    """, (session['user_id'],))

    claims = cursor.fetchall()

    return render_template(
        'my_claims.html',
        claims=claims
    )
# =========================
# SEARCH
# =========================

@app.route('/search')
def search():

    keyword = request.args.get('keyword')

    query = """
    SELECT * FROM lost_items
    WHERE title LIKE %s
    """

    values = ('%' + keyword + '%',)

    cursor.execute(query, values)

    results = cursor.fetchall()

    return render_template(
        'search_results.html',
        results=results,
        keyword=keyword
    )

# =========================
# RUN APP
# =========================

if __name__ == '__main__':

    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000
    )
    