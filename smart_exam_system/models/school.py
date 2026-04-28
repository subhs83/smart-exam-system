from smart_exam_system.extensions import db
class School:
    @staticmethod
    def get(school_id):
        school = SchoolModel.query.get(school_id)
        if school:
            # Return a dictionary similar to what raw SQL returned
            return {"id": school.id, "name": school.name}
        return None


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
    expiry_date = db.Column(db.DateTime, nullable=True)
    # Relationship to school admins
    admins = db.relationship("UserModel", backref="school", lazy="dynamic")
       # Optional: relationship back to attempts
    attempts = db.relationship("AttemptModel", backref="school")
 

 