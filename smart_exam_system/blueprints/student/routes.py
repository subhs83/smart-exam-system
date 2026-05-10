from flask import render_template, session, redirect, url_for, request, flash,make_response
from smart_exam_system.blueprints.student import student_bp
from smart_exam_system.extensions import db
from smart_exam_system.utils.services.student_service import (
    get_exam_by_quiz_code,
    start_student_attempt,
    get_question_for_attempt,
    save_student_answer,
    get_student_result,
    get_question_palette,
    record_violation,
    get_submitted_attempts,
    resolve_student_mobile,
    create_retry_attempt,
    get_attempt_state,
    persist_student_identity,
    extract_student_form_data,
    resolve_attempt,
    calculate_remaining_time,
    normalize_question_index,
    resolve_quiz_navigation_action,
    get_attempt_question_order,
    get_used_attempt_count,
    get_max_attempts
)
from smart_exam_system.utils.services.school_service import get_school_or_404
from smart_exam_system.utils.helpers import no_cache
from smart_exam_system.models.attempt import AttemptModel
from smart_exam_system.models.exam import ExamModel
from smart_exam_system.models.school import SchoolModel
from datetime import datetime, timedelta


@student_bp.route("/<school_slug>/quiz/<quiz_code>")
def quiz_page(school_slug, quiz_code):
    school = get_school_or_404(school_slug)
    exam = get_exam_by_quiz_code(quiz_code)

    new_attempt = request.args.get("new_attempt")

    if not exam:
        flash("Invalid Quiz Link", "danger")
        return "Invalid Quiz Link"

    # -------------------------------
    # 🔹 Resolve student identity
    # -------------------------------
    student_mobile = resolve_student_mobile( exam.id, request.remote_addr)

    # -------------------------------
    # 🔹 Existing attempts check
    # -------------------------------
    if student_mobile:
        attempts = get_submitted_attempts(exam.id, student_mobile)

        attempt_state = get_attempt_state(exam, attempts)

        if attempt_state["has_attempts"]:

            last_attempt = attempt_state["latest_attempt"]

            # -------------------------------
            # 🔹 If user wants new attempt
            # -------------------------------
            if new_attempt == "1":

                if not attempt_state["can_retry"]:
                    return redirect(url_for(
                        "student.submit_quiz",
                        school_slug=school_slug,
                        quiz_code=quiz_code,
                        attempt_id=last_attempt.id
                    ))

                attempt, error = create_retry_attempt(
                    exam,
                    last_attempt,
                    request.remote_addr
                )

                if attempt:
                    session["attempt_id"] = attempt.id

                    return redirect(url_for(
                        "student.quiz_question",
                        school_slug=school_slug,
                        quiz_code=quiz_code,
                        q_index=0,
                        hide_nav=True,
                        hide_footer=True,
                        hide_sidebar=True
                    ))

            # -------------------------------
            # 🔹 DEFAULT → ALWAYS SHOW RESULT
            # -------------------------------
            return redirect(url_for(
                "student.submit_quiz",
                school_slug=school_slug,
                quiz_code=quiz_code,
                attempt_id=last_attempt.id
            ))

    # -------------------------------
    # 🔹 Default: show registration form
    # -------------------------------
    used_attempts = len(get_submitted_attempts(exam.id, student_mobile))
    max_attempts = exam.max_attempts_per_mobile or 1
    return render_template(
    "student_register.html",
    school_slug=school_slug,
    quiz_code=quiz_code,
    exam=exam,
    used_attempts=used_attempts,
    max_attempts=max_attempts,
    hide_nav=True,
    hide_footer=True,
    hide_sidebar=True
)


# -----------------------------
# Start Quiz
# -----------------------------
@student_bp.route("/<school_slug>/quiz/<quiz_code>/start", methods=["POST"])
def start_quiz(school_slug,quiz_code):
    school = get_school_or_404(school_slug)

    exam = get_exam_by_quiz_code(quiz_code)
    if not exam:
        flash("Invalid quiz link", "danger")
        return redirect(url_for("student.quiz_page", school_slug=school_slug,quiz_code=quiz_code))

    student_data = extract_student_form_data(request.form)

    attempt, error = start_student_attempt(
        exam.id,
        exam.school_id,
        student_data,
        request.remote_addr
    )

    if error:
        flash(error, "danger")
        return redirect(url_for("student.quiz_page", school_slug=school_slug,quiz_code=quiz_code))

    response = make_response(redirect(url_for(
        "student.quiz_question",
        quiz_code=quiz_code,
        school_slug=school_slug,
        q_index=0
    )))

    response = persist_student_identity(response,attempt)

    return response

# -----------------------------
# Quiz Page
# -----------------------------
@student_bp.route("/<school_slug>/quiz/<quiz_code>/<int:q_index>", methods=["GET", "POST"])
def quiz_question(school_slug, quiz_code, q_index):
    school = get_school_or_404(school_slug)

    # -------------------------------
    # 🔹 Get attempt safely
    # -------------------------------
    attempt_id = (
        session.get("attempt_id")
        or request.args.get("attempt_id")
    )

    attempt = resolve_attempt(attempt_id)

    if not attempt:
        return redirect(url_for(
            "student.quiz_page",
            school_slug=school_slug,
            quiz_code=quiz_code
        ))

    # -------------------------------
    # 🔹 Prevent answering after submit
    # -------------------------------
    if attempt.is_submitted:
        return redirect(url_for(
            "student.submit_quiz",
            school_slug=school_slug,
            quiz_code=quiz_code,
            attempt_id=attempt.id
        ))

    exam = attempt.exam

    # -------------------------------
    # 🔹 Time check
    # -------------------------------
    remaining_time = calculate_remaining_time(attempt, exam )

    if remaining_time <= 0:
        return redirect(url_for(
            "student.submit_quiz",
            school_slug=school_slug,
            quiz_code=quiz_code,
            attempt_id=attempt.id
        ))

    # -------------------------------
    # 🔹 Question order & index safety
    # -------------------------------
    question_data = get_attempt_question_order( attempt)

    question_order = question_data["question_order"]
    total_questions = question_data["total_questions"]

    q_index = normalize_question_index( q_index, total_questions )

    if q_index is None:
        return redirect(url_for(
            "student.submit_quiz",
            school_slug=school_slug,
            quiz_code=quiz_code,
            attempt_id=attempt.id
        ))

    # -------------------------------
    # 🔹 POST: Save answer + navigation
    # -------------------------------
    if request.method == "POST":

        question_id = request.form.get("question_id")
        selected_option = request.form.get("option")

        # ✅ Save answer
        if question_id and selected_option:
            save_student_answer(attempt_id, question_id, selected_option)
        # 🔥 NEW: palette navigation
        navigation = resolve_quiz_navigation_action(request.form)

        if navigation["action"] == "goto":

            return redirect(url_for(
                "student.quiz_question",
                school_slug=school_slug,
                quiz_code=quiz_code,
                q_index=navigation["target_index"]
            ))

        if navigation["action"] == "next":

            return redirect(url_for(
                "student.quiz_question",
                school_slug=school_slug,
                quiz_code=quiz_code,
                q_index=min(q_index + 1, total_questions - 1)
            ))

        elif navigation["action"] == "prev":

            return redirect(url_for(
                "student.quiz_question",
                school_slug=school_slug,
                quiz_code=quiz_code,
                q_index=max(q_index - 1, 0)
            ))

        elif navigation["action"] == "submit":

            return redirect(url_for(
                "student.submit_quiz",
                school_slug=school_slug,
                quiz_code=quiz_code,
                attempt_id=attempt.id
            ))

    # -------------------------------
    # 🔹 GET: Load question + palette
    # -------------------------------
    question = get_question_for_attempt(attempt_id, q_index)
    palette = get_question_palette(attempt_id, exam.id)

    if not question:
        return redirect(url_for("student.submit_quiz", school_slug=school_slug,quiz_code=quiz_code,attempt_id=attempt.id))

    response = make_response(render_template(
        "student_quiz.html",
        question=question,
        q_index=q_index,
        palette=palette,
        total_questions=total_questions,
        remaining_time=remaining_time,
        exam=exam,
        school_slug=school_slug,   # 🔹 add this
        quiz_code=quiz_code,       # 🔹 add this
        hide_nav=True,
        hide_footer=True,
        hide_sidebar=True
    ))
    return no_cache(response)
# -----------------------------
# Submit Quiz
# -----------------------------
@student_bp.route("/<school_slug>/quiz/<quiz_code>/submit", methods=["GET", "POST"])
def submit_quiz(school_slug, quiz_code):
     # ✅ Resolve school from slug
    school = get_school_or_404(school_slug)
    attempt_id = ( request.args.get("attempt_id") or session.get("attempt_id") )

    attempt = resolve_attempt(attempt_id)

    if not attempt:
        flash("Attempt not found", "danger")
        return redirect(url_for(
            "student.quiz_page",
            school_slug=school_slug,
            quiz_code=quiz_code
        ))

    if attempt.is_submitted:
        result = get_student_result(attempt_id)

        used_attempts = get_used_attempt_count(attempt.exam_id,attempt.mobile)

        max_attempts = get_max_attempts(attempt.exam)

        return render_template(
            "student_result.html",
            **result,
            used_attempts=used_attempts,
            max_attempts=max_attempts,
            school_slug=school_slug,   # ✅ add this
            hide_nav=True,
            hide_footer=True,
        )

    if attempt.violation_count >= 2:
        attempt.auto_submitted_reason = "Tab switch / DevTools / App switch detected"

    result = get_student_result(attempt_id)

    session.pop("attempt_id", None)
    used_attempts = get_used_attempt_count(attempt.exam_id,attempt.mobile)

    max_attempts = get_max_attempts(attempt.exam)
    return render_template(
    "student_result.html",
    **result,
    used_attempts=used_attempts,
    max_attempts=max_attempts,
    school_slug=school_slug,   # ✅ add this
    hide_nav=True,
    hide_footer=True,
)

# ---------------------------------
# Save Violation (with slug + quiz_code)
# ---------------------------------
@student_bp.route("/<school_slug>/quiz/<quiz_code>/save-violation", methods=["POST"])
def save_violation(school_slug, quiz_code):
    attempt_id = session.get("attempt_id")

    if not attempt_id:
        return {"status": "error"}, 400

    data = request.get_json() or {}
    reason = data.get("reason", "Unknown")

    result = record_violation(attempt_id, reason)
    print(f"Violation API HIT for {school_slug}/{quiz_code}")
    return result

# -----------------------------
# Auto Save Answer (AJAX)
# -----------------------------
@student_bp.route("/save-answer", methods=["POST"])
def save_answer_ajax():

    attempt_id = session.get("attempt_id")
    if not attempt_id:
        return {"status": "error"}

    attempt = resolve_attempt(attempt_id)

    if not attempt:
        return {"status": "error"}

    # 🔒 Block if already submitted
    if attempt.is_submitted:
        return {"status": "blocked"}

    # ⏱️ Time check (backend safety)
    remaining_time = calculate_remaining_time(attempt, attempt.exam)

    if remaining_time <= 0:
        return {"status": "expired"}

    question_id = request.form.get("question_id")
    selected_option = request.form.get("option")

    save_student_answer(attempt_id, question_id, selected_option)

    return {"status": "saved"}