from datetime import datetime

from smart_exam_system.extensions import db
from smart_exam_system.models.exam import ExamModel


class AttemptModel(db.Model):
    __tablename__ = "student_attempts"

    id = db.Column(db.Integer, primary_key=True)

    exam_id = db.Column(
        db.Integer,
        db.ForeignKey("exams.id"),
        nullable=False
    )

    school_id = db.Column(
        db.Integer,
        db.ForeignKey("schools.id"),
        nullable=False
    )

    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    student_class = db.Column(db.String(50))
    roll_number = db.Column(db.String(50))
    mobile = db.Column(db.String(20))

    # IPv4 / IPv6
    ip_address = db.Column(db.String(45))

    start_time = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    end_time = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    score = db.Column(db.Float)
    total_marks = db.Column(db.Float)
    percentage = db.Column(db.Float)

    attempt_number = db.Column(db.Integer)

    # Randomized question order
    question_order = db.Column(db.Text)

    # JSON mapping for randomized options
    option_order = db.Column(db.Text)

    is_submitted = db.Column(
        db.Boolean,
        default=False
    )

    # Violation / Auto-submit tracking
    violation_count = db.Column(
        db.Integer,
        default=0
    )

    violation_log = db.Column(
        db.Text,
        nullable=True
    )

    auto_submitted_reason = db.Column(
        db.String(255),
        nullable=True
    )

    last_violation_time = db.Column(
        db.DateTime,
        nullable=True
    )

    # Relationships
    exam = db.relationship(
        ExamModel,
        backref="attempts"
    )

    __table_args__ = (
        db.Index(
            "idx_exam_submitted_percentage",
            "exam_id",
            "is_submitted",
            "percentage",
        ),
    )

    # --------------------------
    # Query Helpers
    # --------------------------

    @classmethod
    def get_all_by_student(cls, student_name):
        return cls.query.filter_by(
            student_name=student_name
        ).all()

    @classmethod
    def get_by_id(cls, attempt_id):
        return cls.query.get(attempt_id)

    @classmethod
    def count_by_school(cls, school_id):
        return (
            db.session.query(db.func.count(cls.id))
            .join(ExamModel, cls.exam_id == ExamModel.id)
            .filter(ExamModel.school_id == school_id)
            .scalar()
        )

    @classmethod
    def get_attempt_count(cls, exam_id):
        return (
            db.session.query(db.func.count(cls.id))
            .filter_by(exam_id=exam_id)
            .scalar()
        )