import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key")

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    DATABASE_URL = os.getenv("DATABASE_URL")

    # Fix for Render (VERY IMPORTANT)
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # ✅ Use Postgres if available, else fallback to SQLite (for local)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or "sqlite:///" + os.path.join(BASE_DIR, "exam.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")