import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key")
   # SECRET_KEY = "super-secret-key"
    
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # SQLite database
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "exam.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    

    # Optional: directory for uploads, logs, etc.
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")