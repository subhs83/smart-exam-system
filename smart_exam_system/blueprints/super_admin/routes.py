from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from smart_exam_system.blueprints.super_admin import super_admin_bp
from smart_exam_system.models.user import UserModel
from smart_exam_system.models.school import SchoolModel
from smart_exam_system.models.exam import ExamModel
from smart_exam_system.models.attempt import AttemptModel
from smart_exam_system.extensions import db
from smart_exam_system.utils.decorators import super_admin_required
from smart_exam_system.utils.security import hash_password
import secrets, string
from sqlalchemy import func


# =========================
# SUPER ADMIN DASHBOARD
# =========================
@super_admin_bp.route("/dashboard")
@login_required
@super_admin_required
def dashboard():
    # -------------------------
    # Total Schools
    # -------------------------
    total_schools = SchoolModel.query.count()

    # -------------------------
    # Total Exams
    # -------------------------
    total_exams = ExamModel.query.count()

    # -------------------------
    # Total Teachers
    # -------------------------
    total_teachers = UserModel.query.filter_by(role="teacher").count()

    # -------------------------
    # Total Unique Students
    # Use subquery with distinct (school_id, roll_number) for SQLite compatibility
    # -------------------------
    student_subquery = db.session.query(
        AttemptModel.school_id,
        AttemptModel.roll_number
    ).filter(
        AttemptModel.roll_number.isnot(None),
        AttemptModel.roll_number != ""
    ).distinct().subquery()

    total_students = db.session.query(func.count()).select_from(student_subquery).scalar()

    # -------------------------
    # Optional: Total Attempts (all student attempts)
    # -------------------------
    total_attempts = db.session.query(func.count(AttemptModel.id)).scalar()

    return render_template(
        "super_admin_dashboard.html",
        total_schools=total_schools,
        total_exams=total_exams,
        total_teachers=total_teachers,
        total_students=total_students,
        total_attempts=total_attempts
    )
# =========================
# VIEW ALL SCHOOLS
# =========================
@super_admin_bp.route("/schools")
@login_required
@super_admin_required
def schools():
    if current_user.role != "super_admin":
        abort(403)

    schools = SchoolModel.query.order_by(SchoolModel.id.asc()).all()
    return render_template("schools.html", schools=schools)

# =========================
# ADD SCHOOL
# =========================
@super_admin_bp.route("/schools/add", methods=["GET", "POST"])
@login_required
@super_admin_required
def add_school():
    if request.method == "POST":
        name = request.form["name"].strip()
        address = request.form["address"].strip()
        phone = request.form["phone"].strip()
        email = request.form["email"].strip()

        if not name:
            flash("School name is required.", "danger")
            return redirect(url_for("super_admin.add_school"))

        new_school = SchoolModel(name=name, address=address, phone=phone, email=email)
        db.session.add(new_school)
        db.session.commit()

        flash("School created successfully!", "success")
        return redirect(url_for("super_admin.schools"))

    return render_template("add_school.html")

# =========================
# EDIT SCHOOL
# =========================
@super_admin_bp.route("/schools/edit/<int:school_id>", methods=["GET", "POST"])
@login_required
@super_admin_required
def edit_school(school_id):

    school = SchoolModel.query.get_or_404(school_id)

    if request.method == "POST":
        name = request.form["name"].strip()
        address = request.form["address"].strip()
        phone = request.form["phone"].strip()
        email = request.form["email"].strip()

        if not name:
            flash("School name is required.", "danger")
            return redirect(url_for("super_admin.edit_school", school_id=school_id))

        school.name = name
        school.address = address
        school.phone = phone
        school.email = email
        db.session.commit()

        flash("School updated successfully!", "success")
        return redirect(url_for("super_admin.schools"))

    return render_template("edit_school.html", school=school)

# =========================
# TOGGLE SCHOOL STATUS
# =========================
@super_admin_bp.route("/schools/toggle/<int:school_id>", methods=["POST"])
@login_required
@super_admin_required
def toggle_school(school_id):

    school = SchoolModel.query.get_or_404(school_id)
    school.is_active = not school.is_active
    db.session.commit()

    return redirect(url_for("super_admin.schools"))

# =========================
# VIEW SCHOOL ADMINS
# =========================
@super_admin_bp.route("/schools/<int:school_id>/admins")
@login_required
@super_admin_required
def view_school_admins(school_id):

    school = SchoolModel.query.get_or_404(school_id)
    admins = UserModel.query.filter_by(role="school_admin", school_id=school_id).order_by(UserModel.id.asc()).all()

    return render_template("view_school_admins.html", school=school, admins=admins)

# =========================
# ADD SCHOOL ADMIN
# =========================
@super_admin_bp.route("/schools/<int:school_id>/admins/add", methods=["GET", "POST"])
@login_required
@super_admin_required
def add_school_admin(school_id):

    school = SchoolModel.query.get_or_404(school_id)

    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("super_admin.add_school_admin", school_id=school_id))

        hashed_password = hash_password(password)

        if UserModel.query.filter_by(email=email).first():
            flash("Email already exists!", "danger")
            return redirect(url_for("super_admin.add_school_admin", school_id=school_id))

        new_admin = UserModel(
            name=name,
            email=email,
            password=hashed_password,
            role="school_admin",
            school_id=school_id,
            is_active=True
        )
        db.session.add(new_admin)
        db.session.commit()

        flash("School Admin created successfully!", "success")
        return redirect(url_for("super_admin.view_school_admins", school_id=school_id))

    return render_template("add_school_admin.html", school=school)

# =========================
# TOGGLE SCHOOL ADMIN STATUS
# =========================
@super_admin_bp.route("/admins/toggle/<int:user_id>", methods=["POST"])
@login_required
@super_admin_required
def toggle_school_admin(user_id):

    admin = UserModel.query.get_or_404(user_id)
    if admin.role == "school_admin":
        admin.is_active = not admin.is_active
        db.session.commit()

    return redirect(request.referrer)

# =========================
# RESET SCHOOL ADMIN PASSWORD
# =========================
@super_admin_bp.route("/admins/reset-password/<int:user_id>", methods=["POST"])
@login_required
@super_admin_required
def reset_school_admin_password(user_id):

    admin = UserModel.query.get_or_404(user_id)
    if admin.role != "school_admin":
        abort(404)

    temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
    admin.password = hash_password(temp_password)
    admin.force_password_change = True
    db.session.commit()

    flash(f"Temporary Password: {temp_password}", "warning")
    return redirect(request.referrer)

# =========================
# View Stats
# =========================

@super_admin_bp.route("/stats")
@login_required
@super_admin_required
def platform_stats():
    total_schools = SchoolModel.query.count()
    total_exams = ExamModel.query.count()
    total_teachers = UserModel.query.filter_by(role="teacher").count()
    total_attempts = AttemptModel.query.count()

    return render_template(
        "platform_stats.html",
        total_schools=total_schools,
        total_exams=total_exams,
        total_teachers=total_teachers,
        total_attempts=total_attempts
    )

# =========================
# System Health
# =========================

from datetime import datetime

@super_admin_bp.route("/system-health")
@login_required
@super_admin_required
def system_health():
    return render_template(
        "system_health.html",
        current_time=datetime.now()
    )