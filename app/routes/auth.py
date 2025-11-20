import os
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import get_db

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        reg_key = data.get('registration_key')
        
        if not username or not password or not reg_key:
            return jsonify({'error': 'All fields are required'}), 400
        
        # Check registration key and determine role
        ADMIN_KEY = os.environ.get('ADMIN_KEY')
        USER_KEY = os.environ.get('USER_KEY')
        
        if reg_key == ADMIN_KEY:
            role = 'admin'
        elif reg_key == USER_KEY:
            role = 'user'
        else:
            return jsonify({'error': 'Invalid registration key'}), 400
        
        db = get_db()
        c = db.cursor()
        
        # Check if user exists
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        if c.fetchone():
            return jsonify({'error': 'Username already exists'}), 400
        
        # Create user
        hashed_password = generate_password_hash(password)
        c.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                  (username, hashed_password, role))
        db.commit()
        user_id = c.lastrowid
        
        session['user_id'] = user_id
        session['username'] = username
        session['role'] = role
        
        return jsonify({'message': 'Registration successful', 'redirect': '/'}), 201
    
    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        db = get_db()
        c = db.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return jsonify({'message': 'Login successful', 'redirect': '/'}), 200
        
        return jsonify({'error': 'Invalid credentials'}), 401
    
    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
