 
from models.attempt import AttemptModel
from openpyxl import Workbook


# ---------------------------------
# Get all attempts for an exam
# ---------------------------------


def get_results(exam_id):

    results = AttemptModel.query.with_entities(
        AttemptModel.id,
        AttemptModel.first_name,
        AttemptModel.last_name,
        AttemptModel.student_class,
        AttemptModel.roll_number,
        AttemptModel.mobile,
        AttemptModel.score,
        AttemptModel.total_marks,
        AttemptModel.percentage,
        AttemptModel.start_time,
        AttemptModel.end_time,
        AttemptModel.ip_address
    ).filter(
        AttemptModel.exam_id == exam_id,
        AttemptModel.end_time.isnot(None)
    ).order_by(
        AttemptModel.percentage.desc(),
        AttemptModel.end_time.asc()
    ).all()

    return results

 
# ---------------------------------
# Get leaderboard for an exam
# ---------------------------------
from datetime import datetime

def generate_leaderboard(exam_id):
    # Fetch full AttemptModel objects
    attempts_query = AttemptModel.query.filter(
        AttemptModel.exam_id == exam_id,
        AttemptModel.start_time.isnot(None),
        AttemptModel.end_time.isnot(None)
    ).order_by(
        AttemptModel.percentage.desc()
    ).limit(5).all()

    leaderboard = []
    for idx, a in enumerate(attempts_query, start=1):
        # Ensure valid datetime objects
        start_time = a.start_time if isinstance(a.start_time, datetime) else datetime.utcnow()
        end_time = a.end_time if isinstance(a.end_time, datetime) else datetime.utcnow()
        time_taken = end_time - start_time

        leaderboard.append({
            "rank": idx,
            "first_name": a.first_name,
            "last_name": a.last_name,
            "student_class": a.student_class,
            "roll_number": a.roll_number,
            "mobile": a.mobile,
            "score": a.score,
            "total_marks": a.total_marks,
            "percentage": a.percentage,
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