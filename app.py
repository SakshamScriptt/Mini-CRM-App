from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # Required for session and flash messages

# --- Helper Functions ---
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row # Returns rows as dictionaries
    return conn

# Decorator to protect routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM admin WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        
        if admin:
            session['logged_in'] = True
            session['username'] = admin['username']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    conn = get_db_connection()
    total_customers = conn.execute('SELECT COUNT(*) FROM customers').fetchone()[0]
    active_customers = conn.execute('SELECT COUNT(*) FROM customers WHERE status = "Active"').fetchone()[0]
    pending_customers = conn.execute('SELECT COUNT(*) FROM customers WHERE status = "Pending"').fetchone()[0]
    
    # --- DATA ANALYTICS LOGIC: Extract Email Domains ---
    emails = conn.execute('SELECT email FROM customers').fetchall()
    domains = {}
    for e in emails:
        # Email id se domain alag karna (e.g., @gmail.com)
        domain = e['email'].split('@')[-1] if '@' in e['email'] else 'Other'
        domains[domain] = domains.get(domain, 0) + 1
    
    # Python dictionaries ko list me convert karna for Chart.js
    domain_labels = list(domains.keys())
    domain_data = list(domains.values())
    
    conn.close()
    
    return render_template('dashboard.html', 
                           total=total_customers, 
                           active=active_customers, 
                           pending=pending_customers,
                           domain_labels=domain_labels,
                           domain_data=domain_data)

# @app.route('/')
# @login_required
# def dashboard():
#     conn = get_db_connection()
#     total_customers = conn.execute('SELECT COUNT(*) FROM customers').fetchone()[0]
#     active_customers = conn.execute('SELECT COUNT(*) FROM customers WHERE status = "Active"').fetchone()[0]
#     pending_customers = conn.execute('SELECT COUNT(*) FROM customers WHERE status = "Pending"').fetchone()[0]
#     conn.close()
    
#     return render_template('dashboard.html', total=total_customers, active=active_customers, pending=pending_customers)

@app.route('/customers')
@login_required
def customers():
    conn = get_db_connection()
    all_customers = conn.execute('SELECT * FROM customers ORDER BY date_added DESC').fetchall()
    conn.close()
    return render_template('customers.html', customers=all_customers)

@app.route('/add_customer', methods=['POST'])
@login_required
def add_customer():
    name = request.form['name']
    phone = request.form['phone']
    email = request.form['email']
    address = request.form['address']
    status = request.form['status']
    
    conn = get_db_connection()
    conn.execute('INSERT INTO customers (name, phone, email, address, status) VALUES (?, ?, ?, ?, ?)',
                 (name, phone, email, address, status))
    conn.commit()
    conn.close()
    
    flash('Customer added successfully!', 'success')
    return redirect(url_for('customers'))

@app.route('/edit_customer/<int:id>', methods=['POST'])
@login_required
def edit_customer(id):
    name = request.form['name']
    phone = request.form['phone']
    email = request.form['email']
    address = request.form['address']
    status = request.form['status']
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE customers 
        SET name = ?, phone = ?, email = ?, address = ?, status = ? 
        WHERE id = ?
    ''', (name, phone, email, address, status, id))
    conn.commit()
    conn.close()
    
    flash('Customer updated successfully!', 'success')
    return redirect(url_for('customers'))

@app.route('/delete_customer/<int:id>', methods=['POST'])
@login_required
def delete_customer(id):
    conn = get_db_connection()
    
    # 1. Fetch the customer's data BEFORE deleting them
    customer = conn.execute('SELECT * FROM customers WHERE id = ?', (id,)).fetchone()
    
    # 2. Save their data temporarily in the session
    session['deleted_customer'] = {
        'name': customer['name'],
        'phone': customer['phone'],
        'email': customer['email'],
        'address': customer['address'],
        'status': customer['status']
    }
    
    # 3. Now delete them from the database
    conn.execute('DELETE FROM customers WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    # 4. Show a flash message with an HTML 'Undo' button
    undo_url = url_for('undo_delete')
    flash(f"Customer <b>{customer['name']}</b> deleted. <form action='{undo_url}' method='POST' class='d-inline ms-3'><button type='submit' class='btn btn-sm btn-outline-danger'>Undo Delete</button></form>", 'warning')
    
    return redirect(url_for('customers'))

@app.route('/undo_delete', methods=['POST'])
@login_required
def undo_delete():
    # Check if we have deleted data saved in the session
    if 'deleted_customer' in session:
        cust = session['deleted_customer']
        
        # Insert the data back into the database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO customers (name, phone, email, address, status) 
            VALUES (?, ?, ?, ?, ?)
        ''', (cust['name'], cust['phone'], cust['email'], cust['address'], cust['status']))
        conn.commit()
        conn.close()
        
        # Clear the session so they can't undo multiple times
        session.pop('deleted_customer', None)
        
        flash(f"Customer <b>{cust['name']}</b> restored successfully!", 'success')
    else:
        flash('Nothing to undo.', 'info')
        
    return redirect(url_for('customers'))

if __name__ == '__main__':
    app.run(debug=True)