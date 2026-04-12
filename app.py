import os
from werkzeug.utils import secure_filename
from flask import Flask, redirect, render_template, request, session, url_for
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# =========================
# DATABASE CONNECTION
# =========================
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="NewPassword@123",
    database="rentify2"
)

cursor = db.cursor()




# =========================
# HOME PAGE
# =========================
@app.route('/')
def home():
    return render_template('home.html')


# =========================
# REGISTER
# =========================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        Full_Name = request.form['Full_Name']
        Email = request.form['Email']
        Password = request.form['Password']

        query = "INSERT INTO register (Full_Name, Email, Password) VALUES (%s, %s, %s)"
        cursor.execute(query, (Full_Name, Email, Password))
        db.commit()

        return redirect(url_for('login'))

    return render_template("register.html")


# =========================
# LOGIN
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['Email']
        password = request.form['Password']

        query = "SELECT * FROM register WHERE Email=%s AND Password=%s"
        cursor.execute(query, (email, password))
        user = cursor.fetchone()

        if user:
            session['email'] = user[2]   # email
            session['name'] = user[1]    # name
            return redirect(url_for('dashboard'))
        else:
            return "Invalid email or password."

    return render_template('login.html')


# =========================
# DASHBOARD
# =========================
@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('login'))

    return render_template(
        'dashboard.html',
        name=session['name'],
        email=session['email']
    )


# =========================
# LOGOUT
# =========================
@app.route('/logout')
def logout():
    session.clear()   # ✅ full session clear
    return redirect(url_for('login'))


# =========================
# CONTACT
# =========================
@app.route('/contact')
def contact():
    return render_template('contact.html')


# =========================
# ADD ITEM
# =========================
@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if 'email' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        contact = request.form['contact']
        image = request.files['image']

        # ✅ phone validation
        if not contact.isdigit() or len(contact) != 10:
            return "Phone number must be exactly 10 digits!"

        # ✅ image save
        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
        else:
            filename = None

        email = session['email']

        query = "INSERT INTO items (name, price, contact, email, image) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (name, price, contact, email, filename))
        db.commit()

        return redirect(url_for('my_items'))

    return render_template('add_item.html')


# =========================
# ALL ITEMS
# =========================
@app.route('/items')
def show_items():
    cursor.execute("SELECT * FROM items")
    data = cursor.fetchall()

    return render_template('items.html', items=data)


# =========================
# MY ITEMS (USER ONLY)
# =========================
@app.route('/my_items')
def my_items():
    if 'email' not in session:
        return redirect(url_for('login'))

    email = session['email']

    query = "SELECT * FROM items WHERE email=%s"
    cursor.execute(query, (email,))
    data = cursor.fetchall()

    return render_template('my_items.html', items=data)


# =========================
# RUN APP
# =========================
if __name__ == '__main__':
    app.run(debug=True)