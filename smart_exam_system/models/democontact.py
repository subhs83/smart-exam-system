from datetime import datetime
from smart_exam_system.extensions import db


# ================= DEMO MODEL =================
class DemoRequest(db.Model):
    __tablename__ = "demo_requests"

    id = db.Column(db.Integer, primary_key=True)
    school_name = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    size = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ================= CONTACT MODEL =================
class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)