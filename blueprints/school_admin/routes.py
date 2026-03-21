from . import school_admin_bp
from flask import render_template, redirect, url_for, flash, abort, Response, request,session
from flask_login import login_required, current_user
from utils.decorators import school_admin_required
from models.user import User
from models.exam import Exam
from models.result import Result
from models.attempt import Attempt
from utils.services.result_service import get_results, generate_leaderboard

from database import get_db
from forms.teacher_forms import AddTeacherForm
import io, csv
from utils.security import hash_password, verify_password


# --------------------------
# Dashboard
# --------------------------
@school_admin_bp.route("/dashboard")
@login_required
@school_admin_required
def dashboard():
    school_id = current_user.school_id

    total_teachers = User.count_teachers_by_school_sa(school_id)
    total_exams = Exam.count_by_school(school_id)
    total_attempts = Attempt.count_by_school(school_id)

    return render_template(
        "school_admin_dashboard.html",
        total_teachers=total_teachers,
        total_exams=total_exams,
        total_attempts=total_attempts,
        active_page="dashboard"
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
        teacher = User.add_teacher_sa(
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

    return render_template("add_teacher.html", form=form)

# --------------------------
# View Teachers
# --------------------------
@school_admin_bp.route("/view_teachers")
@login_required
@school_admin_required
def view_teachers():
    conn = get_db()
    teachers = conn.execute(
        "SELECT * FROM users WHERE role = 'teacher' AND school_id = ?",
        (current_user.school_id,)
    ).fetchall()
    conn.close()
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
    success = User.toggle_teacher_status_sa(
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
    User.reset_teacher_password(teacher_id, current_user.school_id)
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
    teachers = User.get_teachers_by_school_sa(school_id)
    return render_template(
        'teachers.html',
        teachers=teachers,
       active_page="exams"
    )
# --------------------------
# View Exams
# --------------------------
 
@school_admin_bp.route('/teacher/<int:teacher_id>/exams')
def teacher_exams(teacher_id):
    exams = Exam.get_exams_by_teacher(teacher_id)
    exam_list = []
    for exam in exams:
        attempts = Attempt.get_attempt_count(exam["id"])
        exam_list.append({
            "id": exam["id"],
            "title": exam["title"],
            "student_attempts": attempts
        })
 
    return render_template(
        "teacher_exams.html",
        exams=exam_list,
        active_page="exams"
    )
# ---------------------------------
# School Admin - Exam Results
# ---------------------------------
@school_admin_bp.route('/school_admin/exams/<int:exam_id>/results')
@school_admin_required
def admin_exam_results(exam_id):
    results = get_results(exam_id)
    # get teacher id from exam
    teacher_id = Exam.get_teacher_id_by_exam(exam_id)
    exam_info = Exam.get_exam_info(exam_id)
    exam_title = exam_info[0]
    teacher_name = exam_info[1]
    return render_template(
        'school_admin_results.html',
        exam_id=exam_id,
        results=results,
        teacher_id=teacher_id,
        exam_title = exam_title,
        teacher_name = teacher_name,
    )
# --------------------------
# Leaderboard
# --------------------------
# ---------------------------------
# School Admin - Leaderboard
# ---------------------------------
@school_admin_bp.route('/school-admin/exams/<int:exam_id>/leaderboard')
@school_admin_required
def admin_exam_leaderboard(exam_id):

    leaderboard = generate_leaderboard(exam_id)
     # get teacher id from exam
    teacher_id = Exam.get_teacher_id_by_exam(exam_id)

    exam_info = Exam.get_exam_info(exam_id)
    exam_title = exam_info[0]
    teacher_name = exam_info[1]
    return render_template(
        'school_admin_leaderboard.html',
        exam_id=exam_id,
        teacher_id=teacher_id,
        exam_title = exam_title,
        teacher_name = teacher_name,
        leaderboard=leaderboard
    )

# --------------------------
# Download Reports (CSV)
# --------------------------
@school_admin_bp.route("/download_reports")
@login_required
@school_admin_required
def download_reports():
    results = Result.get_by_school(current_user.school_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student", "Exam", "Score"])
    for r in results:
        writer.writerow([r["student_name"], r["exam_name"], r["score"]])
    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=school_reports.csv"
    return response