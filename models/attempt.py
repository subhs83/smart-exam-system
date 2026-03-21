from database import get_db

class Attempt:
    @staticmethod
    def get_all_by_student(student_name):
        conn = get_db()
        attempts = conn.execute(
            "SELECT id, student_name, exam_id, score FROM attempts WHERE student_name = ?",
            (student_name,)
        ).fetchall()
        conn.close()
        return attempts

    @staticmethod
    def get_by_id(attempt_id):
        conn = get_db()
        attempt = conn.execute(
            "SELECT id, student_name, exam_id, score FROM attempts WHERE id = ?",
            (attempt_id,)
        ).fetchone()
        conn.close()
        return attempt

    @staticmethod
    def count_by_school(school_id):
        conn = get_db()

        total = conn.execute("""
            SELECT COUNT(*)
            FROM student_attempts a
            JOIN exams e ON a.exam_id = e.id
            WHERE e.school_id = ?
        """, (school_id,)).fetchone()[0]

        conn.close()
        return total

     
    @staticmethod
    def get_attempt_count(exam_id):
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM student_attempts
            WHERE exam_id=?
        """, (exam_id,))

        count = cursor.fetchone()[0]
        conn.close()

        return count