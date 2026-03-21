import random
import string
from database import get_db


# -------------------------------
# Create Exam
# -------------------------------
def create_exam(teacher_id, school_id, title, duration, marks, negative, max_attempts):
    """
    Inserts a new exam into the database.
    Default status = draft (handled by DB)
    Returns (success: bool, message: str)
    """
    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO exams (
                title,
                duration_minutes,
                marks_per_question,
                negative_marks,
                max_attempts_per_mobile,
                school_id,
                teacher_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            duration,
            marks,
            negative,
            max_attempts,
            school_id,
            teacher_id
        ))

        db.commit()
        return True, "Exam created successfully (Draft mode)"

    except Exception as e:
        return False, f"Error creating exam: {str(e)}"


# -------------------------------
# Get all exams for a teacher
# -------------------------------

def get_teacher_exams(teacher_id):
    """
    Returns all exams created by the teacher
    including:
    - total_questions
    - total_attempts
    """

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT 
            e.id,
            e.title,
            e.duration_minutes,
            e.status,
            e.quiz_code,
            e.created_at,

            COUNT(DISTINCT q.id) AS total_questions,
            COUNT(DISTINCT a.id) AS total_attempts

        FROM exams e

        LEFT JOIN questions q
            ON q.exam_id = e.id

        LEFT JOIN student_attempts a
            ON a.exam_id = e.id

        WHERE e.teacher_id = ?

        GROUP BY e.id
        ORDER BY e.created_at DESC
    """, (teacher_id,))

    exams = cursor.fetchall()

    return exams


# -------------------------------
# Publish Exam
# -------------------------------
def generate_quiz_code(length=8):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def publish_exam(exam_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM questions WHERE exam_id=?", (exam_id,))
    q_count = cursor.fetchone()[0]

    if q_count == 0:
        return False, "Cannot publish exam without questions"

    quiz_code = generate_quiz_code()

    cursor.execute("""
        UPDATE exams
        SET status='published',
            published_at=CURRENT_TIMESTAMP,
            quiz_code=?
        WHERE id=?
    """, (quiz_code, exam_id))

    db.commit()

    return True, quiz_code


# -------------------------------
# Delete Exam (only if no attempts)
# -------------------------------
def delete_exam(exam_id):
    from database import get_db

    db = get_db()
    cursor = db.cursor()

    # 1️⃣ Check if student attempts exist
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM student_attempts
        WHERE exam_id = ?
    """, (exam_id,))
    attempt_count = cursor.fetchone()["total"]

    if attempt_count > 0:
        return False, "Cannot delete exam with student attempts."

    # 2️⃣ Delete related questions first
    cursor.execute("""
        DELETE FROM questions
        WHERE exam_id = ?
    """, (exam_id,))

    # 3️⃣ Now delete exam
    cursor.execute("""
        DELETE FROM exams
        WHERE id = ?
    """, (exam_id,))

    db.commit()

    return True, "Exam deleted successfully."