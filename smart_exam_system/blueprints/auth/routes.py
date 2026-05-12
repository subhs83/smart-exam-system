from smart_exam_system.blueprints.auth import auth_bp
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required,current_user
from smart_exam_system.extensions import db
from smart_exam_system.models.user import UserModel
from smart_exam_system.utils.security import verify_password,validate_password_strength
from smart_exam_system.utils.services.auth_service import (
    get_dashboard_redirect,
    authenticate_user,
    validate_login_access,
    change_user_password,
    log_login_attempt,
    is_rate_limited
    )
from datetime import datetime,timedelta
from urllib.parse import urlparse, urljoin



@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    expected_role = request.args.get("role")

    # 🔐 FORCE ROLE SELECTION (IMPORTANT FIX)
    if not expected_role:
        flash("Please select a role before login.", "danger")
        return redirect(url_for("home.home"))  # or role selection page

    # already logged in
    if current_user.is_authenticated:
        if expected_role and current_user.role != expected_role:
            logout_user()
        else:
            return redirect(get_dashboard_redirect(current_user.role))

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        user = authenticate_user(email, password)

        # log failed auth early
        if not user:
            log_login_attempt(email, None, False, request)
            flash("Incorrect email or password.", "danger")
            return render_template("login.html", role=expected_role, email=email)

        error = validate_login_access(user, expected_role)

        if error:
            log_login_attempt(email, user, False, request)
            flash(error, "danger")
            return redirect(url_for("auth.login", role=expected_role))

        login_user(user)

        log_login_attempt(email, user, True, request)

        if user.force_password_change:
            return redirect(url_for("auth.change_password"))

        next_page = request.args.get("next")

        if next_page and is_safe_url(next_page):
            return redirect(next_page)

        return redirect(get_dashboard_redirect(user.role))

    # GET request
    return render_template("login.html", role=expected_role)
    



@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():

    if request.method == "POST":
        new_password = request.form.get("new_password")

        error = validate_password_strength(new_password)
        if error:
            flash(error, "danger")
            return redirect(url_for("auth.change_password"))

        change_user_password(current_user, new_password)

        flash("Password changed successfully.", "success")

        return redirect(get_dashboard_redirect(current_user.role))

    return render_template("change_password.html")



def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))