import sqlite3
import click
from flask import current_app, g
from flask.cli import with_appcontext

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA journal_mode=WAL')

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()
    
    # Users table with role
    db.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  role TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Transactions table (expenses and income)
    db.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  username TEXT NOT NULL,
                  amount REAL NOT NULL,
                  type TEXT NOT NULL,
                  category TEXT NOT NULL,
                  description TEXT,
                  date TEXT NOT NULL,
                  attachment_filename TEXT,
                  attachment_path TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Categories table
    db.execute('''CREATE TABLE IF NOT EXISTS categories
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE NOT NULL,
                  type TEXT NOT NULL,
                  icon TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Notes table
    db.execute('''CREATE TABLE IF NOT EXISTS notes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  title TEXT NOT NULL,
                  content TEXT,
                  color TEXT DEFAULT '#ffffff',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')

    # Reminders table
    db.execute('''CREATE TABLE IF NOT EXISTS reminders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  title TEXT NOT NULL,
                  description TEXT,
                  due_date TIMESTAMP,
                  is_completed BOOLEAN DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')

    # Calendar Events table
    db.execute('''CREATE TABLE IF NOT EXISTS calendar_events
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  title TEXT NOT NULL,
                  description TEXT,
                  start_time TIMESTAMP NOT NULL,
                  end_time TIMESTAMP,
                  color TEXT DEFAULT '#3b82f6',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Insert default categories if table is empty
    cur = db.execute('SELECT COUNT(*) FROM categories')
    if cur.fetchone()[0] == 0:
        default_categories = [
            ('🍔 Food & Dining', 'expense', '🍔'),
            ('🚗 Transport', 'expense', '🚗'),
            ('🛍️ Shopping', 'expense', '🛍️'),
            ('🎬 Entertainment', 'expense', '🎬'),
            ('💡 Bills & Utilities', 'expense', '💡'),
            ('🏥 Healthcare', 'expense', '🏥'),
            ('🎓 Education', 'expense', '🎓'),
            ('🏠 Rent', 'expense', '🏠'),
            ('📦 Other', 'expense', '📦'),
            ('💼 Salary', 'income', '💼'),
            ('💰 Business', 'income', '💰'),
            ('📈 Investment', 'income', '📈'),
            ('🎁 Gift', 'income', '🎁'),
            ('💵 Freelance', 'income', '💵'),
            ('🏆 Bonus', 'income', '🏆'),
        ]
        db.executemany('INSERT INTO categories (name, type, icon) VALUES (?, ?, ?)', 
                      default_categories)
    
    db.commit()

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
