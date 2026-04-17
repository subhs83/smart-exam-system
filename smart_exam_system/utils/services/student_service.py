from flask import session
import random
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from smart_exam_system.extensions import db
from smart_exam_system.models.attempt import AttemptModel
from smart_exam_system.models.exam import ExamModel
from smart_exam_system.models.question import QuestionModel
from smart_exam_system.models.answer import StudentAnswerModel
import json
 
# -------------------------------
# Get Exam by Quiz Code
# -------------------------------

def get_exam_by_quiz_code(quiz_code):

    return ExamModel.query.with_entities(
        ExamModel.id,
        ExamModel.school_id,
        ExamModel.duration_minutes,
        ExamModel.marks_per_question,
        ExamModel.negative_marks,
        ExamModel.max_attempts_per_mobile
    ).filter(
        ExamModel.quiz_code == quiz_code
    ).first()

# -------------------------------
# Start Student Attempt
# -------------------------------


def start_student_attempt(exam_id, school_id, form_data, ip_address):
    import json
    from datetime import datetime

    # -------------------------------
    # Extract student data
    # -------------------------------
    first_name = form_data.get("first_name")
    last_name = form_data.get("last_name")
    student_class = form_data.get("class_name")
    roll_number = form_data.get("roll_number")
    mobile = form_data.get("mobile")

    # -------------------------------
    # Check attempt limit (by mobile)
    # -------------------------------
    previous_attempts = AttemptModel.query.filter_by(
        exam_id=exam_id,
        mobile=mobile
    ).count()

    exam = ExamModel.query.get(exam_id)

    if exam.max_attempts_per_mobile and previous_attempts >= exam.max_attempts_per_mobile:
        return None, "Maximum attempts reached"

    attempt_number = previous_attempts + 1

    # -------------------------------
    # Get all questions
    # -------------------------------
    questions = QuestionModel.query.filter_by(exam_id=exam_id).all()

    if not questions:
        return None, "No questions available"

    # -------------------------------
    # Question Order
    # -------------------------------
    question_ids = [q.id for q in questions]
    random.shuffle(question_ids)
    question_order = json.dumps(question_ids)

    # -------------------------------
    # Option Order
    # -------------------------------
    option_order_map = {}

    for q in questions:
        options = ["A", "B", "C", "D"]
        random.shuffle(options)
        option_order_map[str(q.id)] = options

    option_order = json.dumps(option_order_map)

    # -------------------------------
    # Create Attempt
    # -------------------------------
    new_attempt = AttemptModel(
        exam_id=exam_id,
        school_id=school_id,
        first_name=first_name,
        last_name=last_name,
        student_class=student_class,
        roll_number=roll_number,
        mobile=mobile,
        ip_address=ip_address,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow(),  # will update later
        attempt_number=attempt_number,
        question_order=question_order,
        option_order=option_order
    )

    db.session.add(new_attempt)
    db.session.commit()

    return new_attempt, None
# -------------------------------
# Get Question by Index
# -------------------------------
 
def get_question_for_attempt(attempt_id, q_index):
    import json

    attempt = AttemptModel.query.get(attempt_id)
    if not attempt or not attempt.question_order or not attempt.option_order:
        return None

    question_order = json.loads(attempt.question_order)
    option_order_map = json.loads(attempt.option_order)

    # Safety
    if q_index < 0 or q_index >= len(question_order):
        return None

    question_id = question_order[q_index]
    question = QuestionModel.query.get(question_id)

    if not question:
        return None

    # Get saved answer
    answer = StudentAnswerModel.query.filter_by(
        attempt_id=attempt_id,
        question_id=question_id
    ).first()

    selected_option = answer.selected_option if answer else None

    # -------------------------------
    # Apply OPTION ORDER
    # -------------------------------
    order = option_order_map.get(str(question_id), ["A", "B", "C", "D"])

    option_text_map = {
        "A": question.option_a,
        "B": question.option_b,
        "C": question.option_c,
        "D": question.option_d
    }

    options = [(opt, option_text_map[opt]) for opt in order]

    return {
        "question_id": question.id,
        "question_text": question.question_text,
        "options": options,
        "correct_option": question.correct_option,
        "selected_option": selected_option
    }
# -------------------------------
# Save Answer
# -------------------------------
 
def save_student_answer(attempt_id, question_id, selected_option):

    attempt = AttemptModel.query.get(attempt_id)
    if not attempt:
        return

    # -------------------------------
    # 🔒 Prevent saving after submission
    # -------------------------------
    if attempt.is_submitted:
        return

    # -------------------------------
    # ⏱️ Enforce time expiry (BACKEND)
    # -------------------------------
    exam = ExamModel.query.get(attempt.exam_id)
    end_time = attempt.start_time + timedelta(minutes=exam.duration_minutes)

    if datetime.utcnow() > end_time:
        return  # Block saving after time ends

    # -------------------------------
    # ✅ Validate question belongs to attempt
    # -------------------------------
    question_order = json.loads(attempt.question_order or "[]")
    if int(question_id) not in question_order:
        return  # Invalid request

    # -------------------------------
    # Save / Update Answer
    # -------------------------------
    answer = StudentAnswerModel.query.filter_by(
        attempt_id=attempt_id,
        question_id=question_id
    ).first()

    correct_option = QuestionModel.query.with_entities(
        QuestionModel.correct_option
    ).filter_by(id=question_id).scalar()

    is_correct = 1 if selected_option == correct_option else 0

    if answer:
        answer.selected_option = selected_option
        answer.is_correct = is_correct
    else:
        new_answer = StudentAnswerModel(
            attempt_id=attempt_id,
            question_id=question_id,
            selected_option=selected_option,
            is_correct=is_correct
        )
        db.session.add(new_answer)

    db.session.commit()


# ----------------------------------
# Get exam end timestamp
# ----------------------------------
def get_exam_end_timestamp(attempt_id):
    attempt = AttemptModel.query.get(attempt_id)
    if not attempt:
        return None, None

    exam = ExamModel.query.get(attempt.exam_id)
    if not exam:
        return None, None

    start_time = attempt.start_time

    # If start_time is string (legacy data), parse it
    if isinstance(start_time, str):
        try:
            start_time = datetime.fromisoformat(start_time)
        except ValueError:
            # fallback for older format: "YYYY-MM-DD HH:MM:SS"
            start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    
    # Make sure it's timezone aware (UTC)
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)

    end_time = start_time + timedelta(minutes=exam.duration_minutes)

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

    return db.session.query(func.count(QuestionModel.id))\
        .filter(QuestionModel.exam_id == exam_id)\
        .scalar()


# ----------------------------------
# Get student score
# ----------------------------------


def get_student_score(attempt_id):

    return db.session.query(func.count(StudentAnswerModel.id))\
        .filter(
            StudentAnswerModel.attempt_id == attempt_id,
            StudentAnswerModel.is_correct == 1
        ).scalar()
# ----------------------------------
# Get student Results
# ----------------------------------


def get_student_result(attempt_id):

    attempt = AttemptModel.query.get(attempt_id)

    if not attempt:
        return None

    exam = attempt.exam

    total = get_total_questions(exam.id)
    score = get_student_score(attempt_id)

    # ⏱️ TIME CHECK
    end_time = attempt.start_time + timedelta(minutes=exam.duration_minutes)
    is_time_up = datetime.utcnow() > end_time

    # ✅ HANDLE SUBMISSION (BOTH CASES)
    if not attempt.is_submitted:

        percentage = (score / total) * 100 if total > 0 else 0

        attempt.score = score
        attempt.total_marks = total
        attempt.percentage = percentage
        attempt.is_submitted = True
        attempt.end_time = datetime.utcnow()

        db.session.commit()

    else:
        percentage = attempt.percentage or 0

    # 📊 STATS
    correct_answers = score
    wrong_answers = total - score

    return {
        "score": score,
        "total": total,
        "percentage": percentage,
        "correct_answers": correct_answers,
        "wrong_answers": wrong_answers,

        "student_name": f"{attempt.first_name} {attempt.last_name}",
        "student_class": attempt.student_class,
        "roll_number": attempt.roll_number,

        "exam": exam
    }
# ----------------------------------
# Finalize attempt (update DB)
# ----------------------------------

def finalize_attempt(attempt_id, score, total):

    attempt = AttemptModel.query.get(attempt_id)

    percentage = (score / total * 100) if total else 0

    attempt.score = score
    attempt.total_marks = total
    attempt.percentage = percentage
    attempt.end_time = datetime.utcnow()

    db.session.commit()

    return percentage
#---------------------
#Question Palette
#-------------------


def get_question_palette(attempt_id, exam_id):
    import json

    attempt = AttemptModel.query.get(attempt_id)
    if not attempt or not attempt.question_order:
        return []

    order = json.loads(attempt.question_order)

    palette = []

    for index, q_id in enumerate(order):
        answer = StudentAnswerModel.query.filter_by(
            attempt_id=attempt_id,
            question_id=q_id
        ).first()

        palette.append({
            "index": index,
            "answered": 1 if answer and answer.selected_option else 0
        })

    return palette