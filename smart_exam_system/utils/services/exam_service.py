import random
import string
from smart_exam_system.extensions import db
from sqlalchemy import func
from smart_exam_system.models.exam import ExamModel
from smart_exam_system.models.question import QuestionModel
from smart_exam_system.models.attempt import AttemptModel
from smart_exam_system.utils.helpers import apply_exam_status
from datetime import datetime, timezone


# -------------------------------
# Create Exam
# -------------------------------


def create_exam(
    teacher_id, 
    school_id, 
    title, 
    duration, 
    marks, 
    negative, 
    max_attempts, 
    start_date,
    end_date):
    try:
        if duration <= 0:
            return False, "Duration must be greater than 0."

        if marks <= 0:
            return False, "Marks per question must be greater than 0."

        if negative < 0:
            return False, "Negative marks cannot be negative."

        if max_attempts <= 0:
            return False, "Max attempts must be at least 1."
        exam = ExamModel(
            title=title,
            duration_minutes=duration,
            marks_per_question=marks,
            negative_marks=negative,
            max_attempts_per_student=max_attempts,
            school_id=school_id,
            teacher_id=teacher_id,
            start_date=start_date,
            end_date=end_date
        )

        db.session.add(exam)
        db.session.commit()

        return True, "Exam created successfully (Draft mode)"

    except Exception as e:
        db.session.rollback()
        return False, f"Error creating exam: {str(e)}"


# -------------------------------
# Get all exams for a teacher
# -------------------------------

def get_teacher_exams(teacher_id):
    
    exams = db.session.query(
        ExamModel.id,
        ExamModel.title,
        ExamModel.duration_minutes,
        ExamModel.status,
        ExamModel.quiz_code,
        ExamModel.max_attempts_per_student,
        ExamModel.created_at,
        ExamModel.end_date,   # ⚠️ make sure included if used

        func.count(func.distinct(QuestionModel.id)).label("total_questions"),
        func.count(func.distinct(AttemptModel.id)).label("total_attempts")

    ).outerjoin(
        QuestionModel, QuestionModel.exam_id == ExamModel.id
    ).outerjoin(
        AttemptModel, AttemptModel.exam_id == ExamModel.id
    ).filter(
        ExamModel.teacher_id == teacher_id
    ).group_by(
        ExamModel.id
    ).order_by(
        ExamModel.created_at.desc()
    ).all()

    result = []

    for e in exams:
        exam = dict(e._mapping)
        result.append(apply_exam_status(exam))

    return result

# -------------------------------
# Publish Exam
# -------------------------------
def generate_quiz_code(length=8):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_unique_quiz_code():

    while True:

        quiz_code = generate_quiz_code()

        exists = ExamModel.query.filter_by(
            quiz_code=quiz_code
        ).first()

        if not exists:
            return quiz_code

def publish_exam(exam_id):

    q_count = db.session.query(func.count(QuestionModel.id))\
        .filter(QuestionModel.exam_id == exam_id)\
        .scalar()

    if q_count == 0:
        return False, "Cannot publish exam without questions"

    quiz_code = generate_unique_quiz_code()

    exam = ExamModel.query.get(exam_id)

    exam.status = "published"
    exam.quiz_code = quiz_code
    exam.published_at = db.func.current_timestamp()

    db.session.commit()

    return True, quiz_code

# -------------------------------
# Delete Exam (only if no attempts)
# -------------------------------

def delete_exam(exam_id):

    attempt_count = db.session.query(func.count(AttemptModel.id))\
        .filter(AttemptModel.exam_id == exam_id)\
        .scalar()

    if attempt_count > 0:
        return False, "Cannot delete exam with student attempts."

    # delete questions
    try:

        QuestionModel.query.filter_by(
            exam_id=exam_id
        ).delete(synchronize_session=False)

        ExamModel.query.filter_by(
            id=exam_id
        ).delete(synchronize_session=False)

        db.session.commit()

        return True, "Exam deleted successfully."

    except Exception as e:

        db.session.rollback()

        return False, f"Error deleting exam: {str(e)}"




def parse_exam_datetime(datetime_string):

    return datetime.strptime(
        datetime_string,
        "%Y-%m-%dT%H:%M"
    ).astimezone(timezone.utc)


def extract_exam_form_data(form_data):

    start_date = parse_exam_datetime(
        form_data.get('start_date')
    )

    end_date = parse_exam_datetime(
        form_data.get('end_date')
    )
    if end_date <= start_date:
        raise ValueError(
            "End date must be after start date."
        )
    return {
        "title": form_data.get('title'),
        "duration": int(form_data.get('duration') or 0),

        "marks": float(form_data.get('marks') or 1),

        "negative": float(form_data.get('negative') or 0),

        "max_attempts": int(
            form_data.get('max_attempts') or 1
        ),
        "start_date": start_date,
        "end_date": end_date
    }