from flask import render_template, abort, request, redirect, url_for, flash
from flask_login import login_required, current_user
from utils.decorators import super_admin_required
from . import super_admin_bp
from database import get_db
import secrets
import string
from utils.security import hash_password, verify_password
from flask import flash
# =========================
# DASHBOARD
# =========================
@super_admin_bp.route("/dashboard")
@login_required
@super_admin_required
def dashboard():
    if current_user.role != "super_admin":
        abort(403)

    conn = get_db()
    cursor = conn.cursor()

    # Total Schools
    cursor.execute("SELECT COUNT(*) FROM schools")
    total_schools = cursor.fetchone()[0]

    # Total Exams
    cursor.execute("SELECT COUNT(*) FROM exams")
    total_exams = cursor.fetchone()[0]

    # Total Teachers
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'teacher'")
    total_teachers = cursor.fetchone()[0]

    # Total Students (based on results)
    cursor.execute("SELECT COUNT(DISTINCT mobile) FROM results")
    total_students = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "super_admin_dashboard.html",
        total_schools=total_schools,
        total_exams=total_exams,
        total_teachers=total_teachers,
        total_students=total_students
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

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM schools ORDER BY id ASC")
    schools = cursor.fetchall()

    conn.close()

    return render_template("schools.html", schools=schools)


# =========================
# ADD SCHOOL
# =========================
@super_admin_bp.route("/schools/add", methods=["GET", "POST"])
@login_required
@super_admin_required
def add_school():

    if current_user.role != "super_admin":
        abort(403)

    if request.method == "POST":

        name = request.form["name"].strip()
        address = request.form["address"].strip()
        phone = request.form["phone"].strip()
        email = request.form["email"].strip()

        # Basic validation
        if not name:
            flash("School name is required.", "danger")
            return redirect(url_for("super_admin.add_school"))

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO schools (name, address, phone, email)
            VALUES (?, ?, ?, ?)
        """, (name, address, phone, email))

        conn.commit()
        conn.close()

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

    if current_user.role != "super_admin":
        abort(403)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM schools WHERE id = ?", (school_id,))
    school = cursor.fetchone()

    if not school:
        conn.close()
        abort(404)

    if request.method == "POST":

        name = request.form["name"].strip()
        address = request.form["address"].strip()
        phone = request.form["phone"].strip()
        email = request.form["email"].strip()

        if not name:
            flash("School name is required.", "danger")
            return redirect(url_for("super_admin.edit_school", school_id=school_id))

        cursor.execute("""
            UPDATE schools
            SET name = ?, address = ?, phone = ?, email = ?
            WHERE id = ?
        """, (name, address, phone, email, school_id))

        conn.commit()
        conn.close()

        flash("School updated successfully!", "success")
        return redirect(url_for("super_admin.schools"))

    conn.close()
    return render_template("edit_school.html", school=school)


# =========================
# TOGGLE SCHOOL STATUS (POST ONLY)
# =========================
@super_admin_bp.route("/schools/toggle/<int:school_id>", methods=["POST"])
@login_required
@super_admin_required
def toggle_school(school_id):

    if current_user.role != "super_admin":
        abort(403)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT is_active FROM schools WHERE id = ?", (school_id,))
    school = cursor.fetchone()

    if school:
        new_status = 0 if school["is_active"] == 1 else 1
        cursor.execute(
            "UPDATE schools SET is_active = ? WHERE id = ?",
            (new_status, school_id)
        )
        conn.commit()

    conn.close()
    return redirect(url_for("super_admin.schools"))

 # =========================
# View School Admins
# =========================   

@super_admin_bp.route("/schools/<int:school_id>/admins")
@login_required
@super_admin_required
def view_school_admins(school_id):

    if current_user.role != "super_admin":
        abort(403)

    conn = get_db()
    cursor = conn.cursor()

    # Get School
    cursor.execute("SELECT * FROM schools WHERE id = ?", (school_id,))
    school = cursor.fetchone()

    if not school:
        conn.close()
        abort(404)

    # Get School Admins
    cursor.execute("""
        SELECT * FROM users
        WHERE role = 'school_admin' AND school_id = ?
        ORDER BY id ASC
    """, (school_id,))
    
    admins = cursor.fetchall()

    conn.close()

    return render_template(
        "view_school_admins.html",
        school=school,
        admins=admins
    )    

# =========================
# View School Admins
# =========================   

@super_admin_bp.route("/schools/<int:school_id>/admins/add", methods=["GET", "POST"])
@login_required
@super_admin_required
def add_school_admin(school_id):

    if current_user.role != "super_admin":
        abort(403)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM schools WHERE id = ?", (school_id,))
    school = cursor.fetchone()

    if not school:
        conn.close()
        abort(404)

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("super_admin.add_school_admin", school_id=school_id))

        hashed_password = hash_password(password)

        try:
            cursor.execute("""
                INSERT INTO users (name, email, password, role, school_id, is_active)
                VALUES (?, ?, ?, 'school_admin', ?, 1)
            """, (name, email, hashed_password, school_id))

            conn.commit()
            flash("School Admin created successfully!", "success")
            return redirect(url_for("super_admin.view_school_admins", school_id=school_id))

        except:
            flash("Email already exists!", "danger")

    conn.close()
    return render_template("add_school_admin.html", school=school) 


# =========================
# TOGGLE SCHOOL ADMIN STATUS
# =========================
@super_admin_bp.route("/admins/toggle/<int:user_id>", methods=["POST"])
@login_required
@super_admin_required
def toggle_school_admin(user_id):

    if current_user.role != "super_admin":
        abort(403)

    conn = get_db()
    cursor = conn.cursor()

    # Fetch user
    cursor.execute("""
        SELECT id, is_active, role
        FROM users
        WHERE id = ?
    """, (user_id,))
    
    user = cursor.fetchone()

    # Ensure user exists and is school_admin
    if user and user["role"] == "school_admin":

        new_status = 0 if user["is_active"] == 1 else 1

        cursor.execute("""
            UPDATE users
            SET is_active = ?
            WHERE id = ?
        """, (new_status, user_id))

        conn.commit()

    conn.close()

    return redirect(request.referrer)   

# =========================
# RESET SCHOOL ADMIN PASSWORD
# =========================
@super_admin_bp.route("/admins/reset-password/<int:user_id>", methods=["POST"])
@login_required
@super_admin_required
def reset_school_admin_password(user_id):

    if current_user.role != "super_admin":
        abort(403)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, role
        FROM users
        WHERE id = ?
    """, (user_id,))
    
    user = cursor.fetchone()

    if not user or user["role"] != "school_admin":
        conn.close()
        abort(404)

    # 🔐 Generate secure temporary password
    characters = string.ascii_letters + string.digits
    temp_password = ''.join(secrets.choice(characters) for _ in range(10))

    hashed_password = hash_password(temp_password)

    cursor.execute("""
        UPDATE users
        SET password = ?, force_password_change = 1
        WHERE id = ?
    """, (hashed_password, user_id))

    conn.commit()
    conn.close()

    flash(f"Temporary Password: {temp_password}", "warning")

    return redirect(request.referrer)    