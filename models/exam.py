from database import get_db
from extensions import db
from models.user import UserModel

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


# ================= NEW SYSTEM =================
    @staticmethod
    def count_by_school_sa(school_id):
        return ExamModel.query.filter_by(
            school_id=school_id
        ).count()
# ================= NEW SYSTEM =================
    @staticmethod
    def get_exams_by_teacher_sa(teacher_id):
        return ExamModel.query.filter_by(
            teacher_id=teacher_id
        ).all()

# ================= NEW SYSTEM =================

    @staticmethod
    def get_teacher_id_by_exam_sa(exam_id):
        exam = ExamModel.query.filter_by(id=exam_id).first()
        return exam.teacher_id if exam else None
 # ================= NEW SYSTEM =================
    @staticmethod
    def get_exam_info_sa(exam_id):
        # Fetch exam object
        exam = ExamModel.query.filter_by(id=exam_id).first()
        if not exam:
            return None, None  # safe if exam doesn't exist

        # Fetch teacher object
        teacher = UserModel.query.filter_by(id=exam.teacher_id).first()
        teacher_name = teacher.name if teacher else None

        # Return in same order as old function
        return exam.title, teacher_name
 # ================= NEW SYSTEM =================       

class ExamModel(db.Model):
    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)

    marks_per_question = db.Column(db.Integer, default=1)
    negative_marks = db.Column(db.Float, default=0)
    max_attempts_per_mobile = db.Column(db.Integer, default=1)

    status = db.Column(db.String, default="draft")

    school_id = db.Column(db.Integer, nullable=False)
    teacher_id = db.Column(db.Integer, nullable=False)

     # ✅ ADD HER

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    published_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Exam {self.title}>"