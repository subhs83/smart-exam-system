from smart_exam_system.extensions import db
from smart_exam_system.models.question import QuestionModel
from openpyxl import load_workbook


# -------------------------------
# Upload Questions from Excel
# -------------------------------

def upload_questions(exam_id, excel_file):
    try:
        workbook = load_workbook(excel_file)
        sheet = workbook.active

        # 🔥 DELETE OLD QUESTIONS FIRST
        QuestionModel.query.filter_by(exam_id=exam_id).delete()

        row_count = 0

        for row in sheet.iter_rows(min_row=2, values_only=True):

            if not row or all(cell is None for cell in row):
                continue

            if len(row) < 6:
                return False, "Excel format error: Expected 6 columns."

            question, option_a, option_b, option_c, option_d, correct_option = row[:6]

            new_question = QuestionModel(
                exam_id=exam_id,
                question_text=question,
                option_a=option_a,
                option_b=option_b,
                option_c=option_c,
                option_d=option_d,
                correct_option=correct_option.upper()
            )

            db.session.add(new_question)
            row_count += 1

        db.session.commit()

        return True, f"{row_count} questions uploaded successfully."

    except Exception as e:
        db.session.rollback()
        return False, f"Error uploading questions: {str(e)}"

# -------------------------------
# Get all questions for an exam
# -------------------------------

def get_exam_questions(exam_id):
    """
    Returns all questions for given exam
    """

    return QuestionModel.query\
        .filter_by(exam_id=exam_id)\
        .order_by(QuestionModel.id.asc())\
        .all()