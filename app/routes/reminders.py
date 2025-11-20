from flask import Blueprint, request, jsonify, session
from app.db import get_db
from app.utils import login_required

bp = Blueprint('reminders', __name__, url_prefix='/api/reminders')

@bp.route('', methods=['GET'])
@login_required
def get_reminders():
    user_id = session['user_id']
    db = get_db()
    c = db.cursor()
    c.execute('SELECT id, user_id, title, description, CAST(due_date AS TEXT) as due_date, is_completed, created_at FROM reminders WHERE user_id = ? ORDER BY due_date ASC', (user_id,))
    reminders = [dict(row) for row in c.fetchall()]
    return jsonify(reminders)

@bp.route('', methods=['POST'])
@login_required
def add_reminder():
    user_id = session['user_id']
    data = request.json
    title = data.get('title')
    description = data.get('description', '')
    due_date = data.get('due_date')
    
    if not title:
        return jsonify({'error': 'Title is required'}), 400
        
    db = get_db()
    c = db.cursor()
    c.execute('INSERT INTO reminders (user_id, title, description, due_date) VALUES (?, ?, ?, ?)',
              (user_id, title, description, due_date))
    db.commit()
    reminder_id = c.lastrowid
    return jsonify({'id': reminder_id, 'message': 'Reminder added successfully'}), 201

@bp.route('/<int:reminder_id>', methods=['PUT'])
@login_required
def update_reminder(reminder_id):
    user_id = session['user_id']
    data = request.json
    title = data.get('title')
    description = data.get('description', '')
    due_date = data.get('due_date')
    is_completed = data.get('is_completed')
    
    db = get_db()
    c = db.cursor()
    
    if is_completed is not None:
        c.execute('UPDATE reminders SET is_completed = ? WHERE id = ? AND user_id = ?',
                  (is_completed, reminder_id, user_id))
    else:
        c.execute('''UPDATE reminders 
                     SET title = ?, description = ?, due_date = ?
                     WHERE id = ? AND user_id = ?''',
                  (title, description, due_date, reminder_id, user_id))
    
    db.commit()
    return jsonify({'message': 'Reminder updated successfully'})

@bp.route('/<int:reminder_id>', methods=['DELETE'])
@login_required
def delete_reminder(reminder_id):
    user_id = session['user_id']
    db = get_db()
    c = db.cursor()
    c.execute('DELETE FROM reminders WHERE id = ? AND user_id = ?', (reminder_id, user_id))
    db.commit()
    return jsonify({'message': 'Reminder deleted successfully'})
