import sqlite3
from flask import Blueprint, request, jsonify
from app.db import get_db
from app.utils import login_required, admin_required

bp = Blueprint('categories', __name__, url_prefix='/api/categories')

@bp.route('', methods=['GET'])
@login_required
def get_categories():
    trans_type = request.args.get('type', 'all')
    
    db = get_db()
    c = db.cursor()
    
    if trans_type == 'all':
        c.execute('SELECT * FROM categories ORDER BY type, name')
    else:
        c.execute('SELECT * FROM categories WHERE type = ? ORDER BY name', (trans_type,))
    
    categories = [dict(row) for row in c.fetchall()]
    
    return jsonify(categories)

@bp.route('', methods=['POST'])
@login_required
@admin_required
def add_category():
    data = request.json
    
    if not data.get('name') or not data.get('type'):
        return jsonify({'error': 'Name and type are required'}), 400
    
    if data['type'] not in ['income', 'expense']:
        return jsonify({'error': 'Type must be income or expense'}), 400
    
    db = get_db()
    c = db.cursor()
    
    try:
        c.execute('INSERT INTO categories (name, type, icon) VALUES (?, ?, ?)',
                  (data['name'], data['type'], data.get('icon', '📦')))
        db.commit()
        category_id = c.lastrowid
        return jsonify({'id': category_id, 'message': 'Category added successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Category already exists'}), 400

@bp.route('/<int:category_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_category(category_id):
    db = get_db()
    c = db.cursor()
    
    # Check if category is in use
    c.execute('SELECT COUNT(*) as count FROM transactions WHERE category IN (SELECT name FROM categories WHERE id = ?)', 
              (category_id,))
    count = c.fetchone()['count']
    
    if count > 0:
        return jsonify({'error': 'Cannot delete category that is in use'}), 400
    
    c.execute('DELETE FROM categories WHERE id = ?', (category_id,))
    db.commit()
    
    return jsonify({'message': 'Category deleted successfully'})
