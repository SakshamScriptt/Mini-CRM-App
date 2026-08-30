import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Create Admin Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Create Customers Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            address TEXT NOT NULL,
            status TEXT NOT NULL,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Insert default admin if it doesn't exist
    cursor.execute('SELECT * FROM admin WHERE username = "admin"')
    if not cursor.fetchone():
        cursor.execute('INSERT INTO admin (username, password) VALUES (?, ?)', ('admin', 'admin123'))

    # Insert some dummy customer data for testing
    cursor.execute('SELECT COUNT(*) FROM customers')
    if cursor.fetchone()[0] == 0:
        sample_customers = [
            ('John Doe', '555-0101', 'john@example.com', '123 Main St, NY', 'Active', datetime.now()),
            ('Jane Smith', '555-0102', 'jane@example.com', '456 Oak Ave, CA', 'Pending', datetime.now()),
            ('Mike Johnson', '555-0103', 'mike@example.com', '789 Pine Rd, TX', 'Active', datetime.now())
        ]
        cursor.executemany('''
            INSERT INTO customers (name, phone, email, address, status, date_added) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', sample_customers)

    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()