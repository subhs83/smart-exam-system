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
from smart_exam_system.utils.services.school_service import generate_unique_school_slug
from smart_exam_system.utils.services.super_admin_service import (
    build_super_admin_dashboard,
    create_school_service
)
import secrets
import string
from datetime import datetime, timedelta
import os

# =========================
# Temporarily add route
# =========================
from smart_exam_system.utils.db_fixes import run_all_fixes
@super_admin_bp.route("/db-fix-contact-phone")
def fix_contact_phone():
    run_all_fixes()
    return "DB FIX EXECUTED"

# =========================
# SUPER ADMIN DASHBOARD
# =========================
@super_admin_bp.route("/dashboard")
@login_required
@super_admin_required
def dashboard():
    dashboard_data = build_super_admin_dashboard()
    return render_template(
        "super_admin_dashboard.html",
        **dashboard_data
    )
# =========================
# VIEW ALL SCHOOLS
# =========================
@super_admin_bp.route("/schools")
@login_required
@super_admin_required
def schools():

    schools = SchoolModel.query.order_by(SchoolModel.id.asc()).all()

    # mark if school has admin
    for s in schools:
        s.has_admin = bool(s.admins)

    return render_template(
        "schools.html",
        schools=schools,
        current_time=datetime.utcnow()
    )

# =========================
# ADD SCHOOL
# =========================
@super_admin_bp.route("/schools/add", methods=["GET", "POST"])
@login_required
@super_admin_required
def add_school():

    if request.method == "POST":

        result = create_school_service(request.form, request.files)

        if result.get("error"):
            flash(result["error"], "danger")
            return redirect(url_for("super_admin.add_school"))

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

        # update basic fields
        school.name = name
        school.address = address
        school.phone = phone
        school.email = email

        # regenerate slug
        school.slug = generate_unique_school_slug(name, school.id)

        # -----------------------------
        # LOGO HANDLING (NEW LOGIC)
        # -----------------------------
        logo_file = request.files.get("logo")

        if logo_file and logo_file.filename:

            import os
            from werkzeug.utils import secure_filename

            upload_folder = "static/uploads/schools"

            # delete old logo if exists
            if school.logo:
                old_path = os.path.join(upload_folder, school.logo)
                if os.path.exists(old_path):
                    os.remove(old_path)

            # save new logo
            filename = secure_filename(logo_file.filename)
            logo_path = os.path.join(upload_folder, filename)
            logo_file.save(logo_path)

            school.logo = filename

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

        # check duplicate FIRST
        if UserModel.query.filter_by(email=email).first():
            flash("Email already exists!", "danger")
            return redirect(url_for("super_admin.add_school_admin", school_id=school_id))

        # generate temp password
        temp_password = ''.join(
            secrets.choice(string.ascii_letters + string.digits)
            for _ in range(8)
        )

        hashed_password = hash_password(temp_password)

        new_admin = UserModel(
            name=name,
            email=email,
            password=hashed_password,
            role="school_admin",
            school_id=school_id,
            is_active=True,
            force_password_change=True
        )

        db.session.add(new_admin)
        db.session.commit()

        # safer flash (no sensitive exposure style)
        flash("School Admin created successfully!", "success")
        flash(f"Temporary password (show once): {temp_password}", "info")

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

    if admin.role != "school_admin":
        abort(404)

    admin.is_active = not admin.is_active
    db.session.commit()

    return redirect(request.referrer or url_for("super_admin.schools"))


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

    temp_password = ''.join(
        secrets.choice(string.ascii_letters + string.digits)
        for _ in range(10)
    )

    admin.password = hash_password(temp_password)
    admin.force_password_change = True
    db.session.commit()

    flash(f"Temporary Password: {temp_password}", "password")

    return redirect(request.referrer or url_for("super_admin.schools"))


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
    return redirect(request.referrer or url_for("super_admin.demo_requests"))


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
    return redirect(request.referrer or url_for("super_admin.demo_requests"))


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
    return redirect(request.referrer or url_for("super_admin.contact_messages"))


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
    return redirect(request.referrer or url_for("super_admin.contact_messages"))
    
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
        demo=demo
    )

# =========================
# Extend School Validity
# =========================

@super_admin_bp.route("/schools/extend/<int:school_id>/<int:days>", methods=["POST"])
@login_required
@super_admin_required
def extend_school(school_id, days):
    school = SchoolModel.query.get_or_404(school_id)

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