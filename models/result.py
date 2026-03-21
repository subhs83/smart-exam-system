from database import get_db

class Result:

    @staticmethod
    def get_all():
        conn = get_db()
        results = conn.execute(
            "SELECT id, student_name, exam_name, score FROM results"
        ).fetchall()
        conn.close()
        return results

    @staticmethod
    def get_by_id(result_id):
        conn = get_db()
        result = conn.execute(
            "SELECT id, student_name, exam_name, score FROM results WHERE id = ?",
            (result_id,)
        ).fetchone()
        conn.close()
        return result

    @staticmethod
    def get_by_school(school_id):
        conn = get_db()
        results = conn.execute("""
            SELECT 
                r.id,
                r.mobile,
                r.score,
                r.total,
                r.submitted_at,
                e.title AS exam_title
            FROM results r
            JOIN exams e ON r.exam_id = e.id
            WHERE r.school_id = ?
            ORDER BY r.submitted_at DESC
        """, (school_id,)).fetchall()

        conn.close()
        return results