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


# =========================
# School Model
# =========================
class SchoolModel(db.Model):
    __tablename__ = "schools"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationship to school admins
    admins = db.relationship("UserModel", backref="school", lazy="dynamic")
       # Optional: relationship back to attempts
    attempts = db.relationship("AttemptModel", backref="school")
 

 