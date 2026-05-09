from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from smart_exam_system.blueprints.super_admin import super_admin_bp
from smart_exam_system.models.user import UserModel
from smart_exam_system.models.school import SchoolModel
from smart_exam_system.models.exam import ExamModel
from smart_exam_system.models.attempt import AttemptModel
from smart_exam_system.extensions import db
from smart_exam_system.models.democontact import DemoRequest, ContactMessage
from smart_exam_system.utils.decorators import super_admin_required
from smart_exam_system.utils.security import hash_password
from smart_exam_system.utils.helpers import generate_slug
import secrets, string
from sqlalchemy import func
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os


@super_admin_bp.route("/run-slug-fix")
def run_slug_fix():

    schools = SchoolModel.query.all()

    for school in schools:

        if not school.slug:
            school.slug = generate_slug(school.name)

    db.session.commit()

    return "Slug fix completed"
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
    # Demo + Contact Leads
    # -------------------------
    total_demo_requests = DemoRequest.query.count()
    total_contact_messages = ContactMessage.query.count()
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
    total_attempts=total_attempts,
    total_demo_requests=total_demo_requests,
    total_contact_messages=total_contact_messages
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
    # 🔥 FIX: compute flag for template
    for s in schools:
        s.has_admin = len(list(s.admins)) > 0
    return render_template("schools.html", schools=schools,current_time=datetime.utcnow())

# =========================
# ADD SCHOOL
# =========================
@super_admin_bp.route("/schools/add", methods=["GET", "POST"])
@login_required
@super_admin_required
def add_school():
    if request.method == "POST":
        name = request.form["name"].strip()
        slug = generate_slug(name)

        # 🔥 Ensure unique slug
        existing_slug = SchoolModel.query.filter_by(slug=slug).first()
        if existing_slug:
            slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

        address = request.form["address"].strip()
        phone = request.form["phone"].strip()
        email = request.form["email"].strip()
        duration_days = request.form.get("duration_days")

        # 🔥 STEP 1: CHECK DUPLICATES
        existing_school = SchoolModel.query.filter(
            (SchoolModel.email == email) | (SchoolModel.name == name)
        ).first()
        if existing_school:
            flash("School already exists with same name or email.", "danger")
            return redirect(url_for("super_admin.add_school"))

        # 🔥 STEP 2: VALIDATE
        if not name:
            flash("School name is required.", "danger")
            return redirect(url_for("super_admin.add_school"))

        # 🔥 STEP 3: SET EXPIRY
        expiry_date = None
        if duration_days:
            expiry_date = datetime.utcnow() + timedelta(days=int(duration_days))

        # 🔥 STEP 4: HANDLE LOGO UPLOAD
        logo_file = request.files.get("logo")
        logo_filename = None
        if logo_file and logo_file.filename:
         
            logo_filename = secure_filename(logo_file.filename)
            logo_file.save(os.path.join("static/uploads/schools", logo_filename))

        # 🔥 STEP 5: CREATE SCHOOL
        new_school = SchoolModel(
            name=name,
            slug=slug,
            address=address,
            phone=phone,
            email=email,
            expiry_date=expiry_date,
            logo=logo_filename  # ✅ save logo filename in DB
        )

        db.session.add(new_school)

        demo_id = request.form.get("demo_id")
        if demo_id:
            demo = DemoRequest.query.get(demo_id)
            if demo:
                demo.status = "converted"

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

        slug = generate_slug(name)

        existing_slug = SchoolModel.query.filter(
            SchoolModel.slug == slug,
            SchoolModel.id != school.id
        ).first()

        if existing_slug:
            slug = f"{slug}-{school.id}"

        school.slug = slug
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
        if not name or not email:
            flash("Name and Email are required.", "danger")
            return redirect(url_for("super_admin.add_school_admin", school_id=school_id))

        # ✅ Generate temp password
        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))

        hashed_password = hash_password(temp_password)

        if UserModel.query.filter_by(email=email).first():
            flash("Email already exists!", "danger")
            return redirect(url_for("super_admin.add_school_admin", school_id=school_id))

        new_admin = UserModel(
            name=name,
            email=email,
            password=hashed_password,
            role="school_admin",
            school_id=school_id,
            is_active=True,
            force_password_change=True   # ✅ IMPORTANT
        )
        db.session.add(new_admin)
        db.session.commit()

        flash(f"Temporary Password: {temp_password}", "password")
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

    flash(f"Temporary Password: {temp_password}", "password")
    return redirect(request.referrer)


# =========================
# DEMO REQUESTS
# =========================

@super_admin_bp.route("/demo-requests")
@login_required
@super_admin_required
def demo_requests():
    demos = DemoRequest.query.order_by(DemoRequest.id.desc()).all()
    return render_template("demo_requests.html", demos=demos)


# =========================
# CONTACT MESSAGES
# =========================
@super_admin_bp.route("/contact-messages")
@login_required
@super_admin_required
def contact_messages():
    messages = ContactMessage.query.order_by(ContactMessage.id.desc()).all()
    return render_template("contact_messages.html", messages=messages)


# =========================
# UPDATE DEMO STATUS
# =========================
@super_admin_bp.route("/demo/<int:id>/status/<string:status>", methods=["POST"])
@login_required
@super_admin_required
def update_demo_status(id, status):
    demo = DemoRequest.query.get_or_404(id)
    demo.status = status
    db.session.commit()
    return redirect(request.referrer)


# =========================
# DELETE DEMO
# =========================
@super_admin_bp.route("/demo/<int:id>/delete", methods=["POST"])
@login_required
@super_admin_required
def delete_demo(id):
    demo = DemoRequest.query.get_or_404(id)
    db.session.delete(demo)
    db.session.commit()
    return redirect(request.referrer)


# =========================
# UPDATE CONTACT STATUS
# =========================
@super_admin_bp.route("/contact/<int:id>/status/<string:status>", methods=["POST"])
@login_required
@super_admin_required
def update_contact_status(id, status):
    msg = ContactMessage.query.get_or_404(id)
    msg.status = status
    db.session.commit()
    return redirect(request.referrer)


# =========================
# DELETE CONTACT
# =========================
@super_admin_bp.route("/contact/<int:id>/delete", methods=["POST"])
@login_required
@super_admin_required
def delete_contact(id):
    msg = ContactMessage.query.get_or_404(id)
    db.session.delete(msg)
    db.session.commit()
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

# =========================
# Convert Demo Request
# =========================
@super_admin_bp.route("/demo/<int:id>/convert")
@login_required
@super_admin_required
def convert_demo(id):
    demo = DemoRequest.query.get_or_404(id)

    return render_template(
        "add_school.html",
        demo=demo   # 👈 pass demo data
    )

# =========================
# Extend School Validity
# =========================

@super_admin_bp.route("/schools/extend/<int:school_id>/<int:days>", methods=["POST"])
@login_required
@super_admin_required
def extend_school(school_id, days):
    school = SchoolModel.query.get_or_404(school_id)

    # If expiry exists → extend from that date
    # If not → extend from today
    base_date = school.expiry_date or datetime.utcnow()

    school.expiry_date = base_date + timedelta(days=days)
    school.is_active = True

    db.session.commit()

    flash(f"School extended by {days} days!", "success")
    return redirect(url_for("super_admin.schools"))

# =========================
# Reset School Validity
# =========================

@super_admin_bp.route("/schools/reset/<int:school_id>", methods=["POST"])
@login_required
@super_admin_required
def reset_school_validity(school_id):
    school = SchoolModel.query.get_or_404(school_id)

    school.expiry_date = None
    school.is_active = True

    db.session.commit()

    flash("School validity reset successfully!", "success")
    return redirect(url_for("super_admin.schools"))

# =========================
# Delete School
# =========================

@super_admin_bp.route("/schools/delete/<int:school_id>", methods=["POST"])
@login_required
@super_admin_required
def delete_school(school_id):
    school = SchoolModel.query.get_or_404(school_id)

    # Check if admins exist
    from smart_exam_system.models.user import UserModel
    admin_exists = UserModel.query.filter_by(
        school_id=school.id,
        role="school_admin"
    ).first()

    if admin_exists:
        flash("Cannot delete school with existing admin.", "danger")
        return redirect(url_for("super_admin.schools"))

    db.session.delete(school)
    db.session.commit()

    flash("School deleted successfully!", "success")
    return redirect(url_for("super_admin.schools"))