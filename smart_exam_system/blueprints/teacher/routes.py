from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from smart_exam_system.utils.decorators import teacher_required, exam_owner_required
from smart_exam_system.utils.services.exam_service import ( 
    create_exam, 
    get_teacher_exams, 
    publish_exam, 
    delete_exam,
    parse_exam_datetime,
    extract_exam_form_data
    )
from smart_exam_system.utils.services.question_service import upload_questions, get_exam_questions
from smart_exam_system.utils.services.result_service import(
    generate_leaderboard,
    get_attempt_detailed_report,
    get_student_attempts,
    get_best_attempt_id,
    build_student_summary
)
from smart_exam_system.models.attempt import AttemptModel
from smart_exam_system.models.school import SchoolModel
from smart_exam_system.blueprints.teacher import teacher_bp
from datetime import datetime,timezone

# ---------------------------------
# Dashboard
# ---------------------------------
@teacher_bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():

    exams = get_teacher_exams(current_user.id)
    school = SchoolModel.query.get(current_user.school_id)  # or however you get the teacher's school
    return render_template('teacher_dashboard.html', school_slug=school.slug,exams=exams,active_page='dashboard')


# ---------------------------------
# Create Exam
# ---------------------------------


@teacher_bp.route('/teacher/exams/create', methods=['GET', 'POST'])
@teacher_required
def create_exam_route():

    if request.method == 'POST':

        exam_data = extract_exam_form_data(request.form  )

        success, msg = create_exam(
            teacher_id=current_user.id,
            school_id=current_user.school_id,
            **exam_data
        )

        flash(msg, 'success' if success else 'danger')
        return redirect(url_for('teacher.dashboard'))

    return render_template('exams_create.html', active_page='exams_create')


# ---------------------------------
# Upload Questions (Excel)
# ---------------------------------
@teacher_bp.route('/teacher/exams/<int:exam_id>/questions/upload', methods=['GET', 'POST'])
@teacher_required
@exam_owner_required
def upload_questions_route(exam_id):

    if request.method == 'POST':
        excel_file = request.files.get('excel_file')
        if not excel_file:
            flash("Please upload an Excel file.", "danger")
            return redirect(request.url)

        success, msg = upload_questions(exam_id, excel_file)
        flash(msg, 'success' if success else 'danger')
        
        return redirect(url_for('teacher.review_questions_route', exam_id=exam_id))

    return render_template('questions_upload.html', exam_id=exam_id,active_page='manage_questions')


# ---------------------------------
# Review Questions (Read Only)
# ---------------------------------
@teacher_bp.route('/teacher/exams/<int:exam_id>/questions')
@teacher_required
@exam_owner_required
def review_questions_route(exam_id):
    questions = get_exam_questions(exam_id)
    return render_template('exam_review.html', exam_id=exam_id, questions=questions,active_page='manage_questions')


# ---------------------------------
# Publish Exam
# ---------------------------------
@teacher_bp.route('/teacher/exams/<int:exam_id>/publish', methods=['POST'])
@teacher_required
def publish_exam_route(exam_id):

    success, result = publish_exam(exam_id)

    if not success:
        flash(result, "danger")
    else:
        flash(f"Exam Published! Quiz Code: {result}", "success")

    return redirect(url_for("teacher.dashboard"))


# ---------------------------------
# View Results
# ---------------------------------
@teacher_bp.route('/teacher/exams/<int:exam_id>/results')
@teacher_required
@exam_owner_required
def results_route(exam_id):
    results = get_results(exam_id)
    return render_template('results.html', exam_id=exam_id, results=results,active_page='results_overview')


# ---------------------------------
# Leaderboard
# ---------------------------------
@teacher_bp.route('/teacher/exams/<int:exam_id>/leaderboard')
@teacher_required
@exam_owner_required
def leaderboard_route(exam_id):
    leaderboard = generate_leaderboard(exam_id)
    print (leaderboard, "leaderboard")
    return render_template('leaderboard.html', exam_id=exam_id, leaderboard=leaderboard,active_page='leaderboard_overview')


# ---------------------------------
# Delete Exam (only if no attempts)
# ---------------------------------
@teacher_bp.route('/teacher/exams/<int:exam_id>/delete', methods=['POST'])
@teacher_required
@exam_owner_required
def delete_exam_route(exam_id):
    success, msg = delete_exam(exam_id)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('teacher.dashboard'))

# ---------------------------------
# Student Attempt Overview
# ---------------------------------
@teacher_bp.route('/teacher/student/<string:mobile>/<string:roll>/<int:exam_id>')
@teacher_required
def student_attempts(mobile, roll, exam_id):

    attempts = get_student_attempts(mobile, roll, exam_id)

    if not attempts:
        flash("No attempts found", "danger")
        return redirect(url_for('teacher.results_route', exam_id=exam_id))
    # find best attempt
    best_attempt_id = get_best_attempt_id(attempts)
    return render_template(
        "student_attempts.html",
        attempts=attempts,
        exam_id=exam_id,
        best_attempt_id=best_attempt_id,
        student=build_student_summary(attempts),
        active_page="results_overview"
    )    

# ---------------------------------
# Detailed Student Report)
# ---------------------------------

@teacher_bp.route('/teacher/attempt/<int:attempt_id>')
@teacher_required
def attempt_detail(attempt_id):
    report = get_attempt_detailed_report(attempt_id)
    attempt = AttemptModel.query.get(attempt_id)
    exam_id = attempt.exam_id   # ✅ get from DB
    if not report:
        flash("Attempt not found", "danger")
        return redirect(url_for('teacher.results_overview'))

    return render_template(
        'attempt_detail.html',
        report=report,
         exam_id=exam_id,
        active_page='results_overview'
    )

# Sidebar Link Routes

# ---------------------------------
# Manage Questions Overview
# ---------------------------------
@teacher_bp.route('/teacher/manage_questions')
@teacher_required
def manage_questions_overview():
    exams = get_teacher_exams(current_user.id)
    return render_template(
        'manage_questions_overview.html',
        exams=exams,
        active_page='manage_questions'
    )


# ---------------------------------
# Results Overview
# ---------------------------------
@teacher_bp.route('/teacher/results')
@teacher_required
def results_overview():
    exams = get_teacher_exams(current_user.id)
    return render_template(
        'results_overview.html',
        exams=exams,
        active_page='results_overview'
    )


# ---------------------------------
# Leaderboard Overview
# ---------------------------------
@teacher_bp.route('/teacher/leaderboard')
@teacher_required
def leaderboard_overview():
    exams = get_teacher_exams(current_user.id)
    return render_template(
        'leaderboard_overview.html',
        exams=exams,
        active_page='leaderboard_overview'
    )