# normalize_attempts.py
from datetime import datetime
from extensions import db
from app import create_app
from models.attempt import AttemptModel

app = create_app()

with app.app_context():
    attempts = AttemptModel.query.all()

    for a in attempts:
        # Start time
        try:
            if isinstance(a.start_time, str):
                a.start_time = datetime.fromisoformat(a.start_time)
            elif not isinstance(a.start_time, datetime):
                a.start_time = datetime.utcnow()
        except Exception:
            a.start_time = datetime.utcnow()

        # End time
        try:
            if isinstance(a.end_time, str):
                a.end_time = datetime.fromisoformat(a.end_time)
            elif not isinstance(a.end_time, datetime):
                a.end_time = datetime.utcnow()
        except Exception:
            a.end_time = datetime.utcnow()

    db.session.commit()
    print("✅ All AttemptModel datetimes normalized (robust)!")