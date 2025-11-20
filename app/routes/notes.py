from flask import Blueprint, request, jsonify, session
from app.db import get_db
from app.utils import login_required

bp = Blueprint('notes', __name__, url_prefix='/api/notes')

@bp.route('', methods=['GET'])
@login_required
def get_notes():
    user_id = session['user_id']
    db = get_db()
    c = db.cursor()
    c.execute('SELECT id, user_id, title, content, color, CAST(created_at AS TEXT) as created_at, CAST(updated_at AS TEXT) as updated_at FROM notes WHERE user_id = ? ORDER BY updated_at DESC', (user_id,))
    notes = [dict(row) for row in c.fetchall()]
    return jsonify(notes)

@bp.route('', methods=['POST'])
@login_required
def add_note():
    user_id = session['user_id']
    data = request.json
    title = data.get('title')
    content = data.get('content', '')
    color = data.get('color', '#ffffff')
    
    if not title:
        return jsonify({'error': 'Title is required'}), 400
        
    db = get_db()
    c = db.cursor()
    c.execute('INSERT INTO notes (user_id, title, content, color) VALUES (?, ?, ?, ?)',
              (user_id, title, content, color))
    db.commit()
    note_id = c.lastrowid
    return jsonify({'id': note_id, 'message': 'Note added successfully'}), 201

@bp.route('/<int:note_id>', methods=['PUT'])
@login_required
def update_note(note_id):
    user_id = session['user_id']
    data = request.json
    title = data.get('title')
    content = data.get('content', '')
    color = data.get('color', '#ffffff')
    
    db = get_db()
    c = db.cursor()
    c.execute('''UPDATE notes 
                 SET title = ?, content = ?, color = ?, updated_at = CURRENT_TIMESTAMP 
                 WHERE id = ? AND user_id = ?''',
              (title, content, color, note_id, user_id))
    db.commit()
    return jsonify({'message': 'Note updated successfully'})

@bp.route('/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    user_id = session['user_id']
    db = get_db()
    c = db.cursor()
    c.execute('DELETE FROM notes WHERE id = ? AND user_id = ?', (note_id, user_id))
    db.commit()
    return jsonify({'message': 'Note deleted successfully'})
