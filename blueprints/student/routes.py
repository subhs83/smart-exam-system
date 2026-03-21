from flask import render_template, session, redirect, url_for,request,flash
from . import student_bp
from database import get_db
from datetime import datetime, timedelta,timezone
from utils.services.student_service import(
    get_exam_by_quiz_code,
    start_student_attempt,
    get_question_for_attempt,
    save_student_answer,
    get_exam_end_timestamp, 
    is_exam_expired,
    get_total_questions,
    get_student_score,
    finalize_attempt,
    get_question_palette,
    get_student_result,)


# -----------------------------
# Registration / Quiz Start Page
# -----------------------------
@student_bp.route("/quiz/<quiz_code>")
def quiz_page(quiz_code):
    exam = get_exam_by_quiz_code(quiz_code)
    if not exam:
        flash("Invalid Quiz Link", "danger")
        return "Invalid Quiz Link"

    return render_template(
        "student_register.html",
        quiz_code=quiz_code,
        exam=exam
    )


# -----------------------------
# Start Quiz (POST Registration)
# -----------------------------
@student_bp.route("/quiz/<quiz_code>/start", methods=["POST"])
def start_quiz(quiz_code):

    success, result = start_student_attempt(
        quiz_code,
        request.form,
        request.remote_addr
    )

    if not success:
        flash(result, "danger")
        return redirect(url_for("student.quiz_page", quiz_code=quiz_code))

    session["attempt_id"] = result

    return redirect(url_for(
        "student.quiz_question",
        quiz_code=quiz_code,
        q_index=0
    ))


# -----------------------------
# Quiz Question Page
# -----------------------------
@student_bp.route("/quiz/<quiz_code>/<int:q_index>", methods=["GET", "POST"])
def quiz_question(quiz_code, q_index):

    if "attempt_id" not in session:
        return redirect(url_for("student.quiz_page", quiz_code=quiz_code))

    attempt_id = session["attempt_id"]
    db = get_db()
    cursor = db.cursor()

    end_timestamp, end_time = get_exam_end_timestamp(attempt_id)

    if is_exam_expired(end_time):
        return redirect(url_for("student.submit_quiz", quiz_code=quiz_code))
    
    if request.method == "POST":

        question_id = request.form.get("question_id")
        selected_option = request.form.get("option")

        if question_id:
            save_student_answer(attempt_id, question_id, selected_option)

        # palette navigation
        if request.form.get("goto_question"):
            goto_index = int(request.form.get("goto_question"))
            return redirect(url_for("student.quiz_question",
                                    quiz_code=quiz_code,
                                    q_index=goto_index))

        if "next" in request.form:
            return redirect(url_for("student.quiz_question",
                                    quiz_code=quiz_code,
                                    q_index=q_index + 1))

        elif "prev" in request.form:
            return redirect(url_for("student.quiz_question",
                                    quiz_code=quiz_code,
                                    q_index=max(q_index - 1, 0)))

        elif "submit" in request.form or "auto_submit" in request.form:
            return redirect(url_for("student.submit_quiz",
                                    quiz_code=quiz_code))
        # Get current question
    # get exam_id
    cursor.execute("SELECT exam_id FROM student_attempts WHERE id=?", (attempt_id,))
    exam_id = cursor.fetchone()["exam_id"]

    total_questions = get_total_questions(exam_id)
    question = get_question_for_attempt(attempt_id, q_index)
    palette = get_question_palette(attempt_id, exam_id)
    if not question:
        return redirect(url_for("student.submit_quiz", quiz_code=quiz_code))
    return render_template(
        "student_quiz.html",
        question=question,
        q_index=q_index,
        palette=palette,
        total_questions = total_questions,
        end_timestamp=end_timestamp
       
        

    )


# -----------------------------
# Submit Quiz
# -----------------------------

@student_bp.route("/quiz/<quiz_code>/submit", methods=["GET", "POST"])
def submit_quiz(quiz_code):

    attempt_id = session.get("attempt_id")

    if not attempt_id:
        flash("No active attempt found", "danger")
        return redirect(url_for("student.quiz_page", quiz_code=quiz_code))

    result = get_student_result(attempt_id)

    session.pop("attempt_id", None)

    return render_template(
        "student_result.html",
        **result
    )

    # -----------------------------
# Auto Save Answer (AJAX)
# -----------------------------
@student_bp.route("/save-answer", methods=["POST"])
def save_answer_ajax():

    attempt_id = session.get("attempt_id")
    if not attempt_id:
        return {"status": "error"}

    question_id = request.form.get("question_id")
    selected_option = request.form.get("option")

    save_student_answer(attempt_id, question_id, selected_option)

    return {"status": "saved"}