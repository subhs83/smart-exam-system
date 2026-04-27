 
from smart_exam_system.models.attempt import AttemptModel
from smart_exam_system.models.question import QuestionModel
from smart_exam_system.models.answer import StudentAnswerModel
import json
from openpyxl import Workbook
from datetime import datetime
from sqlalchemy import desc, asc
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


def get_results(exam_id):

    query = AttemptModel.query.filter(
        AttemptModel.exam_id == exam_id,
        AttemptModel.end_time.isnot(None)
    ).order_by(
    AttemptModel.percentage.desc().nullslast(),
    AttemptModel.end_time.asc()
    ).all()

    results = []

    for a in query:
        percentage = float(a.percentage) if a.percentage is not None else 0.0

        results.append({
            "id": a.id,
            "first_name": a.first_name,
            "last_name": a.last_name,
            "student_class": a.student_class,
            "roll_number": a.roll_number,
            "mobile": a.mobile,
            "score": a.score,
            "total_marks": a.total_marks,
            "percentage": percentage,   # ✅ safe
            "start_time": a.start_time,
            "end_time": a.end_time,
            "ip_address": a.ip_address,
            "violation_count": a.violation_count,
            "auto_submitted_reason": a.auto_submitted_reason
        })

    return results

 
# ---------------------------------
# Get leaderboard for an exam
# ---------------------------------


def generate_leaderboard(exam_id):

    attempts_query = AttemptModel.query.filter(
        AttemptModel.exam_id == exam_id,
        AttemptModel.start_time.isnot(None),
        AttemptModel.end_time.isnot(None),

        # 🔥 ADD THESE (CRITICAL)
        AttemptModel.score.isnot(None),
        AttemptModel.total_marks.isnot(None),
        AttemptModel.percentage.isnot(None)
    ).order_by(
        desc(AttemptModel.percentage),
        asc(AttemptModel.end_time)
    ).limit(5).all()

    leaderboard = []
    prev_percentage = None
    rank = 0

    for idx, a in enumerate(attempts_query, start=1):

        start_time = a.start_time if isinstance(a.start_time, datetime) else datetime.utcnow()
        end_time = a.end_time if isinstance(a.end_time, datetime) else datetime.utcnow()
        time_taken = end_time - start_time

        percentage = float(a.percentage) if a.percentage is not None else 0.0

        # ✅ REAL RANK LOGIC (tie handling)
        if percentage != prev_percentage:
            rank = idx

        prev_percentage = percentage

        leaderboard.append({
            "rank": rank,
            "first_name": a.first_name,
            "last_name": a.last_name,
            "student_class": a.student_class,
            "roll_number": a.roll_number,
            "mobile": a.mobile,
            "score": a.score,
            "total_marks": a.total_marks,
            "percentage": percentage,
            "time_taken": time_taken
        })

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

