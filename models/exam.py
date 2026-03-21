from database import get_db

class Exam:

    @staticmethod
    def get_all():
        conn = get_db()
        exams = conn.execute("SELECT * FROM exams").fetchall()
        conn.close()
        return exams

    @staticmethod
    def get_by_school(school_id):
        conn = get_db()
        exams = conn.execute(
            "SELECT * FROM exams WHERE school_id = ?",
            (school_id,)
        ).fetchall()
        conn.close()
        return exams

    @staticmethod
    def count_by_school(school_id):
        conn = get_db()

        total = conn.execute(
            "SELECT COUNT(*) FROM exams WHERE school_id = ?",
            (school_id,)
        ).fetchone()[0]

        conn.close()
        return total


    @staticmethod
    def get_exams_by_teacher(teacher_id):
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, title
            FROM exams
            WHERE teacher_id=?
        """, (teacher_id,))

        exams = cursor.fetchall()
        conn.close()

        return exams

    @staticmethod
    def get_teacher_id_by_exam(exam_id):

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT teacher_id
            FROM exams
            WHERE id = ?
        """, (exam_id,))

        row = cursor.fetchone()
        conn.close()

        return row["teacher_id"] if row else None

    @staticmethod
    def get_exam_info(exam_id):
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            SELECT exams.title, users.name
            FROM exams
            JOIN users ON exams.teacher_id = users.id
            WHERE exams.id = ?
        """, (exam_id,))

        return cursor.fetchone()