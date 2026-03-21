from database import get_db
from openpyxl import Workbook


# ---------------------------------
# Get all attempts for an exam
# ---------------------------------
def get_results(exam_id):

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            id,
            first_name,
            last_name,
            student_class,
            roll_number,
            mobile,
            score,
            total_marks,
            percentage,
            start_time,
            end_time,
            ip_address
        FROM student_attempts
        WHERE exam_id = ?
        AND end_time IS NOT NULL
        ORDER BY percentage DESC, percentage DESC, end_time ASC
    """, (exam_id,))

    return cursor.fetchall()

# ---------------------------------
# Generate Leaderboard
# ---------------------------------
# ---------------------------------
# Get leaderboard for an exam
# ---------------------------------
def generate_leaderboard(exam_id):
    """
    Leaderboard ranking:
    1. Highest score first
    2. If tie → fastest completion wins
    """

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            first_name,
            last_name,
            student_class,
            roll_number,
            mobile,
            score,
            total_marks,
            percentage,
            (strftime('%s', end_time) - strftime('%s', start_time)) AS time_taken
        FROM student_attempts
        WHERE exam_id = ?
        AND end_time IS NOT NULL
        ORDER BY percentage DESC, time_taken ASC
        LIMIT 5
    """, (exam_id,))

    attempts = cursor.fetchall()

    leaderboard = []
    for idx, row in enumerate(attempts, start=1):
        row_dict = dict(row)
        row_dict["rank"] = idx
        leaderboard.append(row_dict)

    return leaderboard
# ---------------------------------
# Export Results to Excel
# ---------------------------------
def export_results_to_excel(exam_id, file_path):
    """
    Export student attempts to Excel
    """

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM student_attempts
        WHERE exam_id = ?
        ORDER BY score DESC
    """, (exam_id,))

    attempts = cursor.fetchall()

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
            row["first_name"],
            row["last_name"],
            row["class"],
            row["roll_number"],
            row["mobile"],
            row["score"],
            row["total_marks"],
            row["percentage"],
            row["start_time"],
            row["end_time"],
            row["ip_address"]
        ])

    wb.save(file_path)

    return True, f"Results exported to {file_path}"