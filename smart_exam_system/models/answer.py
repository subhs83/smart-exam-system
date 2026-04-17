from smart_exam_system.extensions import db

class StudentAnswerModel(db.Model):
    __tablename__ = "student_answers"

    id = db.Column(db.Integer, primary_key=True)

    attempt_id = db.Column(
        db.Integer,
        db.ForeignKey("student_attempts.id"),
        nullable=False
    )

    question_id = db.Column(
        db.Integer,
        db.ForeignKey("questions.id"),
        nullable=False
    )

    selected_option = db.Column(db.String(1))
    is_correct = db.Column(db.Integer, default=0)

    answered_at = db.Column(db.DateTime)