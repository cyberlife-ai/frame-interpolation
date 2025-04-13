from flask import Flask
from flask_cors import CORS

def create_app():
    """Initialize the Flask app."""
    app = Flask(__name__)
    CORS(app)

    # Register routes
    from app.routes import film_routes
    app.register_blueprint(film_routes)

    return app