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
        exam = ExamModel(
            title=title,
            duration_minutes=duration,
            marks_per_question=marks,
            negative_marks=negative,
            max_attempts_per_mobile=max_attempts,
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
        ExamModel.max_attempts_per_mobile,
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


def publish_exam(exam_id):

    q_count = db.session.query(func.count(QuestionModel.id))\
        .filter(QuestionModel.exam_id == exam_id)\
        .scalar()

    if q_count == 0:
        return False, "Cannot publish exam without questions"

    quiz_code = generate_quiz_code()

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
    QuestionModel.query.filter_by(exam_id=exam_id).delete()

    # delete exam
    ExamModel.query.filter_by(id=exam_id).delete()

    db.session.commit()

    return True, "Exam deleted successfully."




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

    return {
        "title": form_data.get('title'),
        "duration": form_data.get('duration'),
        "marks": form_data.get('marks'),
        "negative": form_data.get('negative'),
        "max_attempts": form_data.get('max_attempts'),
        "start_date": start_date,
        "end_date": end_date
    }