from flask import render_template, session, redirect, url_for, request, flash,make_response
from smart_exam_system.blueprints.student import student_bp
from smart_exam_system.extensions import db
from smart_exam_system.utils.services.student_service import (
    get_exam_by_quiz_code,
    start_student_attempt,
    get_question_for_attempt,
    save_student_answer,
    get_exam_end_timestamp,
    is_exam_expired,
    get_total_questions,
    get_student_result,
    get_question_palette,
    record_violation,
)
from smart_exam_system.utils.helpers import no_cache
from smart_exam_system.models.attempt import AttemptModel
from smart_exam_system.models.exam import ExamModel
from datetime import datetime, timedelta


@student_bp.route("/quiz/<quiz_code>")
def quiz_page(quiz_code):
    print("FULL URL:", request.url)
    print("ARGS:", request.args)
    exam = get_exam_by_quiz_code(quiz_code)
    new_attempt = request.args.get("new_attempt")
    print("NEW ATTEMPT FLAG:", new_attempt)
    if not exam:
        flash("Invalid Quiz Link", "danger")
        return "Invalid Quiz Link"

    # -------------------------------
    # 🔹 Resolve student identity
    # -------------------------------
    student_mobile = session.get("student_mobile") or request.cookies.get("student_mobile")

    if not student_mobile:
        last_attempt = AttemptModel.query.filter_by(
            exam_id=exam.id,
            ip_address=request.remote_addr
        ).order_by(AttemptModel.id.desc()).first()

        if last_attempt:
            student_mobile = last_attempt.mobile
            session["student_mobile"] = student_mobile

    # -------------------------------
    # 🔹 Existing attempts check
    # -------------------------------
    if student_mobile:
        attempts = AttemptModel.query.filter_by(
            exam_id=exam.id,
            mobile=student_mobile,
            is_submitted=True
        ).order_by(AttemptModel.id.desc()).all()

        if attempts:
            last_attempt = attempts[0]
            max_attempts = exam.max_attempts_per_mobile or 1

            # -------------------------------
            # 🔹 If user wants new attempt
            # -------------------------------
            if new_attempt == "1":
                print("Creating new attempt...")
                if len(attempts) >= max_attempts:
                    return redirect(url_for(
                        "student.submit_quiz",
                        quiz_code=quiz_code,
                        attempt_id=last_attempt.id
                    ))

                attempt, error = start_student_attempt(
                    exam.id,
                    exam.school_id,
                    {
                        "first_name": last_attempt.first_name,
                        "last_name": last_attempt.last_name,
                        "mobile": last_attempt.mobile,
                        "student_class": last_attempt.student_class,
                        "roll_number": last_attempt.roll_number,
                    },
                    request.remote_addr
                )

                if attempt:
                    session["attempt_id"] = attempt.id
                    return redirect(url_for(
                        "student.quiz_question",
                        quiz_code=quiz_code,
                        q_index=0
                    ))

            # -------------------------------
            # 🔹 DEFAULT → ALWAYS SHOW RESULT
            # -------------------------------
            return redirect(url_for(
                "student.submit_quiz",
                quiz_code=quiz_code,
                attempt_id=last_attempt.id
            ))

    # -------------------------------
    # 🔹 Default: show registration form
    # -------------------------------
    used_attempts = AttemptModel.query.filter_by(
        exam_id=exam.id,
        mobile=student_mobile,
        is_submitted=True
    ).count()
    max_attempts = exam.max_attempts_per_mobile or 1
    return render_template(
    "student_register.html",
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
@student_bp.route("/quiz/<quiz_code>/start", methods=["POST"])
def start_quiz(quiz_code):

    exam = ExamModel.query.filter_by(quiz_code=quiz_code).first()

    if not exam:
        flash("Invalid quiz link", "danger")
        return redirect(url_for("student.quiz_page", quiz_code=quiz_code))

    attempt, error = start_student_attempt(
        exam.id,
        exam.school_id,
        request.form,
        request.remote_addr
    )

    if error:
        flash(error, "danger")
        return redirect(url_for("student.quiz_page", quiz_code=quiz_code))

    response = make_response(redirect(url_for(
        "student.quiz_question",
        quiz_code=quiz_code,
        q_index=0
    )))

    session["attempt_id"] = attempt.id
    session["student_mobile"] = attempt.mobile

    # ✅ Persist identity (important)
    response.set_cookie(
        "student_mobile",
        attempt.mobile,
        max_age=30 * 24 * 60 * 60
    )

    return response


@student_bp.route("/quiz/<quiz_code>/<int:q_index>", methods=["GET", "POST"])
def quiz_question(quiz_code, q_index):

    # -------------------------------
    # 🔹 Get attempt safely
    # -------------------------------
    attempt_id = session.get("attempt_id") or request.args.get("attempt_id")

    if not attempt_id:
        return redirect(url_for("student.quiz_page", quiz_code=quiz_code))

    # ✅ Convert to int safely
    try:
        attempt_id = int(attempt_id)
    except (TypeError, ValueError):
        return redirect(url_for("student.quiz_page", quiz_code=quiz_code))

    attempt = AttemptModel.query.get(attempt_id)

    if not attempt:
        return redirect(url_for("student.quiz_page", quiz_code=quiz_code))

    # -------------------------------
    # 🔹 Prevent answering after submit
    # -------------------------------
    if attempt.is_submitted:
        return redirect(url_for(
            "student.submit_quiz",
            quiz_code=quiz_code,
            attempt_id=attempt.id
        ))

    exam = attempt.exam

    # -------------------------------
    # 🔹 Time check
    # -------------------------------
    end_time = attempt.start_time + timedelta(minutes=exam.duration_minutes)
    remaining_time = int((end_time - datetime.utcnow()).total_seconds())

    if remaining_time <= 0:
        return redirect(url_for("student.submit_quiz", quiz_code=quiz_code,attempt_id=attempt.id))

    # -------------------------------
    # 🔹 Question order & index safety
    # -------------------------------
    import json
    question_order = json.loads(attempt.question_order)
    total_questions = len(question_order)

    if q_index < 0:
        q_index = 0

    if q_index >= total_questions:
        return redirect(url_for("student.submit_quiz", quiz_code=quiz_code,attempt_id=attempt.id))

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
        goto_index = request.form.get("goto")
        if goto_index is not None:
            return redirect(url_for(
                "student.quiz_question",
                quiz_code=quiz_code,
                q_index=int(goto_index)
            ))
        # ✅ Navigation buttons only
        if "next" in request.form:
            return redirect(url_for(
                "student.quiz_question",
                quiz_code=quiz_code,
                q_index=min(q_index + 1, total_questions - 1)
            ))

        elif "prev" in request.form:
            return redirect(url_for(
                "student.quiz_question",
                quiz_code=quiz_code,
                q_index=max(q_index - 1, 0)
            ))

        elif "submit" in request.form:
            return redirect(url_for(
                "student.submit_quiz",
                quiz_code=quiz_code,
                attempt_id=attempt.id
            ))

    # -------------------------------
    # 🔹 GET: Load question + palette
    # -------------------------------
    question = get_question_for_attempt(attempt_id, q_index)
    palette = get_question_palette(attempt_id, exam.id)

    if not question:
        return redirect(url_for("student.submit_quiz", quiz_code=quiz_code,attempt_id=attempt.id))

    response = make_response(render_template(
        "student_quiz.html",
        question=question,
        q_index=q_index,
        palette=palette,
        total_questions=total_questions,
        remaining_time=remaining_time,
        exam=exam,
        hide_nav=True,
        hide_footer=True,
        hide_sidebar=True
    ))
    return no_cache(response)
# -----------------------------
# Submit Quiz
# -----------------------------
@student_bp.route("/quiz/<quiz_code>/submit", methods=["GET", "POST"])
def submit_quiz(quiz_code):

    attempt_id = request.args.get("attempt_id") or session.get("attempt_id")

    if not attempt_id:
        flash("No active attempt found", "danger")
        return redirect(url_for("student.quiz_page", quiz_code=quiz_code))

    try:
        attempt_id = int(attempt_id)
    except (TypeError, ValueError):
        flash("Invalid attempt ID", "danger")
        return redirect(url_for("student.quiz_page", quiz_code=quiz_code))

    attempt = AttemptModel.query.get(attempt_id)
    if not attempt:
        flash("Attempt not found", "danger")
        return redirect(url_for("student.quiz_page", quiz_code=quiz_code))

    if attempt.is_submitted:
        flash("This attempt has already been submitted.", "warning")
        result = get_student_result(attempt_id)

        used_attempts = AttemptModel.query.filter_by(
            exam_id=attempt.exam_id,
            mobile=attempt.mobile,
            is_submitted=True
        ).count()

        max_attempts = attempt.exam.max_attempts_per_mobile or 1

        return render_template(
            "student_result.html",
            **result,
            used_attempts=used_attempts,
            max_attempts=max_attempts
        )

    if attempt.violation_count >= 2:
        attempt.auto_submitted_reason = "Tab switch / DevTools / App switch detected"

    result = get_student_result(attempt_id)

    session.pop("attempt_id", None)
    used_attempts = AttemptModel.query.filter_by(
        exam_id=attempt.exam_id,
        mobile=attempt.mobile,
        is_submitted=True
    ).count()

    max_attempts = attempt.exam.max_attempts_per_mobile or 1
    return render_template(
    "student_result.html",
    **result,
    used_attempts=used_attempts,
    max_attempts=max_attempts
)

    # -------------------------------
    # Save Violation
    # -------------------------------

# ---------------------------------
# Save Violation (FINAL CLEAN)
# ---------------------------------
@student_bp.route("/quiz/save-violation", methods=["POST"])
def save_violation():

    attempt_id = session.get("attempt_id")

    if not attempt_id:
        return {"status": "error"}, 400

    data = request.get_json() or {}
    reason = data.get("reason", "Unknown")

    result = record_violation(attempt_id, reason)
    print("Violation API HIT")
    return result
# -----------------------------
# Auto Save Answer (AJAX)
# -----------------------------
@student_bp.route("/save-answer", methods=["POST"])
def save_answer_ajax():

    attempt_id = session.get("attempt_id")
    if not attempt_id:
        return {"status": "error"}

    attempt = AttemptModel.query.get(attempt_id)
    if not attempt:
        return {"status": "error"}

    # 🔒 Block if already submitted
    if attempt.is_submitted:
        return {"status": "blocked"}

    # ⏱️ Time check (backend safety)
    exam = attempt.exam
    end_time = attempt.start_time + timedelta(minutes=exam.duration_minutes)

    if datetime.utcnow() > end_time:
        return {"status": "expired"}

    question_id = request.form.get("question_id")
    selected_option = request.form.get("option")

    save_student_answer(attempt_id, question_id, selected_option)

    return {"status": "saved"}