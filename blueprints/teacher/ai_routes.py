import os
from flask import render_template, request, redirect, url_for, session
from flask import current_app
from . import teacher_bp

from utils.ai.image_reader import extract_text
from utils.ai.ai_question_generator import generate_questions


# ============================
# AI GENERATE PAGE
# ============================

@teacher_bp.route("/exam/<int:exam_id>/ai_generate", methods=["GET", "POST"])
def ai_generate(exam_id):

    if request.method == "POST":

        file = request.files.get("file")
        text_input = request.form.get("text_input")

        num_questions = int(request.form.get("num_questions", 5))
        difficulty = request.form.get("difficulty", "Medium")

        marks = request.form.get("marks", 1)
        negative = request.form.get("negative", 0)

        text = ""

        # ============================
        # FILE UPLOAD
        # ============================

        if file and file.filename != "":

            upload_folder = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(upload_folder, exist_ok=True)

            path = os.path.join(upload_folder, file.filename)
            print("UPLOAD PATH:", path)
            file.save(path)

            text = extract_text(path)

        # ============================
        # TEXT INPUT
        # ============================

        elif text_input:
            text = text_input

        else:
            return "No input provided"

        # ============================
        # AI QUESTION GENERATION
        # ============================

        questions = generate_questions(text, num_questions, difficulty)

        session["ai_questions"] = questions
        session["exam_id"] = exam_id
        session["marks"] = marks
        session["negative"] = negative

        return redirect(url_for("teacher.ai_preview"))

    return render_template("ai_generate.html", exam_id=exam_id)


# ============================
# AI PREVIEW PAGE
# ============================

@teacher_bp.route("/ai_preview")
def ai_preview():

    questions = session.get("ai_questions", [])

    return render_template(
        "ai_preview.html",
        questions=questions
    )


# ============================
# SAVE QUESTION
# ============================

@teacher_bp.route("/save_ai_question/<int:index>")
def save_ai_question(index):

    from database import get_db_connection

    questions = session.get("ai_questions", [])

    if index >= len(questions):
        return "Invalid question"

    q = questions[index]

    exam_id = session["exam_id"]
    marks = session["marks"]
    negative = session["negative"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO questions
        (exam_id, question_text, option_a, option_b, option_c, option_d,
        correct_option, marks, negative_marks, ai_generated)

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    """, (
        exam_id,
        q["question"],
        q["option_a"],
        q["option_b"],
        q["option_c"],
        q["option_d"],
        q["correct_answer"],
        marks,
        negative
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("teacher.ai_preview"))


# ============================
# REGENERATE QUESTION
# ============================

@teacher_bp.route("/regenerate_question/<int:index>")
def regenerate_question(index):

    questions = session.get("ai_questions", [])

    if index >= len(questions):
        return redirect(url_for("teacher.ai_preview"))

    old_q = questions[index]

    new_q = generate_questions(old_q["question"], 1, "Medium")[0]

    questions[index] = new_q

    session["ai_questions"] = questions

    return redirect(url_for("teacher.ai_preview"))