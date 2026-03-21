from flask import session
from datetime import datetime, timezone, timedelta
from database import get_db


# -------------------------------
# Get Exam by Quiz Code
# -------------------------------
def get_exam_by_quiz_code(quiz_code):

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id, 
        school_id,
        duration_minutes,
        marks_per_question,
        negative_marks, 
        max_attempts_per_mobile
        FROM exams
        WHERE quiz_code=?
    """, (quiz_code,))

    exam = cursor.fetchone()

    return exam


# -------------------------------
# Start Student Attempt
# -------------------------------



def start_student_attempt(quiz_code, form_data, ip_address):
    db = get_db()
    cursor = db.cursor()

    # Get exam
    cursor.execute("""
        SELECT id, school_id, max_attempts_per_mobile
        FROM exams
        WHERE quiz_code=?
    """, (quiz_code,))
    exam = cursor.fetchone()
    if not exam:
        return False, "Invalid quiz link"

    exam_id = exam["id"]
    school_id = exam["school_id"]
    max_attempts = exam["max_attempts_per_mobile"]

    # Extract student info from form
    first_name = form_data.get("first_name")
    last_name = form_data.get("last_name")
    student_class = form_data.get("class_name")
    roll_number = form_data.get("roll_number")
    mobile = form_data.get("mobile")

    # Validate max attempts
    cursor.execute("""
        SELECT COUNT(*) as attempts
        FROM student_attempts
        WHERE exam_id=? AND mobile=?
    """, (exam_id, mobile))
    attempts = cursor.fetchone()["attempts"]

    if attempts >= max_attempts:
        return False, "Maximum attempts reached"

    # Determine attempt number
    attempt_number = attempts + 1

    # Store start_time in UTC
    start_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # Insert attempt
    cursor.execute("""
        INSERT INTO student_attempts
        (exam_id, school_id, first_name, last_name, student_class, roll_number,
         mobile, ip_address, start_time, attempt_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        exam_id,
        school_id,
        first_name,
        last_name,
        student_class,
        roll_number,
        mobile,
        ip_address,
        start_time,
        attempt_number
    ))
    db.commit()

    attempt_id = cursor.lastrowid
    return True, attempt_id
# -------------------------------
# Get Question by Index
# -------------------------------
def get_question_for_attempt(attempt_id, q_index):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT exam_id FROM student_attempts WHERE id=?", (attempt_id,))
    attempt = cursor.fetchone()
    if not attempt:
        return None
    exam_id = attempt["exam_id"]

    # get question
    cursor.execute("""
        SELECT id, question_text, option_a, option_b, option_c, option_d, correct_option
        FROM questions
        WHERE exam_id=?
        ORDER BY id ASC
        LIMIT 1 OFFSET ?
    """, (exam_id, q_index))
    question = cursor.fetchone()
    if not question:
        return None

    # get selected option
    cursor.execute("""
        SELECT selected_option
        FROM student_answers
        WHERE attempt_id=? AND question_id=?
    """, (attempt_id, question["id"]))
    answer = cursor.fetchone()
    selected_option = answer["selected_option"] if answer else None

    # shuffle options once using session
    session_key = f"question_{question['id']}_options"
    if session_key in session:
        options = session[session_key]
    else:
        options = [
            ("A", question["option_a"]),
            ("B", question["option_b"]),
            ("C", question["option_c"]),
            ("D", question["option_d"])
        ]
        import random
        random.shuffle(options)
        session[session_key] = options

    return {
        "question_id": question["id"],
        "question_text": question["question_text"],
        "options": options,
        "correct_option": question["correct_option"],
        "selected_option": selected_option
    }

# -------------------------------
# Save Answer
# -------------------------------
def save_student_answer(attempt_id, question_id, selected_option):
    db = get_db()
    cursor = db.cursor()

    # check if answer exists
    cursor.execute("""
        SELECT id FROM student_answers
        WHERE attempt_id=? AND question_id=?
    """, (attempt_id, question_id))

    exists = cursor.fetchone()

    # is correct?
    cursor.execute("SELECT correct_option FROM questions WHERE id=?", (question_id,))
    correct_option = cursor.fetchone()["correct_option"]
    is_correct = 1 if selected_option == correct_option else 0

    if exists:
        # update existing
        cursor.execute("""
            UPDATE student_answers
            SET selected_option=?, is_correct=?, answered_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (selected_option, is_correct, exists["id"]))
    else:
        # insert new
        cursor.execute("""
            INSERT INTO student_answers
            (attempt_id, question_id, selected_option, is_correct)
            VALUES (?, ?, ?, ?)
        """, (attempt_id, question_id, selected_option, is_correct))

    db.commit()


# ----------------------------------
# Get exam end timestamp
# ----------------------------------
def get_exam_end_timestamp(attempt_id):

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT start_time, exam_id
        FROM student_attempts
        WHERE id=?
    """, (attempt_id,))
    attempt = cursor.fetchone()

    cursor.execute("""
        SELECT duration_minutes
        FROM exams
        WHERE id=?
    """, (attempt["exam_id"],))
    exam = cursor.fetchone()

    start_time = datetime.fromisoformat(attempt["start_time"])
    start_time = start_time.replace(tzinfo=timezone.utc)

    end_time = start_time + timedelta(minutes=exam["duration_minutes"])

    return int(end_time.timestamp()), end_time


# ----------------------------------
# Check if exam expired
# ----------------------------------
def is_exam_expired(end_time):

    now = datetime.now(timezone.utc)
    return now >= end_time


# ----------------------------------
# Get total questions in exam
# ----------------------------------
def get_total_questions(exam_id):

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT COUNT(*) as total
        FROM questions
        WHERE exam_id=?
    """, (exam_id,))

    return cursor.fetchone()["total"]


# ----------------------------------
# Get student score
# ----------------------------------
def get_student_score(attempt_id):

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT COUNT(*) as score
        FROM student_answers
        WHERE attempt_id=? AND is_correct=1
    """, (attempt_id,))

    return cursor.fetchone()["score"]
# ----------------------------------
# Get student Results
# ----------------------------------
def get_student_result(attempt_id):

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT exam_id FROM student_attempts WHERE id=?",
        (attempt_id,)
    )

    exam_id = cursor.fetchone()["exam_id"]

    total = get_total_questions(exam_id)
    score = get_student_score(attempt_id)

    percentage = finalize_attempt(attempt_id, score, total)

    correct_answers = score
    wrong_answers = total - score

    return {
        "score": score,
        "total": total,
        "percentage": percentage,
        "correct_answers": correct_answers,
        "wrong_answers": wrong_answers
    }
# ----------------------------------
# Finalize attempt (update DB)
# ----------------------------------
def finalize_attempt(attempt_id, score, total):

    db = get_db()
    cursor = db.cursor()

    percentage = (score / total * 100) if total else 0

    cursor.execute("""
        UPDATE student_attempts
        SET score=?, total_marks=?, percentage=?, end_time=CURRENT_TIMESTAMP
        WHERE id=?
    """, (score, total, percentage, attempt_id))

    db.commit()

    return percentage
#---------------------
#Question Palette
#-------------------
def get_question_palette(attempt_id, exam_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT q.id,
               CASE WHEN sa.selected_option IS NOT NULL THEN 1 ELSE 0 END as answered
        FROM questions q
        LEFT JOIN student_answers sa
            ON q.id = sa.question_id AND sa.attempt_id = ?
        WHERE q.exam_id = ?
        ORDER BY q.id
    """, (attempt_id, exam_id))

    rows = cursor.fetchall()

    palette = []
    for index, row in enumerate(rows):
        palette.append({
            "index": index,
            "answered": row["answered"]
        })

    return palette