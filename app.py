import json
import sqlite3
import datetime 
from flask import Flask, render_template, request, jsonify, session, make_response, redirect, url_for, g
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, init_db, init_app, get_user_id_by_username 

# --- Configuration ---
app = Flask(__name__)
# IMPORTANT: In a real application, set a strong secret key for session management!
app.secret_key = 'super_secret_dev_key_change_me_in_production'

# --- SESSION TIMEOUT CONFIGURATION ---
# Set the session lifetime to 10 minutes.
# If the user doesn't access any route for this period, the session cookie will expire.
app.permanent_session_lifetime = datetime.timedelta(minutes=10)

# Secret Keys for Registration Restriction and Role Assignment
ADMIN_SECRET_KEY = "finance-admin-2024" 
STANDARD_USER_SECRET_KEY = "read-only-guest-2024"

# Initialize the database connection teardown
init_app(app)

# --- Utility Functions ---

def get_user_id():
    """Helper to retrieve the ID of the current logged-in user."""
    if 'username' not in session:
        return None
    return get_user_id_by_username(session['username'])

def check_permission(required_role):
    """Checks if the logged-in user has the required role."""
    return session.get('role') == required_role

# --- Flask Routes ---

@app.route('/')
def index():
    """Renders the authentication page using the template."""
    logged_in_user = session.get('username')
    logged_in_role = session.get('role')
    
    # Passes user and role to the template
    return render_template('index.html', logged_in_user=logged_in_user, logged_in_role=logged_in_role)

@app.route('/register', methods=['POST'])
def register():
    """Handles new user registration."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    secret_key = data.get('secret_key')

    if not all([username, password, secret_key]):
        return jsonify({"message": "Missing username, password, or secret key"}), 400

    assigned_role = None
    if secret_key == ADMIN_SECRET_KEY:
        assigned_role = 'admin'
    elif secret_key == STANDARD_USER_SECRET_KEY:
        assigned_role = 'standard'
    else:
        return jsonify({"message": "Invalid secret key. You are not authorized to create an account."}), 403

    db = get_db()
    
    if db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
        return jsonify({"message": "Username already exists"}), 409

    try:
        hashed_password = generate_password_hash(password)
        db.execute(
            'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
            (username, hashed_password, assigned_role)
        )
        db.commit()
        
        print(f"User '{username}' successfully registered with role '{assigned_role}'.")
        return jsonify({"message": f"Account created! Role: {assigned_role.upper()}"}), 201
        
    except sqlite3.Error as e:
        print(f"Database error during registration: {e}")
        return jsonify({"message": "A database error occurred during registration."}), 500


@app.route('/login', methods=['POST'])
def login():
    """Handles user login."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not all([username, password]):
        return jsonify({"message": "Missing username or password"}), 400

    db = get_db()
    
    user_row = db.execute(
        'SELECT password_hash, role FROM users WHERE username = ?', (username,)
    ).fetchone()

    if user_row:
        if check_password_hash(user_row['password_hash'], password):
            user_role = user_row['role']
            session['username'] = username
            session['role'] = user_role
            print(f"User '{username}' logged in with role '{user_role}'.")
            
            return jsonify({
                "message": f"Login successful, welcome {username}!",
                "role": user_role
            }), 200
        
    return jsonify({"message": "Invalid username or password"}), 401

@app.route('/logout', methods=['POST'])
def logout():
    """Handles user logout."""
    if 'username' in session:
        username = session['username']
        session.pop('username', None)
        session.pop('role', None) 
        print(f"User '{username}' logged out.")
        return jsonify({"message": "You have been logged out successfully"}), 200
    return jsonify({"message": "Not logged in"}), 400

@app.route('/categories', methods=['GET', 'POST'])
def categories():
    """Handles fetching and creating categories for the current user."""
    user_id = get_user_id()
    if user_id is None:
        return jsonify({"message": "Unauthorized"}), 401

    db = get_db()

    if request.method == 'GET':
        # Fetch all categories, no type filtering
        categories_data = db.execute(
            'SELECT id, name FROM categories WHERE user_id = ? ORDER BY name', 
            (user_id,)
        ).fetchall()
        
        categories_list = [dict(row) for row in categories_data]
        return jsonify(categories_list), 200

    elif request.method == 'POST':
        data = request.get_json()
        category_name = data.get('name')

        # No category type needed for creation
        if not category_name:
            return jsonify({"message": "Invalid category name"}), 400
        
        try:
            # Insert statement only uses name
            cursor = db.execute(
                'INSERT INTO categories (user_id, name) VALUES (?, ?)',
                (user_id, category_name)
            )
            db.commit()
            return jsonify({
                "message": f"Category '{category_name}' created successfully",
                "id": cursor.lastrowid,
                "name": category_name
            }), 201
        except sqlite3.IntegrityError:
            return jsonify({"message": f"Category '{category_name}' already exists"}), 409
        except sqlite3.Error as e:
            print(f"Database error during category creation: {e}")
            return jsonify({"message": "Database error occurred"}), 500

@app.route('/transactions', methods=['POST'])
def add_transaction():
    """Handles adding a new transaction to the database."""
    user_id = get_user_id()
    if user_id is None:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()
    amount = data.get('amount')
    type_ = data.get('type') # 'income' or 'expense' - still necessary for the transaction record
    note = data.get('note', '')
    category_id = data.get('category_id')

    # Basic input validation
    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({"message": "Amount must be positive"}), 400
    except (ValueError, TypeError):
        return jsonify({"message": "Invalid amount"}), 400
        
    if type_ not in ['income', 'expense'] or not category_id:
        return jsonify({"message": "Missing transaction type or category"}), 400

    # Role-based permission check: Only 'admin' can add income (remains)
    if type_ == 'income' and not check_permission('admin'):
        return jsonify({"message": "Only Admin users can record Income"}), 403
    
    db = get_db()
    
    try:
        # Only verify category belongs to user
        category_check = db.execute(
            'SELECT id, name FROM categories WHERE id = ? AND user_id = ?',
            (category_id, user_id)
        ).fetchone()

        if not category_check:
             return jsonify({"message": f"Invalid category ID"}), 400
        
        category_name = category_check['name']

        # Insert transaction into the database
        cursor = db.execute(
            'INSERT INTO transactions (user_id, amount, type, note, category_id) VALUES (?, ?, ?, ?, ?)',
            (user_id, amount, type_, note, category_id)
        )
        db.commit()

        return jsonify({
            "message": f"{type_.capitalize()} of ${amount:.2f} recorded under '{category_name}'",
            "id": cursor.lastrowid,
            "timestamp": datetime.datetime.now().isoformat()
        }), 201

    except sqlite3.Error as e:
        print(f"Database error during transaction insertion: {e}")
        return jsonify({"message": "A database error occurred during transaction recording."}), 500
    
@app.route('/transactions_csv', methods=['GET'])
def transactions_csv():
    """
    Downloads transactions for a given date range and optional category as a CSV file.
    """
    user_id = get_user_id()
    if user_id is None:
        return jsonify({"message": "Unauthorized"}), 401
    
    # --- SECURITY ENFORCEMENT ---
    if not check_permission('admin'):
        return jsonify({"message": "Forbidden: Only Admin users can export data"}), 403

    # Fetch filters from query parameters
    category_id = request.args.get('category_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date') 
    db = get_db()
    
    # Base WHERE clause parts, aliased with 't' for transactions table
    where_parts = ["t.user_id = ?"]
    query_params = [user_id]
    
    # 1. Category Filtering
    if category_id and category_id != '0': # '0' is usually for "All"
        try:
            category_id_int = int(category_id)
            # Use alias 't' for category_id as it belongs to the transactions table
            where_parts.append("t.category_id = ?")
            query_params.append(category_id_int)
        except ValueError:
            return jsonify({"message": "Invalid category_id format"}), 400

    # 2. Date Filtering
    if start_date:
        where_parts.append("t.timestamp >= ?")
        query_params.append(start_date + " 00:00:00") 
    
    if end_date:
        where_parts.append("t.timestamp <= ?")
        query_params.append(end_date + " 23:59:59")
    
    # Construct the full WHERE clause
    where_clause = " AND ".join(where_parts)
    
    try:
        # Query to fetch all relevant transaction details, including category name
        transactions_query = f"""
            SELECT 
                t.timestamp,
                t.type,
                t.amount,
                c.name AS category,
                t.note
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE {where_clause}
            ORDER BY t.timestamp DESC
        """
        transaction_results = db.execute(transactions_query, tuple(query_params)).fetchall()
        
        # Build CSV content
        csv_output = ["Timestamp,Type,Amount,Category,Note"] # CSV Header
        
        for row in transaction_results:
            # Escape quotes in notes if necessary, though simpler to avoid it for this scope
            note_safe = str(row['note']).replace('"', '""')
            
            line = f"{row['timestamp']},{row['type']},{row['amount']:.2f},\"{row['category']}\",\"{note_safe}\""
            csv_output.append(line)
            
        csv_string = "\n".join(csv_output)
        
        # Create a Flask response object with the CSV data and download headers
        response = make_response(csv_string)
        response.headers["Content-Disposition"] = "attachment; filename=transactions_export.csv"
        response.headers["Content-type"] = "text/csv"
        return response

    except sqlite3.Error as e:
        print(f"Database error during CSV export: {e}")
        return jsonify({"message": "A database error occurred during CSV export."}), 500

@app.route('/summary', methods=['GET'])
def get_summary():
    """
    Calculates the financial summary, including overall balance, daily trends, 
    and top categories, optionally filtered by category and date range.
    
    The 't' alias is used for the transactions table in the WHERE clause 
    to prevent 'ambiguous column name' errors when joining tables.
    """
    user_id = get_user_id()
    if user_id is None:
        return jsonify({"message": "Unauthorized"}), 401

    # Permission Check: Only admin can access summary
    if not check_permission('admin'):
        return jsonify({"message": "Forbidden: Only Admin users can view the summary"}), 403

    category_id = request.args.get('category_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date') # Inclusive end date
    db = get_db()
    
    # Base WHERE clause parts, now aliased with 't' (for transactions table) 
    # to resolve the 'ambiguous column name: user_id' error in join queries.
    where_parts = ["t.user_id = ?"]
    query_params = [user_id]
    category_name = "All Categories"
    
    # 1. Category Filtering
    if category_id:
        try:
            category_id_int = int(category_id)
            category_row = db.execute(
                'SELECT name FROM categories WHERE id = ? AND user_id = ?', 
                (category_id_int, user_id)
            ).fetchone()
            
            if not category_row:
                return jsonify({"message": "Invalid category ID for this user"}), 400
                
            category_name = category_row['name']
            # Use alias 't' for category_id as it belongs to the transactions table
            where_parts.append("t.category_id = ?")
            query_params.append(category_id_int)

        except ValueError:
            return jsonify({"message": "Invalid category_id format"}), 400

    # 2. Date Filtering
    if start_date:
        # Transactions on or after the start date (inclusive)
        where_parts.append("t.timestamp >= ?")
        query_params.append(start_date + " 00:00:00") 
    
    if end_date:
        # Transactions on or before the end date (inclusive)
        where_parts.append("t.timestamp <= ?")
        query_params.append(end_date + " 23:59:59")
    
    # Construct the full WHERE clause
    where_clause = " AND ".join(where_parts)
    
    try:
        # A. Calculate Overall Balance (Income - Expense)
        # Use alias 't' for the transactions table to match the aliased WHERE clause
        balance_query = f"SELECT SUM(CASE WHEN type='income' THEN amount ELSE -amount END) AS balance FROM transactions t WHERE {where_clause}"
        balance_result = db.execute(balance_query, tuple(query_params)).fetchone()
        balance = balance_result['balance'] if balance_result and balance_result['balance'] is not None else 0.0

        # B. Get Daily Summary for Line Plot (Grouping by date)
        # Use alias 't' for the transactions table to match the aliased WHERE clause
        daily_summary_query = f"""
            SELECT 
                SUBSTR(t.timestamp, 1, 10) AS date,
                SUM(CASE WHEN t.type='income' THEN t.amount ELSE 0 END) AS total_income,
                SUM(CASE WHEN t.type='expense' THEN t.amount ELSE 0 END) AS total_expense
            FROM transactions t
            WHERE {where_clause}
            GROUP BY date
            ORDER BY date
        """
        # Execute the query with the current parameters
        daily_results = db.execute(daily_summary_query, tuple(query_params)).fetchall()
        daily_summary = [dict(row) for row in daily_results]

        # C. Get Top Income/Expense Categories 
        # This query already uses aliases t and c, and now the where_clause is compatible
        category_summary_query = f"""
            SELECT 
                c.name AS category_name,
                t.type,
                SUM(t.amount) AS total_amount
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE {where_clause}
            GROUP BY c.name, t.type
            ORDER BY t.type DESC, total_amount DESC
        """
        category_results = db.execute(category_summary_query, tuple(query_params)).fetchall()
        
        top_income_categories = []
        top_expense_categories = []
        
        for row in category_results:
            cat_data = {'name': row['category_name'], 'total_amount': round(row['total_amount'], 2)}
            if row['type'] == 'income':
                top_income_categories.append(cat_data)
            elif row['type'] == 'expense':
                top_expense_categories.append(cat_data)
        
        # Sort and limit to top 5 categories
        top_income_categories = sorted(top_income_categories, key=lambda x: x['total_amount'], reverse=True)[:5]
        top_expense_categories = sorted(top_expense_categories, key=lambda x: x['total_amount'], reverse=True)[:5]


        return jsonify({
            "category_name": category_name,
            "start_date": start_date,
            "end_date": end_date,
            "balance": balance,
            "daily_summary": daily_summary,
            "top_income_categories": top_income_categories,
            "top_expense_categories": top_expense_categories
        }), 200

    except sqlite3.Error as e:
        print(f"Database error during detailed summary calculation: {e}")
        return jsonify({"message": "A database error occurred during summary calculation."}), 500


# --- App Execution ---
if __name__ == '__main__':
    # Initialize the database before running the app
    with app.app_context():
        init_db(app)

    print(f"--- Development Server Initialized ---")
    print(f"Admin Key (Role: admin): '{ADMIN_SECRET_KEY}'")
    print(f"Standard Key (Role: standard): '{STANDARD_USER_SECRET_KEY}'")
    print(f"Access the app at: http://127.0.0.1:5000/")
    
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=8080)

