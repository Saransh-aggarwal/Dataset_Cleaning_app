import os
from flask import Flask
from flask_session import Session
from config import Config

sess = Session()

def create_app(config_class=Config):
    
    app = Flask(__name__)
    app.config.from_object(config_class)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['CLEANED_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)


    sess.init_app(app)

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app