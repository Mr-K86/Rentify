# =========================
# IMPORTS
# =========================
import razorpay
import hmac
import hashlib
from flask import jsonify

import os
from werkzeug.utils import secure_filename
from flask import Flask, redirect, render_template, request, session, url_for
import mysql.connector

# =========================
# APP CONFIG
# =========================
app = Flask(__name__)

razorpay_client = razorpay.Client(auth=("rzp_live_SeE0JX90xaFfzU", "LNhtRuwLhWj038uA0EfLplqO")) 
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
            session['email'] = user[2]
            session['name'] = user[1]
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

    return render_template('dashboard.html', name=session['name'], email=session['email'])


# =========================
# LOGOUT
# =========================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# =========================
# CONTACT PAGE
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

        # Phone validation
        if not contact.isdigit() or len(contact) != 10:
            return "Phone number must be exactly 10 digits!"

        # Image upload
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
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

    cursor1 = db.cursor(buffered=True)
    cursor1.execute("SELECT * FROM items")
    items = cursor1.fetchall()

    updated_items = []

    for item in items:
        item_id = item[0]

        cursor2 = db.cursor(buffered=True)
        cursor2.execute(
            "SELECT * FROM rentals WHERE item_id=%s AND status='Paid'",
            (item_id,)
        )
        rented = cursor2.fetchone()

        updated_items.append(item + (rented,))

        cursor2.close()

    cursor1.close()

    return render_template('items.html', items=updated_items)


# =========================
# CREATE ORDER (RAZORPAY)
# =========================
@app.route('/create_order/<int:amount>')
def create_order(amount):

    order = razorpay_client.order.create({
        "amount": amount * 100,
        "currency": "INR",
        "payment_capture": 1
    })

    return jsonify(order)


# =========================
# VERIFY PAYMENT
# =========================
@app.route('/verify_payment', methods=['POST'])
def verify_payment():

    data = request.get_json()

    order_id = data['razorpay_order_id']
    payment_id = data['razorpay_payment_id']
    signature = data['razorpay_signature']

    generated_signature = hmac.new(
        bytes("LNhtRuwLhWj038uA0EfLplqO", 'utf-8'),
        bytes(order_id + "|" + payment_id, 'utf-8'),
        hashlib.sha256
    ).hexdigest()

    if generated_signature == signature:

        rental_id = session.get('rental_id')

        if not rental_id:
            return jsonify({"status": "failed", "message": "Session expired"})

        cursor.execute("""
            UPDATE rentals
            SET payment_method='Online',
                status='completed',
                payment_id=%s
            WHERE id=%s
        """, (payment_id, rental_id))

        db.commit()

        return jsonify({"status": "success"})

    else:
        return jsonify({"status": "failed"})
# =========================
# MY ITEMS
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
# RENT (AGREEMENT)
# =========================
@app.route('/rent/<int:item_id>', methods=['GET', 'POST'])
def rent(item_id):

    if request.method == 'POST':

        name = request.form.get('name')
        adhar = request.form.get('adhar')
        mobile = request.form.get('mobile')

        # ✅ correct email (session se)
        email = session['email']

        print("Form Data:", request.form)
        print("Session Email:", email)

        query = """
        INSERT INTO rentals (item_id, name, adhar, mobile, email)
        VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(query, (item_id, name, adhar, mobile, email))
        db.commit()

        session['rental_id'] = cursor.lastrowid

        return redirect('/payment')

    return render_template('rent.html', item_id=item_id)


# =========================
# PAYMENT PAGE
# =========================
@app.route('/payment')
def payment():
    return render_template('payment.html')




    # DEBUG: print form data
    print("Form Data:", request.form)

    method = request.form.get('method')

    if not method:
        return "❌ Error: Payment method missing!"

    rental_id = session.get('rental_id')

    if not rental_id:
        return "❌ Session expired!"

    query = """
    UPDATE rentals
    SET payment_method=%s,
        status='Paid'
    WHERE id=%s
    """

    cursor.execute(query, (method, rental_id))
    db.commit()

    return f"✅ Payment Successful using {method}"


# =========================
# MY RENTALS (USER HISTORY)
# =========================
@app.route('/my_rentals')
def my_rentals():

    if 'email' not in session:
        return redirect(url_for('login'))

    email = session['email']

    query = """
    SELECT 
        items.name,
        items.price,
        items.image,
        rentals.name,
        rentals.mobile,
        rentals.adhar,
        rentals.payment_method,
        rentals.status
    FROM rentals
    JOIN items ON rentals.item_id = items.id
    WHERE rentals.email = %s
    """

    cursor.execute(query, (email,))
    data = cursor.fetchall()

    return render_template('my_rentals.html', rentals=data)

# =========================
# RUN APP
# =========================
if __name__ == '__main__':
    app.run(debug=True)