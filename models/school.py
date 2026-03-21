from database import get_db

class School:
    @staticmethod
    def get(school_id):
        conn = get_db()
        school = conn.execute(
            "SELECT id, name FROM schools WHERE id = ?", (school_id,)
        ).fetchone()
        conn.close()
        return school
