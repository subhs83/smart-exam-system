from flask_login import UserMixin
from database import get_db
from extensions import db
from utils.security import hash_password, verify_password


class User(UserMixin):
    def __init__(self, id, name, email, password, role, school_id, is_active=True):
        self.id = id
        self.name = name
        self.email = email
        self.password = password  # stored as scrypt hash
        self.role = role
        self.school_id = school_id
        self.active = is_active



    # --- Static DB fetch ---
    @staticmethod
    def get(user_id):
        conn = get_db()
        user = conn.execute(
            "SELECT id, name, email, password, role, school_id, is_active FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        conn.close()

        if user:
            return User(
                id=user["id"],
                name=user["name"],
                email=user["email"],
                password=user["password"],
                role=user["role"],
                school_id=user["school_id"],
                is_active=user["is_active"]
            )
        return None

    # --- Teacher lifecycle actions (school-aware) ---
    @staticmethod
    def activate_teacher(teacher_id, school_id):
        """
        Activate teacher only if they belong to the current school.
        """
        conn = get_db()
        conn.execute(
            "UPDATE users SET is_active = 1 WHERE id = ? AND role = 'teacher' AND school_id = ?",
            (teacher_id, school_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def deactivate_teacher(teacher_id, school_id):
        """
        Deactivate teacher only if they belong to the current school.
        """
        conn = get_db()
        conn.execute(
            "UPDATE users SET is_active = 0 WHERE id = ? AND role = 'teacher' AND school_id = ?",
            (teacher_id, school_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def reset_teacher_password(teacher_id, school_id, new_password="default123"):
        """
        Reset teacher password only if they belong to the current school.
        """
        conn = get_db()
        hashed = hash_password(new_password)
        conn.execute(
            "UPDATE users SET password = ? WHERE id = ? AND role = 'teacher' AND school_id = ?",
            (hashed, teacher_id, school_id)
        )
        conn.commit()
        conn.close()


    @staticmethod
    def count_teachers_by_school(school_id):
        conn = get_db()
        total = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'teacher' AND school_id = ?",
            (school_id,)
        ).fetchone()[0]

        conn.close()
        return total

    @staticmethod
    def get_teachers_by_school(school_id):
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, email
            FROM users
            WHERE role='teacher' AND school_id=?
        """, (school_id,))

        teachers = cursor.fetchall()
        conn.close()

        return teachers
    
     # ================= NEW SYSTEM =================
    @staticmethod
    def count_teachers_by_school_sa(school_id):
        return UserModel.query.filter_by(
            role="teacher",
            school_id=school_id
        ).count()

    # ================= NEW SYSTEM =================

    @staticmethod
    def get_teachers_by_school_sa(school_id):
        return UserModel.query.filter_by(
            role="teacher",
            school_id=school_id
        ).all()
# ================= NEW SYSTEM =================
class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    school_id = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<User {self.email}>"

    
    
   
