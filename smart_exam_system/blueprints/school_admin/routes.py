from smart_exam_system.blueprints.school_admin import school_admin_bp
from flask import render_template, redirect, url_for, flash, abort, Response, request,session,send_file
from flask_login import login_required, current_user
from smart_exam_system.utils.decorators import school_admin_required
from smart_exam_system.models.user import UserModel
from smart_exam_system.models.exam import ExamModel
from smart_exam_system.utils.services.school_service import build_school_dashboard_data,build_teacher_exam_list
from smart_exam_system.models.attempt import AttemptModel
from smart_exam_system.utils.services.result_service import get_results, generate_leaderboard
from smart_exam_system.utils.services.report_service import generate_exam_report, generate_school_report,build_exam_context
from smart_exam_system.forms.teacher_forms import AddTeacherForm


# --------------------------
# Dashboard
# --------------------------
@school_admin_bp.route("/dashboard")
@login_required
@school_admin_required
def dashboard():
    dashboard_data = build_school_dashboard_data(current_user.school_id)
    return render_template(
        "school_admin_dashboard.html",
        active_page="dashboard",
        **dashboard_data
    )

# --------------------------
# Add Teacher (SQLAlchemy)
# --------------------------
@school_admin_bp.route("/add_teacher", methods=["GET", "POST"])
@login_required
@school_admin_required
def add_teacher():
    form = AddTeacherForm()

    if form.validate_on_submit():
        teacher = UserModel.add_teacher(
            name=form.name.data,
            email=form.email.data,
            password=form.password.data,
            school_id=current_user.school_id
        )

        # 🚨 Handle duplicate email
        if not teacher:
            flash("Email already exists!", "danger")
            return redirect(url_for("school_admin.add_teacher"))

        flash("Teacher added successfully!", "success")
        return redirect(url_for("school_admin.view_teachers"))

    return render_template("add_teacher.html", form=form, active_page="add_teacher")

# --------------------------
# View Teachers
# --------------------------
@school_admin_bp.route("/view_teachers")
@login_required
@school_admin_required
def view_teachers():
    teachers = UserModel.get_teachers_by_school(current_user.school_id)
    return render_template(
        "view_teachers.html", 
        teachers=teachers,
         active_page="teachers"
        )

# --------------------------
# Toggle Teacher Active/Inactive
# --------------------------
@school_admin_bp.route("/toggle_teacher/<int:teacher_id>")
@login_required
@school_admin_required
def toggle_teacher(teacher_id):
    success = UserModel.toggle_teacher_status(
    teacher_id,
    current_user.school_id
    )

    if not success:
        abort(404)

    flash("Teacher status updated!", "info")
    return redirect(url_for("school_admin.view_teachers"))

# --------------------------
# Reset Teacher Password
# --------------------------
@school_admin_bp.route("/reset_teacher_password/<int:teacher_id>", methods=["POST"])
@login_required
@school_admin_required
def reset_teacher_password(teacher_id):
    success = UserModel.reset_teacher_password(
    teacher_id,
    current_user.school_id
    )

    if not success:
        abort(404)
    flash("Teacher password reset successfully!", "warning")
    return redirect(url_for("school_admin.view_teachers"))

# --------------------------
#  teachers and Exams
# --------------------------
 
@school_admin_bp.route('/teachers')
@login_required
@school_admin_required
def teachers():
    school_id = current_user.school_id
    teachers = UserModel.get_teachers_by_school(school_id)
    return render_template(
        'teachers.html',
        teachers=teachers,
        active_page="exams"
    )
# --------------------------
# View Exams
# --------------------------
 
@school_admin_bp.route('/teacher/<int:teacher_id>/exams')
@login_required
@school_admin_required
def teacher_exams(teacher_id):
    exam_list = build_teacher_exam_list(teacher_id)
    return render_template(
        "teacher_exams.html",
        exams=exam_list,
        active_page="exams"
    )
# ---------------------------------
# School Admin - Exam Results
# ---------------------------------
@school_admin_bp.route('/school_admin/exams/<int:exam_id>/results')
@login_required
@school_admin_required
def admin_exam_results(exam_id):

    results = get_results(exam_id)
    exam_context = build_exam_context(exam_id)

    return render_template(
        'school_admin_results.html',
        exam_id=exam_id,
        results=results,
        active_page="results",
        **exam_context
    )
# --------------------------
# Leaderboard
# --------------------------
# ---------------------------------
# School Admin - Leaderboard
# ---------------------------------
@school_admin_bp.route('/school-admin/exams/<int:exam_id>/leaderboard')
@school_admin_required
@login_required
def admin_exam_leaderboard(exam_id):

    leaderboard = generate_leaderboard(exam_id)
     # get teacher id from exam
    teacher_id = ExamModel.get_teacher_id_by_exam(exam_id)
    exam_title, teacher_name = ExamModel.get_exam_info(exam_id)
    return render_template(
        'school_admin_leaderboard.html',
        exam_id=exam_id,
        teacher_id=teacher_id,
        exam_title = exam_title,
        teacher_name = teacher_name,
        leaderboard=leaderboard,
        active_page="leaderboard"
    )

# --------------------------
# Download Reports (CSV)
# --------------------------
@school_admin_bp.route("/download_report", methods=["GET"])
@login_required
@school_admin_required
def download_report():
    report_type = request.args.get("type")  # "exam" or "school"
    exam_id = request.args.get("exam_id")

    if report_type == "exam" and exam_id:
        file_path = generate_exam_report(int(exam_id))
    elif report_type == "school":
        file_path = generate_school_report(current_user.school_id)
    else:
        return "Invalid parameters", 400

    return send_file(file_path, as_attachment=True)


@school_admin_bp.route("/reports")
@login_required
@school_admin_required
def reports():
    school_id = current_user.school_id
    exams = ExamModel.get_exams_by_school(school_id)  # ✅ fixed
    return render_template("reports.html", exams=exams, active_page="reports")
