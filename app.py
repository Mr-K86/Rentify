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
    database="rentify"
)



def get_cursor(buffered=False):
    return db.cursor(buffered=buffered)


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

        cur = get_cursor()
        cur.execute(
            "INSERT INTO register (Full_Name, Email, Password) VALUES (%s, %s, %s)",
            (Full_Name, Email, Password)
        )
        db.commit()
        cur.close()

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

        cur = get_cursor(buffered=True)
        cur.execute("SELECT * FROM register WHERE Email=%s AND Password=%s", (email, password))
        user = cur.fetchone()
        cur.close()

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

        if not contact.isdigit() or len(contact) != 10:
            return "Phone number must be exactly 10 digits!"

        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = None

        email = session['email']

        cur = get_cursor()
        cur.execute(
            "INSERT INTO items (name, price, contact, email, image) VALUES (%s, %s, %s, %s, %s)",
            (name, price, contact, email, filename)
        )
        db.commit()
        cur.close()

        return redirect(url_for('my_items'))

    return render_template('add_item.html')


# =========================
# ALL ITEMS
# =========================
@app.route('/items')
def show_items():
    cur1 = get_cursor(buffered=True)
    cur1.execute("SELECT * FROM items")
    items = cur1.fetchall()
    cur1.close()

    updated_items = []
    for item in items:
        item_id = item[0]

        cur2 = get_cursor(buffered=True)

        cur2.execute(
            "SELECT * FROM rentals WHERE item_id=%s AND status='completed'",
            (item_id,)
        )
        rented = cur2.fetchone()
        cur2.close()

        updated_items.append(item + (rented,))

    return render_template('items.html', items=updated_items)


# =========================
# CREATE ORDER (RAZORPAY)

# =========================
@app.route('/create_order/<int:item_id>')
def create_order(item_id):
    cur = get_cursor(buffered=True)
    cur.execute("SELECT price FROM items WHERE id=%s", (item_id,))
    row = cur.fetchone()
    cur.close()

    if not row:
        return jsonify({"error": "Item not found"}), 404

    price = int(row[0])

    if price is None:
        return jsonify({"error": "Price missing"}), 400

    order = razorpay_client.order.create({
        "amount": int(price) * 100,
        "currency": "INR",
        "payment_capture": 1
    })

    session['paying_item_id'] = item_id

    return jsonify(order)


# =========================
# VERIFY PAYMENT
# =========================
@app.route('/verify_payment', methods=['POST'])
def verify_payment():
    data = request.get_json()

    order_id   = data['razorpay_order_id']
    payment_id = data['razorpay_payment_id']
    signature  = data['razorpay_signature']

  
    generated_signature = hmac.new(
        bytes("LNhtRuwLhWj038uA0EfLplqO", 'utf-8'),
        bytes(order_id + "|" + payment_id, 'utf-8'),
        hashlib.sha256
    ).hexdigest()

    if generated_signature == signature:
        rental_id = session.get('rental_id')

        if not rental_id:
            return jsonify({"status": "failed", "message": "Session expired — rental_id missing"})

        cur = get_cursor()
        cur.execute("""
            UPDATE rentals
            SET payment_method='Online',
                status='completed',
                payment_id=%s
            WHERE id=%s
        """, (payment_id, rental_id))
        db.commit()
        cur.close()

        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "failed", "message": "Signature mismatch"})


# =========================
# MY ITEMS
# =========================
@app.route('/my_items')
def my_items():
    if 'email' not in session:
        return redirect(url_for('login'))

    email = session['email']

    cur = get_cursor(buffered=True)
    cur.execute("SELECT * FROM items WHERE email=%s", (email,))
    data = cur.fetchall()
    cur.close()

    return render_template('my_items.html', items=data)


# =========================
# RENT (AGREEMENT)
# =========================
@app.route('/rent/<int:item_id>', methods=['GET', 'POST'])
def rent(item_id):
    if 'email' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name   = request.form.get('name')
        adhar  = request.form.get('adhar')
        mobile = request.form.get('mobile')
        email  = session['email']

        cur = get_cursor()
        cur.execute(
            "INSERT INTO rentals (item_id, name, adhar, mobile, email) VALUES (%s, %s, %s, %s, %s)",
            (item_id, name, adhar, mobile, email)
        )
        db.commit()

        session['rental_id'] = cur.lastrowid
        # ✅ Store item_id in session so payment page knows which item to charge
        session['paying_item_id'] = item_id
        cur.close()

        return redirect('/payment')

    return render_template('rent.html', item_id=item_id)


# =========================
# PAYMENT PAGE

# =========================
@app.route('/payment')
def payment():
    if 'email' not in session:
        return redirect(url_for('login'))

    item_id = session.get('paying_item_id')
    if not item_id:
        return "Session expired. Please start again."

    return render_template('payment.html', item_id=item_id)


# =========================
# MY RENTALS (USER HISTORY)
# =========================
@app.route('/my_rentals')
def my_rentals():
    if 'email' not in session:
        return redirect(url_for('login'))

    email = session['email']

    cur = get_cursor(buffered=True)
    cur.execute("""
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
    """, (email,))
    data = cur.fetchall()
    cur.close()

    return render_template('my_rentals.html', rentals=data)


# =========================
# RUN APP
# =========================
if __name__ == '__main__':
    app.run(debug=True)