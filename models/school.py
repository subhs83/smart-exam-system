from database import get_db
from extensions import db

class School:
    @staticmethod
    def get(school_id):
        conn = get_db()
        school = conn.execute(
            "SELECT id, name FROM schools WHERE id = ?", (school_id,)
        ).fetchone()
        conn.close()
        return school



class SchoolModel(db.Model):
    __tablename__ = "schools"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=True)

    # Optional: relationship back to attempts
    attempts = db.relationship("AttemptModel", backref="school")