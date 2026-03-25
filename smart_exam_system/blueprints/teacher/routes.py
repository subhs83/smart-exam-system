from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from smart_exam_system.utils.decorators import teacher_required, exam_owner_required
from smart_exam_system.utils.services.exam_service import create_exam, get_teacher_exams, publish_exam, delete_exam
from smart_exam_system.utils.services.question_service import upload_questions, get_exam_questions
from smart_exam_system.utils.services.result_service import get_results, generate_leaderboard
from smart_exam_system.blueprints.teacher import teacher_bp

# ---------------------------------
# Dashboard
# ---------------------------------
@teacher_bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():

    exams = get_teacher_exams(current_user.id)

    return render_template('teacher_dashboard.html', exams=exams,active_page='dashboard')


# ---------------------------------
# Create Exam
# ---------------------------------
@teacher_bp.route('/teacher/exams/create', methods=['GET', 'POST'])
@teacher_required
def create_exam_route():

    if request.method == 'POST':

        success, msg = create_exam(
            teacher_id=current_user.id,
            school_id=current_user.school_id,
            title=request.form.get('title'),
            duration=request.form.get('duration'),
            marks=request.form.get('marks'),
            negative=request.form.get('negative'),
            max_attempts=request.form.get('max_attempts')
        )

        flash(msg, 'success' if success else 'danger')
        return redirect(url_for('teacher.dashboard'))

    return render_template('exams_create.html',active_page='exams_create')


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

    return render_template('questions_upload.html', exam_id=exam_id,active_page='exams')


# ---------------------------------
# Review Questions (Read Only)
# ---------------------------------
@teacher_bp.route('/teacher/exams/<int:exam_id>/questions')
@teacher_required
@exam_owner_required
def review_questions_route(exam_id):
    questions = get_exam_questions(exam_id)
    return render_template('exam_review.html', exam_id=exam_id, questions=questions,active_page='exams')


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
    return render_template('results.html', exam_id=exam_id, results=results,active_page='exams')


# ---------------------------------
# Leaderboard
# ---------------------------------
@teacher_bp.route('/teacher/exams/<int:exam_id>/leaderboard')
@teacher_required
@exam_owner_required
def leaderboard_route(exam_id):
    leaderboard = generate_leaderboard(exam_id)
    print (leaderboard, "leaderboard")
    return render_template('leaderboard.html', exam_id=exam_id, leaderboard=leaderboard,active_page='exams')


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