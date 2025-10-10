import sqlite3
import click
from flask import current_app, g
from werkzeug.security import generate_password_hash

# Define the path to the database file
DATABASE = 'finance_tracker.db'

def get_db():
    """Establishes or returns the current database connection."""
    # 'g' is a global object for the application context
    if 'db' not in g:
        g.db = sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        # Allows accessing columns by name (as dictionary keys)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Closes the database connection if it exists."""
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db(app):
    """Initializes the database structure, ensures the 'role' column exists, and seeds the admin user."""
    db = get_db()

    # Create the users table if it doesn't exist
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'standard' 
        )
    ''')
    
    # Create the categories table
    # IMPORTANT UPDATE: Removed 'type' column. Categories are now generic.
    db.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            UNIQUE(user_id, name)
        )
    ''')
    
    # Create the transactions table (Type remains here to track if it was income or expense)
    db.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL, -- 'income' or 'expense'
            note TEXT,
            category_id INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    ''')
    db.commit()

    # Attempt to add the 'role' column if the table existed without it (migration handling)
    try:
        db.execute("SELECT role FROM users LIMIT 1")
    except sqlite3.OperationalError:
        print("Adding 'role' column to existing users table.")
        db.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'standard'")
        db.commit()


    # Seed the default admin user and default categories
    try:
        default_username = "admin"
        default_password = "password123"
        hashed_password = generate_password_hash(default_password)
        
        # Check if user already exists
        user_check = db.execute('SELECT id FROM users WHERE username = ?', (default_username,)).fetchone()
        
        if not user_check:
            # Insert the admin user with the 'admin' role
            cursor = db.execute(
                'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
                (default_username, hashed_password, 'admin')
            )
            admin_id = cursor.lastrowid
            db.commit()
            print(f"Default admin user '{default_username}' seeded successfully with role 'admin'.")
            
            # Seed default categories for the admin user
            # UPDATE: Removed type from seeding data
            default_categories = [
                (admin_id, 'Salary'),
                (admin_id, 'Groceries'),
                (admin_id, 'Rent'),
                (admin_id, 'Utilities'),
                (admin_id, 'Investments'),
            ]
            # UPDATE: Insert statement updated
            db.executemany(
                'INSERT INTO categories (user_id, name) VALUES (?, ?)',
                default_categories
            )
            db.commit()
            print("Default categories seeded for admin user.")
            
        # Ensure the seeded admin always has the 'admin' role if the column was just added
        elif user_check and user_check['role'] != 'admin':
            db.execute('UPDATE users SET role = ? WHERE username = ?', ('admin', default_username))
            db.commit()
            
    except Exception as e:
        print(f"Could not seed admin user or categories: {e}")

# New helper function to get user ID (used by app.py)
def get_user_id_by_username(username):
    """Retrieves the user ID based on the username."""
    db = get_db()
    user_row = db.execute(
        'SELECT id FROM users WHERE username = ?', (username,)
    ).fetchone()
    return user_row['id'] if user_row else None
    
# This function will be called by the Flask app to hook up the database functions
def init_app(app):
    """Registers the close_db function with the app context."""
    app.teardown_appcontext(close_db)
