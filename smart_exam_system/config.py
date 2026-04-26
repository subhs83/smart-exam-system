import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key")

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # 🔥 FORCE DATABASE URL CLEANLY
    database_url = os.environ.get("DATABASE_URL")

    # Fix Render postgres issue
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url or "sqlite:///" + os.path.join(BASE_DIR, "exam.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")