from database import get_db
from extensions import db
from models.school import SchoolModel
from models.exam import ExamModel

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

# ================= NEW SYSTEM =================  
    @staticmethod
    def get_all_by_student_sa(student_name):
        return AttemptModel.query.filter_by(student_name=student_name).all()
# ================= NEW SYSTEM =================  
    @staticmethod
    def get_by_id_sa(attempt_id):
        return AttemptModel.query.get(attempt_id)
# ================= NEW SYSTEM =================  


    @staticmethod
    def count_by_school_sa(school_id):
        total = db.session.query(db.func.count(AttemptModel.id))\
            .join(ExamModel, AttemptModel.exam_id == ExamModel.id)\
            .filter(ExamModel.school_id == school_id)\
            .scalar()
        return total
# ================= NEW SYSTEM =================  
    @staticmethod
    def get_attempt_count_sa(exam_id):
        return db.session.query(db.func.count(AttemptModel.id))\
            .filter_by(exam_id=exam_id).scalar()
# ================= NEW SYSTEM =================  




class AttemptModel(db.Model):
    __tablename__ = "student_attempts"

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id"), nullable=False)

    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    student_class = db.Column(db.String(50))
    roll_number = db.Column(db.String(50))
    mobile = db.Column(db.String(20))

    ip_address = db.Column(db.String(45))  # for IPv4/IPv6

    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)

    score = db.Column(db.Float)
    total_marks = db.Column(db.Float)
    percentage = db.Column(db.Float)

    attempt_number = db.Column(db.Integer)

    # Relationships
    exam = db.relationship(ExamModel, backref="attempts")
