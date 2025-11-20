import os
import io
import csv
from datetime import datetime
from flask import Blueprint, request, jsonify, session, current_app, make_response, send_from_directory
from werkzeug.utils import secure_filename
from app.db import get_db
from app.utils import login_required, admin_required, allowed_file, secure_filename_custom

bp = Blueprint('transactions', __name__, url_prefix='/api')

@bp.route('/transactions', methods=['GET'])
@login_required
def get_transactions():
    user_id = session['user_id']
    role = session['role']
    db = get_db()
    c = db.cursor()
    
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
    
    return jsonify(transactions)

@bp.route('/transactions', methods=['POST'])
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
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            attachment_filename = file.filename
            attachment_path = filename

        # Validate
        if not all([amount, trans_type, category, date]):
            return jsonify({'error': 'Missing required fields'}), 400

        db = get_db()
        c = db.cursor()
        c.execute('''INSERT INTO transactions 
                     (user_id, username, amount, type, category, description, date, 
                      attachment_filename, attachment_path)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (user_id, username, amount, trans_type, category, description, date,
                   attachment_filename, attachment_path))
        db.commit()
        transaction_id = c.lastrowid

        return jsonify({'id': transaction_id, 'message': 'Transaction added successfully'}), 201

    except Exception as e:
        print(f"Error adding transaction: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/transactions/<int:transaction_id>', methods=['PUT'])
@login_required
def update_transaction(transaction_id):
    user_id = session['user_id']
    username = session['username']
    role = session['role']

    db = get_db()
    c = db.cursor()

    # Fetch old record
    c.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,))
    old_trans = c.fetchone()
    if not old_trans:
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
            old_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], old_attachment_path)
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
        filename = secure_filename_custom(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
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

    db.commit()

    return jsonify({'message': 'Transaction updated successfully'})


@bp.route('/transactions/<int:transaction_id>', methods=['DELETE'])
@login_required
def delete_transaction(transaction_id):
    user_id = session['user_id']
    role = session['role']
    
    db = get_db()
    c = db.cursor()
    
    # Get transaction to delete attached file
    if role == 'admin':
        c.execute('SELECT attachment_path FROM transactions WHERE id = ?', (transaction_id,))
    else:
        c.execute('SELECT attachment_path FROM transactions WHERE id = ? AND user_id = ?', 
                  (transaction_id, user_id))
    
    trans = c.fetchone()
    
    if trans and trans['attachment_path']:
        # Delete file from filesystem
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], trans['attachment_path'])
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
    
    db.commit()
    
    return jsonify({'message': 'Transaction deleted successfully'})

@bp.route('/stats', methods=['GET'])
@login_required
@admin_required
def get_stats():
    # Only admins can access stats
    db = get_db()
    c = db.cursor()
    
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
    
    return jsonify({
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': total_income - total_expenses,
        'expense_by_category': expense_by_category,
        'income_by_category': income_by_category,
        'by_month': by_month
    })

@bp.route('/download-csv', methods=['GET'])
@login_required
@admin_required
def download_csv():
    # Only admins can download CSV
    
    # Get filter parameters
    trans_type = request.args.get('type')
    category = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    db = get_db()
    c = db.cursor()
    
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

@bp.route('/attachments/<filename>')
@login_required
def download_attachment(filename):
    """Download or view attachment file"""
    try:
        # Verify file exists
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        print(f"Error serving file: {e}")
        return jsonify({'error': 'File not found'}), 404

# Delete attachment route
@bp.route('/transactions/<int:transaction_id>/attachment', methods=['DELETE'])
@login_required
def delete_attachment(transaction_id):
    user_id = session['user_id']
    role = session['role']
    
    db = get_db()
    c = db.cursor()
    
    # Get transaction
    if role == 'admin':
        c.execute('SELECT attachment_path FROM transactions WHERE id = ?', (transaction_id,))
    else:
        c.execute('SELECT attachment_path FROM transactions WHERE id = ? AND user_id = ?', 
                  (transaction_id, user_id))
    
    trans = c.fetchone()
    
    if not trans:
        return jsonify({'error': 'Transaction not found'}), 404
    
    if trans['attachment_path']:
        # Delete file from filesystem
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], trans['attachment_path'])
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
        
        db.commit()
    
    return jsonify({'message': 'Attachment deleted successfully'})
