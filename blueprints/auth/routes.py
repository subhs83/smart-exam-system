from . import auth_bp
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required,current_user
from models.user import User
from database import get_db
from utils.security import hash_password, verify_password,validate_password_strength

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db()
        user_data = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        conn.close()

        if user_data and verify_password(password, user_data["password"]):

            # 🚫 Block inactive users
            if user_data["is_active"] == 0:
                flash("Account is inactive. Contact Super Admin.", "danger")
                return redirect(url_for("auth.login"))

            user = User(
                user_data["id"],
                user_data["name"],
                user_data["email"],
                user_data["password"],
                user_data["role"],
                user_data["school_id"],
            )

            login_user(user)

            # 🔐 FORCE PASSWORD CHANGE CHECK
            if user_data["force_password_change"] == 1:
                return redirect(url_for("auth.change_password"))

            # Role-based redirect
            if user.role == "super_admin":
                return redirect(url_for("super_admin.dashboard"))
            elif user.role == "school_admin":
                return redirect(url_for("school_admin.dashboard"))
            elif user.role == "teacher":
                return redirect(url_for("teacher.dashboard"))

        flash("Invalid credentials", "danger")

    return render_template("login.html")

@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():

    if request.method == "POST":
        new_password = request.form.get("new_password")

        # 🔐 Validate strength
        error = validate_password_strength(new_password)
        if error:
            flash(error, "danger")
            return redirect(url_for("auth.change_password"))

        hashed_password = hash_password(new_password)

        conn = get_db()
        conn.execute("""
            UPDATE users
            SET password = ?, force_password_change = 0
            WHERE id = ?
        """, (hashed_password, current_user.id))
        conn.commit()
        conn.close()

        flash("Password changed successfully.", "success")

        # Role-based redirect
        if current_user.role == "super_admin":
            return redirect(url_for("super_admin.dashboard"))
        elif current_user.role == "school_admin":
            return redirect(url_for("school_admin.dashboard"))
        elif current_user.role == "teacher":
            return redirect(url_for("teacher.dashboard"))

    return render_template("change_password.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))