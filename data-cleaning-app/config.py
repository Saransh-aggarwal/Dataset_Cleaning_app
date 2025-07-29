import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a-very-secure-and-decentralized-secret-key')
    
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_FILE_DIR = os.path.join(basedir, 'flask_session')
    
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads/')
    CLEANED_FOLDER = os.path.join(basedir, 'cleaned_data/')
    ALLOWED_EXTENSIONS = {'csv', 'xlsx'}