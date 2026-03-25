from smart_exam_system.blueprints.auth import auth_bp
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required,current_user
from smart_exam_system.models.user import UserModel
from smart_exam_system.extensions import db
from smart_exam_system.utils.security import hash_password, verify_password,validate_password_strength

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Get expected role from query param (optional)
    expected_role = request.args.get("role")  # e.g., "teacher", "school_admin"

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = UserModel.query.filter_by(email=email).first()

        if user and verify_password(password, user.password):

            # 🚫 Block inactive users
            if not user.is_active:
                flash("Account is inactive. Contact Super Admin.", "danger")
                return redirect(url_for("auth.login", role=expected_role))

            # 1️⃣ Check role if expected_role provided
            if expected_role and user.role != expected_role:
                flash(f"This account is not a {expected_role.replace('_',' ').title()}.", "danger")
                return redirect(url_for("auth.login", role=expected_role))

            login_user(user)

            # 🔐 FORCE PASSWORD CHANGE CHECK
            if user.force_password_change:
                return redirect(url_for("auth.change_password"))

            # Role-based redirect
            if user.role == "super_admin":
                return redirect(url_for("super_admin.dashboard"))
            elif user.role == "school_admin":
                return redirect(url_for("school_admin.dashboard"))
            elif user.role == "teacher":
                return redirect(url_for("teacher.dashboard"))

        else:
            flash("Invalid credentials", "danger")
            return redirect(url_for("auth.login", role=expected_role))

    return render_template("login.html", role=expected_role)

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

        current_user.password = hash_password(new_password)
        current_user.force_password_change = False
        db.session.commit()

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
    return render_template("home.html")