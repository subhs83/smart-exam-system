
from extensions import db
from models.user import UserModel

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

    # ✅ ADD THIS
    quiz_code = db.Column(db.String(20), unique=True, nullable=True)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    published_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Exam {self.title}>"

        
class Exam:
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

    @staticmethod
    def get_exams_by_school_sa(school_id):
        return ExamModel.query.filter_by(school_id=school_id).all()
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
 # ================= old SYSTEM =================       
 