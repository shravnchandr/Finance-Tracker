import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, make_response, send_from_directory
import sqlite3
import datetime as dt
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import csv
import io
from dotenv import load_dotenv


load_dotenv()  # Load variables from .env

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
app.config['PERMANENT_SESSION_LIFETIME'] = dt.timedelta(minutes=15)

# Registration keys
ADMIN_KEY = os.environ.get('ADMIN_KEY')
USER_KEY = os.environ.get('USER_KEY')

# Database setup
def init_db():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    
    # Users table with role
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  role TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Transactions table (expenses and income)
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
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
    c.execute('''CREATE TABLE IF NOT EXISTS categories
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE NOT NULL,
                  type TEXT NOT NULL,
                  icon TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Insert default categories if table is empty
    c.execute('SELECT COUNT(*) FROM categories')
    if c.fetchone()[0] == 0:
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
        c.executemany('INSERT INTO categories (name, type, icon) VALUES (?, ?, ?)', 
                      default_categories)
    
    conn.commit()
    conn.close()

init_db()

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'doc', 'docx', 'xls', 'xlsx', 'txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def secure_filename_custom(filename):
    """Create a secure filename with timestamp"""
    # First use werkzeug's secure_filename
    filename = secure_filename(filename)
    # Then add timestamp
    name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{timestamp}_{name}{ext}"


# Database helper
def get_db():
    conn = sqlite3.connect('expenses.db')
    conn.row_factory = sqlite3.Row
    return conn

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        reg_key = data.get('registration_key')
        
        if not username or not password or not reg_key:
            return jsonify({'error': 'All fields are required'}), 400
        
        # Check registration key and determine role
        if reg_key == ADMIN_KEY:
            role = 'admin'
        elif reg_key == USER_KEY:
            role = 'user'
        else:
            return jsonify({'error': 'Invalid registration key'}), 400
        
        conn = get_db()
        c = conn.cursor()
        
        # Check if user exists
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        if c.fetchone():
            conn.close()
            return jsonify({'error': 'Username already exists'}), 400
        
        # Create user
        hashed_password = generate_password_hash(password)
        c.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                  (username, hashed_password, role))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        
        session['user_id'] = user_id
        session['username'] = username
        session['role'] = role
        
        return jsonify({'message': 'Registration successful', 'redirect': '/'}), 201
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return jsonify({'message': 'Login successful', 'redirect': '/'}), 200
        
        return jsonify({'error': 'Invalid credentials'}), 401
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    role = session.get('role')
    username = session.get('username')
    return render_template('index.html', username=username, role=role)

# Transaction routes
@app.route('/api/transactions', methods=['GET'])
@login_required
def get_transactions():
    user_id = session['user_id']
    role = session['role']
    conn = get_db()
    c = conn.cursor()
    
    # Get filter parameters
    trans_type = request.args.get('type')
    category = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Admin sees all transactions, users see only their own
    if role == 'admin':
        query = 'SELECT * FROM transactions WHERE 1=1'
        params = []
    else:
        query = 'SELECT * FROM transactions WHERE user_id = ?'
        params = [user_id]
    
    if trans_type and trans_type != 'all':
        query += ' AND type = ?'
        params.append(trans_type)
    
    if category and category != 'all':
        query += ' AND category = ?'
        params.append(category)
    
    if start_date:
        query += ' AND date >= ?'
        params.append(start_date)
    
    if end_date:
        query += ' AND date <= ?'
        params.append(end_date)
    
    query += ' ORDER BY date DESC, id DESC'
    
    c.execute(query, params)
    transactions = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return jsonify(transactions)

@app.route('/api/transactions', methods=['POST'])
@login_required
def add_transaction():
    user_id = session['user_id']
    username = session['username']

    try:
        file = request.files.get('attachment')  # safe getter

        # If multipart/form-data
        if file or request.form:
            amount = request.form.get('amount')
            trans_type = request.form.get('type')
            category = request.form.get('category')
            description = request.form.get('description', '')
            date = request.form.get('date')
        else:
            # JSON
            data = request.get_json(force=True)
            amount = data.get('amount')
            trans_type = data.get('type')
            category = data.get('category')
            description = data.get('description', '')
            date = data.get('date')

        # Handle attachment
        attachment_filename = None
        attachment_path = None
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename_custom(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            attachment_filename = file.filename
            attachment_path = filename

        # Validate
        if not all([amount, trans_type, category, date]):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db()
        c = conn.cursor()
        c.execute('''INSERT INTO transactions 
                     (user_id, username, amount, type, category, description, date, 
                      attachment_filename, attachment_path)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (user_id, username, amount, trans_type, category, description, date,
                   attachment_filename, attachment_path))
        conn.commit()
        transaction_id = c.lastrowid
        conn.close()

        return jsonify({'id': transaction_id, 'message': 'Transaction added successfully'}), 201

    except Exception as e:
        print(f"Error adding transaction: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/transactions/<int:transaction_id>', methods=['PUT'])
@login_required
def update_transaction(transaction_id):
    user_id = session['user_id']
    username = session['username']
    role = session['role']

    conn = get_db()
    c = conn.cursor()

    # Fetch old record
    c.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,))
    old_trans = c.fetchone()
    if not old_trans:
        conn.close()
        return jsonify({'error': 'Transaction not found'}), 404

    old_attachment_filename = old_trans['attachment_filename']
    old_attachment_path = old_trans['attachment_path']

    file = request.files.get('attachment')

    # Parse form-data or JSON
    if file or request.form:
        amount = request.form.get('amount')
        trans_type = request.form.get('type')
        category = request.form.get('category')
        description = request.form.get('description', '')
        date = request.form.get('date')
    else:
        data = request.get_json(force=True)
        amount = data.get('amount')
        trans_type = data.get('type')
        category = data.get('category')
        description = data.get('description', '')
        date = data.get('date')

    attachment_filename = old_attachment_filename
    attachment_path = old_attachment_path

    # Handle new file upload
    if file and file.filename and allowed_file(file.filename):
        # Delete old file if it exists
        if old_attachment_path:
            old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], old_attachment_path)
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
        filename = secure_filename_custom(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        attachment_filename = file.filename
        attachment_path = filename

    # Update DB
    if role == 'admin':
        c.execute('''UPDATE transactions
                     SET amount = ?, type = ?, category = ?, description = ?, date = ?, 
                         user_id = ?, username = ?, attachment_filename = ?, attachment_path = ?
                     WHERE id = ?''',
                  (amount, trans_type, category, description, date,
                   user_id, username, attachment_filename, attachment_path, transaction_id))
    else:
        c.execute('''UPDATE transactions
                     SET amount = ?, type = ?, category = ?, description = ?, date = ?, 
                         attachment_filename = ?, attachment_path = ?
                     WHERE id = ? AND user_id = ?''',
                  (amount, trans_type, category, description, date,
                   attachment_filename, attachment_path, transaction_id, user_id))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Transaction updated successfully'})


@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
@login_required
def delete_transaction(transaction_id):
    user_id = session['user_id']
    role = session['role']
    
    conn = get_db()
    c = conn.cursor()
    
    # Get transaction to delete attached file
    if role == 'admin':
        c.execute('SELECT attachment_path FROM transactions WHERE id = ?', (transaction_id,))
    else:
        c.execute('SELECT attachment_path FROM transactions WHERE id = ? AND user_id = ?', 
                  (transaction_id, user_id))
    
    trans = c.fetchone()
    
    if trans and trans['attachment_path']:
        # Delete file from filesystem
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], trans['attachment_path'])
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Error deleting file: {e}")
    
    # Admin can delete any transaction, users can only delete their own
    if role == 'admin':
        c.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
    else:
        c.execute('DELETE FROM transactions WHERE id = ? AND user_id = ?', 
                  (transaction_id, user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Transaction deleted successfully'})

@app.route('/api/stats', methods=['GET'])
@login_required
@admin_required
def get_stats():
    # Only admins can access stats
    conn = get_db()
    c = conn.cursor()
    
    # Total income (all users)
    c.execute('SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE type = "income"')
    total_income = c.fetchone()['total']
    
    # Total expenses (all users)
    c.execute('SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE type = "expense"')
    total_expenses = c.fetchone()['total']
    
    # Category breakdown for expenses
    c.execute('''SELECT category, COALESCE(SUM(amount), 0) as total 
                 FROM transactions 
                 WHERE type = "expense"
                 GROUP BY category 
                 ORDER BY total DESC''')
    expense_by_category = [dict(row) for row in c.fetchall()]
    
    # Category breakdown for income
    c.execute('''SELECT category, COALESCE(SUM(amount), 0) as total 
                 FROM transactions 
                 WHERE type = "income"
                 GROUP BY category 
                 ORDER BY total DESC''')
    income_by_category = [dict(row) for row in c.fetchall()]
    
    # Monthly breakdown (last 6 months)
    c.execute('''SELECT strftime('%Y-%m', date) as month, 
                 type,
                 COALESCE(SUM(amount), 0) as total
                 FROM transactions
                 WHERE date >= date('now', '-6 months')
                 GROUP BY month, type
                 ORDER BY month DESC''')
    by_month = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    return jsonify({
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': total_income - total_expenses,
        'expense_by_category': expense_by_category,
        'income_by_category': income_by_category,
        'by_month': by_month
    })

@app.route('/api/download-csv', methods=['GET'])
@login_required
@admin_required
def download_csv():
    # Only admins can download CSV
    
    # Get filter parameters
    trans_type = request.args.get('type')
    category = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    conn = get_db()
    c = conn.cursor()
    
    query = 'SELECT date, username, type, category, description, amount FROM transactions WHERE 1=1'
    params = []
    
    if trans_type and trans_type != 'all':
        query += ' AND type = ?'
        params.append(trans_type)
    
    if category and category != 'all':
        query += ' AND category = ?'
        params.append(category)
    
    if start_date:
        query += ' AND date >= ?'
        params.append(start_date)
    
    if end_date:
        query += ' AND date <= ?'
        params.append(end_date)
    
    query += ' ORDER BY date DESC'
    
    c.execute(query, params)
    transactions = c.fetchall()
    conn.close()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'User', 'Type', 'Category', 'Description', 'Amount'])
    
    for trans in transactions:
        writer.writerow(trans)
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=transactions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return response

# Category management routes
@app.route('/api/categories', methods=['GET'])
@login_required
def get_categories():
    trans_type = request.args.get('type', 'all')
    
    conn = get_db()
    c = conn.cursor()
    
    if trans_type == 'all':
        c.execute('SELECT * FROM categories ORDER BY type, name')
    else:
        c.execute('SELECT * FROM categories WHERE type = ? ORDER BY name', (trans_type,))
    
    categories = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return jsonify(categories)

@app.route('/api/categories', methods=['POST'])
@login_required
@admin_required
def add_category():
    data = request.json
    
    if not data.get('name') or not data.get('type'):
        return jsonify({'error': 'Name and type are required'}), 400
    
    if data['type'] not in ['income', 'expense']:
        return jsonify({'error': 'Type must be income or expense'}), 400
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute('INSERT INTO categories (name, type, icon) VALUES (?, ?, ?)',
                  (data['name'], data['type'], data.get('icon', '📦')))
        conn.commit()
        category_id = c.lastrowid
        conn.close()
        return jsonify({'id': category_id, 'message': 'Category added successfully'}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Category already exists'}), 400

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_category(category_id):
    conn = get_db()
    c = conn.cursor()
    
    # Check if category is in use
    c.execute('SELECT COUNT(*) as count FROM transactions WHERE category IN (SELECT name FROM categories WHERE id = ?)', 
              (category_id,))
    count = c.fetchone()['count']
    
    if count > 0:
        conn.close()
        return jsonify({'error': 'Cannot delete category that is in use'}), 400
    
    c.execute('DELETE FROM categories WHERE id = ?', (category_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Category deleted successfully'})

@app.route('/api/attachments/<filename>')
@login_required
def download_attachment(filename):
    """Download or view attachment file"""
    try:
        # Verify file exists
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        print(f"Error serving file: {e}")
        return jsonify({'error': 'File not found'}), 404

# Delete attachment route
@app.route('/api/transactions/<int:transaction_id>/attachment', methods=['DELETE'])
@login_required
def delete_attachment(transaction_id):
    user_id = session['user_id']
    role = session['role']
    
    conn = get_db()
    c = conn.cursor()
    
    # Get transaction
    if role == 'admin':
        c.execute('SELECT attachment_path FROM transactions WHERE id = ?', (transaction_id,))
    else:
        c.execute('SELECT attachment_path FROM transactions WHERE id = ? AND user_id = ?', 
                  (transaction_id, user_id))
    
    trans = c.fetchone()
    
    if not trans:
        conn.close()
        return jsonify({'error': 'Transaction not found'}), 404
    
    if trans['attachment_path']:
        # Delete file from filesystem
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], trans['attachment_path'])
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Error deleting file: {e}")
        
        # Update database
        if role == 'admin':
            c.execute('UPDATE transactions SET attachment_filename = NULL, attachment_path = NULL WHERE id = ?', 
                      (transaction_id,))
        else:
            c.execute('UPDATE transactions SET attachment_filename = NULL, attachment_path = NULL WHERE id = ? AND user_id = ?', 
                      (transaction_id, user_id))
        
        conn.commit()
    
    conn.close()
    
    return jsonify({'message': 'Attachment deleted successfully'})

if __name__ == '__main__':
    app.run(debug=True, port=8080)
    # app.run(host='0.0.0.0', port=8080)