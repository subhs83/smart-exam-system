from database import get_db

class Question:
    @staticmethod
    def get_all_by_exam(exam_id):
        conn = get_db()
        questions = conn.execute(
            "SELECT id, exam_id, text, options, correct_answer FROM questions WHERE exam_id = ?",
            (exam_id,)
        ).fetchall()
        conn.close()
        return questions

    @staticmethod
    def get_by_id(question_id):
        conn = get_db()
        question = conn.execute(
            "SELECT id, exam_id, text, options, correct_answer FROM questions WHERE id = ?",
            (question_id,)
        ).fetchone()
        conn.close()
        return question
