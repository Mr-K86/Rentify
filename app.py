from flask import Flask, redirect, render_template, request, session, url_for
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="NewPassword@123",
    database="rentify2"
)

cursor = db.cursor()

# Home page
@app.route('/')
def home():
    return render_template('home.html')


# Register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        Full_Name = request.form['Full_Name']
        Email = request.form['Email']
        Password = request.form['Password']

        query = "INSERT INTO register (Full_Name, Email, Password) VALUES (%s, %s, %s)"
        values = (Full_Name, Email, Password)
        cursor.execute(query, values)
        db.commit()

        return redirect(url_for('login'))

    return render_template("register.html")


# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['Email']
        password = request.form['Password']

        query = "SELECT * FROM register WHERE Email = %s AND Password = %s"
        values = (email, password)
        cursor.execute(query, values)
        user = cursor.fetchone()

        if user:
            session['email'] = user[2]   # email
            session['name'] = user[1]    # ✅ name store
            return redirect(url_for('dashboard'))
        else:
            return "Invalid email or password."

    return render_template('login.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'email' in session:
        return render_template(
            'dashboard.html',
            name=session['name'],
            email=session['email']
        )
    else:
        return redirect(url_for('login'))


# Logout (FIXED INDENTATION)
@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('login'))


# Contact page
@app.route('/contact')
def contact():
    return render_template('contact.html')


# Add item
@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if 'email' not in session:   # ✅ safety
        return redirect('/login')

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        contact = request.form['contact']
        email = session['email']   # ✅ now correct

        query = "INSERT INTO items (name, price, contact, email) VALUES (%s, %s, %s, %s)"
        values = (name, price, contact, email)
        cursor.execute(query, values)
        db.commit()

        return redirect('/items')

    return render_template('add_item.html')


# Show items (ONLY ONE ROUTE)
@app.route('/items')
def show_items():
    cursor.execute("SELECT * FROM items")
    data = cursor.fetchall()

    return render_template('items.html', items=data)


if __name__ == '__main__':
    app.run(debug=True)