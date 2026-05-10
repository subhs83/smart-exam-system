 
from smart_exam_system.models.attempt import AttemptModel
from smart_exam_system.models.question import QuestionModel
from smart_exam_system.models.answer import StudentAnswerModel
import json
from openpyxl import Workbook
from datetime import datetime
from sqlalchemy import desc, asc
from datetime import datetime
# ---------------------------------
# Get attempts Detailed Report
# ---------------------------------

def get_attempt_detailed_report(attempt_id):

    attempt = AttemptModel.query.get(attempt_id)
    if not attempt:
        return None

    question_order = json.loads(attempt.question_order or "[]")

    report = []

    for q_id in question_order:

        question = QuestionModel.query.get(q_id)

        answer = StudentAnswerModel.query.filter_by(
            attempt_id=attempt_id,
            question_id=q_id
        ).first()

        selected = answer.selected_option if answer else None
        correct = question.correct_option

        # ✅ option mapping
        option_map = {
            "A": question.option_a,
            "B": question.option_b,
            "C": question.option_c,
            "D": question.option_d
        }

        selected_text = option_map.get(selected) if selected else None
        correct_text = option_map.get(correct)

        # ⭐ FIX: NA detection
        is_na = False
        if not answer or answer.selected_option is None:
            is_na = True

        report.append({
            "question_text": question.question_text,

            "selected_option": selected if selected else "NA",   # ⭐ FIX
            "selected_text": selected_text if selected else "Not Attempted",

            "correct_option": correct,
            "correct_text": correct_text,

            "is_correct": selected == correct if not is_na else False,

            "is_na": is_na,   # ⭐ NEW IMPORTANT FLAG

            "options": option_map
        })

    return {
        "student_name": f"{attempt.first_name} {attempt.last_name}",
        "score": attempt.score,
        "total": attempt.total_marks,
        "percentage": attempt.percentage,
        "questions": report
    }
# ---------------------------------
# Get all attempts for an exam
# ---------------------------------


from collections import defaultdict

from collections import defaultdict

def get_results(exam_id):

    attempts = AttemptModel.query.filter(
        AttemptModel.exam_id == exam_id,
        AttemptModel.end_time.isnot(None)
    ).all()

    grouped = {}

    for a in attempts:

        key = (a.school_id, a.mobile, a.roll_number)

        percentage = float(a.percentage or 0)

        if key not in grouped:
            grouped[key] = {
                "best": a,
                "attempts_count": 1
            }
        else:
            data = grouped[key]
            data["attempts_count"] += 1

            existing_best = data["best"]
            existing_percentage = float(existing_best.percentage or 0)

            # keep BEST attempt
            if percentage > existing_percentage:
                data["best"] = a

    results = []

    for data in grouped.values():

        a = data["best"]

        results.append({
            "id": a.id,

            # student info
            "first_name": a.first_name,
            "last_name": a.last_name,
            "student_class": a.student_class,
            "roll_number": a.roll_number,
            "mobile": a.mobile,

            # BEST attempt data
            "score": a.score,
            "total_marks": a.total_marks,
            "percentage": float(a.percentage or 0),

            # meta
            "attempts_count": data["attempts_count"],

            "start_time": a.start_time,
            "end_time": a.end_time,

            "violation_count": a.violation_count,
            "auto_submitted_reason": a.auto_submitted_reason
        })

    return results

 
# ---------------------------------
# Get leaderboard for an exam
# ---------------------------------
 
def generate_leaderboard(exam_id):

    attempts = AttemptModel.query.filter(
        AttemptModel.exam_id == exam_id,
        AttemptModel.start_time.isnot(None),
        AttemptModel.end_time.isnot(None),
        AttemptModel.score.isnot(None),
        AttemptModel.total_marks.isnot(None),
        AttemptModel.percentage.isnot(None)
    ).all()

    grouped = {}

    for a in attempts:

        key = (a.school_id, a.mobile, a.roll_number)
        percentage = float(a.percentage or 0)

        if key not in grouped:
            grouped[key] = a
        else:
            existing = grouped[key]

            existing_percentage = float(existing.percentage or 0)

            # keep BEST attempt
            if percentage > existing_percentage:
                grouped[key] = a

            # tie-break → faster completion wins
            elif percentage == existing_percentage:
                if a.end_time and existing.end_time:
                    if a.end_time < existing.end_time:
                        grouped[key] = a

    # convert to list
    students = list(grouped.values())

    # final ranking sort
    students.sort(
        key=lambda x: (
            -float(x.percentage or 0),  # highest first
            x.end_time                  # earlier wins tie
        )
    )

    leaderboard = []
    rank = 1

    for a in students[:5]:   # TOP 5 AFTER grouping

        start_time = a.start_time if isinstance(a.start_time, datetime) else datetime.utcnow()
        end_time = a.end_time if isinstance(a.end_time, datetime) else datetime.utcnow()

        leaderboard.append({
            "rank": rank,
            "first_name": a.first_name,
            "last_name": a.last_name,
            "student_class": a.student_class,
            "roll_number": a.roll_number,
            "mobile": a.mobile,

            "score": a.score,
            "total_marks": a.total_marks,
            "percentage": float(a.percentage or 0),

            "time_taken": end_time - start_time
        })

        rank += 1

    return leaderboard
# ---------------------------------
# Export Results to Excel
# ---------------------------------
def export_results_to_excel(exam_id, file_path):

    attempts = AttemptModel.query.filter_by(
        exam_id=exam_id
    ).order_by(
        AttemptModel.score.desc()
    ).all()

    if not attempts:
        return False, "No attempts found."

    wb = Workbook()
    ws = wb.active
    ws.title = "Results"

    ws.append([
        "First Name",
        "Last Name",
        "Class",
        "Roll Number",
        "Mobile",
        "Score",
        "Total Marks",
        "Percentage",
        "Start Time",
        "End Time",
        "IP Address"
    ])

    for row in attempts:
        ws.append([
            row.first_name,
            row.last_name,
            row.student_class,
            row.roll_number,
            row.mobile,
            row.score,
            row.total_marks,
            row.percentage,
            row.start_time,
            row.end_time,
            row.ip_address
        ])

    wb.save(file_path)

    return True, f"Results exported to {file_path}"


def get_student_attempts(mobile, roll, exam_id):

    return AttemptModel.query.filter(
        AttemptModel.mobile == mobile,
        AttemptModel.roll_number == roll,
        AttemptModel.exam_id == exam_id
    ).order_by(
        AttemptModel.attempt_number.asc()
    ).all()

def get_best_attempt_id(attempts):

    best_attempt_id = None
    best_percentage = -1

    for attempt in attempts:

        if (
            attempt.percentage is not None
            and attempt.percentage > best_percentage
        ):
            best_percentage = attempt.percentage
            best_attempt_id = attempt.id

    return best_attempt_id



def build_student_summary(attempts):

    first_attempt = attempts[0]

    return {
        "mobile": first_attempt.mobile,
        "roll": first_attempt.roll_number,
        "name": (
            f"{first_attempt.first_name} "
            f"{first_attempt.last_name}"
        ),
        "class": first_attempt.student_class
    }