# utils/decorators.py

from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user
from models.exam import ExamModel

# -----------------------------------------
# Super Admin Required
# -----------------------------------------
def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not current_user.is_authenticated:
            flash("Please login first.", "danger")
            return redirect(url_for("auth.login"))

        if current_user.role != "super_admin":
            flash("Access denied. Super Admin only.", "danger")
            return redirect(url_for("auth.login"))

        return f(*args, **kwargs)

    return decorated_function


# -----------------------------------------
# School Admin Required
# -----------------------------------------
def school_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not current_user.is_authenticated:
            flash("Please login first.", "danger")
            return redirect(url_for("auth.login"))

        if current_user.role != "school_admin":
            flash("Access denied. School Admin only.", "danger")
            return redirect(url_for("auth.login"))

        return f(*args, **kwargs)

    return decorated_function


# -----------------------------------------
# Teacher Required
# -----------------------------------------
def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not current_user.is_authenticated:
            flash("Please login first.", "danger")
            return redirect(url_for("auth.login"))

        if current_user.role != "teacher":
            flash("Access denied. Teacher account required.", "danger")
            return redirect(url_for("auth.login"))

        return f(*args, **kwargs)

    return decorated_function


# -----------------------------------------
# Exam Owner Required
# Ensures teacher owns the exam
# -----------------------------------------
def exam_owner_required(f):
    @wraps(f)
    def decorated_function(exam_id, *args, **kwargs):
        exam = ExamModel.query.get(exam_id)

        if not exam:
            flash("Exam not found.", "danger")
            return redirect(url_for("teacher.dashboard"))

        # Check teacher ownership
        if exam.teacher_id != current_user.id:
            flash("You are not authorized to access this exam.", "danger")
            return redirect(url_for("teacher.dashboard"))

        return f(exam_id, *args, **kwargs)

    return decorated_function


# -----------------------------------------
# School Isolation
# Ensures school admin accesses only their school
# -----------------------------------------
def school_access_required(f):
    @wraps(f)
    def decorated_function(school_id, *args, **kwargs):

        if current_user.role == "super_admin":
            return f(school_id, *args, **kwargs)

        if current_user.role == "school_admin":
            if current_user.school_id != school_id:
                flash("Access denied for this school.", "danger")
                return redirect(url_for("school_admin.dashboard"))

        return f(school_id, *args, **kwargs)

    return decorated_function