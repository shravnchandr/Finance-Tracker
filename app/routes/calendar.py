from flask import Blueprint, request, jsonify, session
from app.db import get_db
from app.utils import login_required

bp = Blueprint('calendar', __name__, url_prefix='/api/calendar')

@bp.route('/events', methods=['GET'])
@login_required
def get_calendar_events():
    user_id = session['user_id']
    db = get_db()
    c = db.cursor()
    
    # 1. Fetch Calendar Events
    c.execute('SELECT id, title, description, CAST(start_time AS TEXT) as start_time, CAST(end_time AS TEXT) as end_time, color, "event" as type FROM calendar_events WHERE user_id = ?', (user_id,))
    events = [dict(row) for row in c.fetchall()]
    
    # 2. Fetch Reminders (map to events)
    c.execute('SELECT id, title, description, CAST(due_date AS TEXT) as start_time, is_completed, "reminder" as type FROM reminders WHERE user_id = ? AND due_date IS NOT NULL', (user_id,))
    reminders = [dict(row) for row in c.fetchall()]
    for rem in reminders:
        rem['color'] = '#10b981' if rem['is_completed'] else '#ef4444' # Green if done, Red if pending
        rem['description'] = f"Reminder: {rem['description'] or ''}"
    
    # 3. Fetch Notes (map to events based on created_at)
    c.execute('SELECT id, title, content as description, CAST(created_at AS TEXT) as start_time, color, "note" as type FROM notes WHERE user_id = ?', (user_id,))
    notes = [dict(row) for row in c.fetchall()]
    for note in notes:
        note['description'] = f"Note: {note['description'][:50]}..." if note['description'] else "Note"
    
    # Combine all
    all_events = events + reminders + notes
    return jsonify(all_events)

@bp.route('/events', methods=['POST'])
@login_required
def add_calendar_event():
    user_id = session['user_id']
    data = request.json
    title = data.get('title')
    description = data.get('description', '')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    color = data.get('color', '#3b82f6')
    
    if not title or not start_time:
        return jsonify({'error': 'Title and start time are required'}), 400
        
    db = get_db()
    c = db.cursor()
    c.execute('''INSERT INTO calendar_events 
                 (user_id, title, description, start_time, end_time, color) 
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (user_id, title, description, start_time, end_time, color))
    db.commit()
    event_id = c.lastrowid
    return jsonify({'id': event_id, 'message': 'Event added successfully'}), 201

@bp.route('/events/<int:event_id>', methods=['PUT'])
@login_required
def update_calendar_event(event_id):
    user_id = session['user_id']
    data = request.json
    title = data.get('title')
    description = data.get('description', '')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    color = data.get('color', '#3b82f6')
    
    db = get_db()
    c = db.cursor()
    c.execute('''UPDATE calendar_events 
                 SET title = ?, description = ?, start_time = ?, end_time = ?, color = ?
                 WHERE id = ? AND user_id = ?''',
              (title, description, start_time, end_time, color, event_id, user_id))
    db.commit()
    return jsonify({'message': 'Event updated successfully'})

@bp.route('/events/<int:event_id>', methods=['DELETE'])
@login_required
def delete_calendar_event(event_id):
    user_id = session['user_id']
    db = get_db()
    c = db.cursor()
    c.execute('DELETE FROM calendar_events WHERE id = ? AND user_id = ?', (event_id, user_id))
    db.commit()
    return jsonify({'message': 'Event deleted successfully'})
