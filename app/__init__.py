from flask import Flask
from flask_cors import CORS
from .routes import main as main_blueprint

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = 'app/static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
    CORS(app)

    app.register_blueprint(main_blueprint)

    return app
