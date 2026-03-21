import sqlite3
from config import Config


def get_db():
    conn = sqlite3.connect(Config.DATABASE, timeout=30)
    conn.row_factory = sqlite3.Row
    # Enable Foreign Keys
    conn.execute("PRAGMA foreign_keys = ON")   # 👈 MOVE IT HERE
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # =========================
    # SCHOOLS TABLE
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schools (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        address TEXT,
        phone TEXT,
        email TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # =========================
    # USERS TABLE
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        school_id INTEGER,
        is_active INTEGER DEFAULT 1,
        force_password_change INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (school_id) REFERENCES schools(id)
    )
    """)

    # =========================
    # EXAMS TABLE (UPGRADED)
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        duration_minutes INTEGER NOT NULL,

        marks_per_question INTEGER DEFAULT 1,
        negative_marks REAL DEFAULT 0,
        max_attempts_per_mobile INTEGER DEFAULT 1,

        status TEXT DEFAULT 'draft',  -- draft / published / closed

        school_id INTEGER NOT NULL,
        teacher_id INTEGER NOT NULL,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        published_at TIMESTAMP,

        FOREIGN KEY (teacher_id) REFERENCES users(id),
        FOREIGN KEY (school_id) REFERENCES schools(id)
    )
    """)

    # =========================
# QUESTIONS TABLE
# =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_id INTEGER NOT NULL,

        question_text TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        correct_option TEXT NOT NULL,

        marks INTEGER DEFAULT 1,
        negative_marks INTEGER DEFAULT 0,

        ai_generated INTEGER DEFAULT 0,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (exam_id) REFERENCES exams(id)
    )
    """)

    # =========================
    # STUDENT ATTEMPTS TABLE (REPLACES RESULTS)
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_id INTEGER NOT NULL,
        school_id INTEGER NOT NULL,

        first_name TEXT,
        last_name TEXT,
        student_class TEXT,
        roll_number TEXT,
        mobile TEXT,

        ip_address TEXT,

        start_time TIMESTAMP,
        end_time TIMESTAMP,

        score REAL,
        total_marks REAL,
        percentage REAL,

        attempt_number INTEGER,

        FOREIGN KEY (exam_id) REFERENCES exams(id),
        FOREIGN KEY (school_id) REFERENCES schools(id)
    )
    """)
    # =========================
    # Student Answer
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attempt_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        selected_option TEXT,
        is_correct INTEGER,
        answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (attempt_id) REFERENCES student_attempts(id),
        FOREIGN KEY (question_id) REFERENCES questions(id)
    );
     """)

    # =========================
    # DEFAULT SUPER ADMIN
    # =========================
    cursor.execute("SELECT * FROM users WHERE role = 'super_admin'")
    admin_exists = cursor.fetchone()
    from utils.security import hash_password
    if not admin_exists:
        password = hash_password("admin123")

        cursor.execute("""
            INSERT INTO users (name, email, password, role)
            VALUES (?, ?, ?, ?)
        """, ("Super Admin", "admin@system.com", password, "super_admin"))

    conn.commit()
    conn.close()