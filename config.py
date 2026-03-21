import os

class Config:
    SECRET_KEY = "super-secret-key"
    DATABASE = "exam.db"
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")