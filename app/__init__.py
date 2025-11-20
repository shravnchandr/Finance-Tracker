import os
import datetime as dt
from flask import Flask
from dotenv import load_dotenv

def create_app(test_config=None):
    # Load variables from .env
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)
    
    # Configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('FLASK_SECRET_KEY', 'dev'),
        DATABASE=os.path.join(app.instance_path, 'expenses.db'),
        PERMANENT_SESSION_LIFETIME=dt.timedelta(minutes=15)
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Upload folder setup
    # We want uploads to be in the project root, not inside app/
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_FOLDER = os.path.join(base_dir, 'uploads')
    
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

    # Initialize extensions
    from . import db
    db.init_app(app)

    # Register blueprints
    from .routes import auth, main, transactions, categories, notes, reminders, calendar
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(transactions.bp)
    app.register_blueprint(categories.bp)
    app.register_blueprint(notes.bp)
    app.register_blueprint(reminders.bp)
    app.register_blueprint(calendar.bp)

    return app
