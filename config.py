import os

class Config:
    SECRET_KEY = "super-secret-key"
    
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Old system (keep for now)
    DATABASE = "exam.db"
    
    # New SQLAlchemy config
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "exam.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")