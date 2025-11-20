import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Use os.environ.get for configuration to support production environments
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=debug_mode, port=port)
