from flask import session
import random
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from extensions import db
from models.attempt import AttemptModel
from models.exam import ExamModel
from models.question import QuestionModel
from models.answer import StudentAnswerModel
 
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


def start_student_attempt(quiz_code, form_data, ip_address):

    exam = ExamModel.query.with_entities(
        ExamModel.id,
        ExamModel.school_id,
        ExamModel.max_attempts_per_mobile
    ).filter(
        ExamModel.quiz_code == quiz_code
    ).first()

    if not exam:
        return False, "Invalid quiz link"

    exam_id = exam.id
    school_id = exam.school_id
    max_attempts = exam.max_attempts_per_mobile

    mobile = form_data.get("mobile")

    # count attempts
    attempts = db.session.query(func.count(AttemptModel.id))\
        .filter(
            AttemptModel.exam_id == exam_id,
            AttemptModel.mobile == mobile
        ).scalar()

    if attempts >= max_attempts:
        return False, "Maximum attempts reached"

    attempt_number = attempts + 1

    new_attempt = AttemptModel(
        exam_id=exam_id,
        school_id=school_id,
        first_name=form_data.get("first_name"),
        last_name=form_data.get("last_name"),
        student_class=form_data.get("class_name"),
        roll_number=form_data.get("roll_number"),
        mobile=mobile,
        ip_address=ip_address,
        start_time=datetime.utcnow(),
        attempt_number=attempt_number
    )

    db.session.add(new_attempt)
    db.session.commit()

    return True, new_attempt.id
# -------------------------------
# Get Question by Index
# -------------------------------
 
def get_question_for_attempt(attempt_id, q_index):

    attempt = AttemptModel.query.get(attempt_id)
    if not attempt:
        return None

    exam_id = attempt.exam_id

    question = QuestionModel.query\
        .filter_by(exam_id=exam_id)\
        .order_by(QuestionModel.id.asc())\
        .offset(q_index)\
        .limit(1)\
        .first()

    if not question:
        return None

    answer = StudentAnswerModel.query.filter_by(
        attempt_id=attempt_id,
        question_id=question.id
    ).first()

    selected_option = answer.selected_option if answer else None

    session_key = f"question_{question.id}_options"

    if session_key in session:
        options = session[session_key]
    else:
        options = [
            ("A", question.option_a),
            ("B", question.option_b),
            ("C", question.option_c),
            ("D", question.option_d)
        ]
        random.shuffle(options)
        session[session_key] = options

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

    exam_id = attempt.exam_id

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

    rows = db.session.query(
        QuestionModel.id,
        StudentAnswerModel.selected_option
    ).outerjoin(
        StudentAnswerModel,
        (QuestionModel.id == StudentAnswerModel.question_id) &
        (StudentAnswerModel.attempt_id == attempt_id)
    ).filter(
        QuestionModel.exam_id == exam_id
    ).order_by(
        QuestionModel.id
    ).all()

    palette = []

    for index, row in enumerate(rows):
        palette.append({
            "index": index,
            "answered": 1 if row.selected_option else 0
        })

    return palette