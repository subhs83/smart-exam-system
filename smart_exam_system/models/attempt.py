from smart_exam_system.extensions import db
from datetime import datetime 
from smart_exam_system.models.exam import ExamModel

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

    start_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    score = db.Column(db.Float)
    total_marks = db.Column(db.Float)
    percentage = db.Column(db.Float)

    attempt_number = db.Column(db.Integer)
    question_order = db.Column(db.Text)  # ✅ ADD THIS
    option_order = db.Column(db.Text)  # JSON mapping per question
        # ✅ NEW
    is_submitted = db.Column(db.Boolean, default=False)
    
     # ✅ NEW Violation / Auto-Submit Reason Tracking
    violation_count = db.Column(db.Integer, default=0)

    violation_log = db.Column(db.Text, nullable=True)  
    # stores JSON list of events

    auto_submitted_reason = db.Column(db.String(255), nullable=True)

    last_violation_time = db.Column(db.DateTime, nullable=True)
    # Relationships
    exam = db.relationship(ExamModel, backref="attempts")
    __table_args__ = (
    db.Index('idx_exam_submitted_percentage',
             'exam_id', 'is_submitted', 'percentage'),
)

class Attempt:

    @staticmethod
    def get_all_by_student(student_name):
        return AttemptModel.query.filter_by(student_name=student_name).all()

    @staticmethod
    def get_by_id(attempt_id):
        return AttemptModel.query.get(attempt_id)
 

    @staticmethod
    def count_by_school(school_id):
        total = db.session.query(db.func.count(AttemptModel.id))\
            .join(ExamModel, AttemptModel.exam_id == ExamModel.id)\
            .filter(ExamModel.school_id == school_id)\
            .scalar()
        return total
 
    @staticmethod
    def get_attempt_count(exam_id):
        return db.session.query(db.func.count(AttemptModel.id))\
            .filter_by(exam_id=exam_id).scalar()
