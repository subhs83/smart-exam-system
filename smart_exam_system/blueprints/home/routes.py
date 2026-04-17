# smart_exam_system/blueprints/home.py
from flask import render_template, redirect, url_for,request,flash
from flask_login import current_user
from smart_exam_system.blueprints.home import home_bp
from smart_exam_system.extensions import db
from smart_exam_system.models.democontact import DemoRequest, ContactMessage
 

@home_bp.route("/")
def home():
    # Render public home page with no sidebar
    return render_template("home.html", hide_nav=False, hide_footer=False, hide_sidebar=True)

# ================= FEATURES =================
@home_bp.route("/features")
def features():
    return render_template("features.html", hide_sidebar=True)


# ================= PRICING =================
#@home_bp.route("/pricing")
#def pricing():
#    return render_template("pricing.html", hide_sidebar=True)


# ================= DEMO =================

@home_bp.route("/demo", methods=["GET", "POST"])
def demo():
    if request.method == "POST":
        school_name = request.form.get("school_name")
        name = request.form.get("name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        size = request.form.get("size")

        if not school_name or not name or not phone:
            flash("Please fill all required fields", "danger")
            return redirect(url_for("home.demo"))

        try:
            demo = DemoRequest(
                school_name=school_name,
                name=name,
                phone=phone,
                email=email,
                size=size
            )

            db.session.add(demo)
            db.session.commit()

            flash("Demo request submitted successfully!", "success")

        except Exception as e:
            db.session.rollback()
            print(e)
            flash("Something went wrong. Try again.", "danger")

        return redirect(url_for("home.demo"))

    return render_template("demo.html", hide_sidebar=True)

# ================= CONTACT =================
 
@home_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        message = request.form.get("message")

        if not name or not phone or not message:
            flash("Please fill all required fields", "danger")
            return redirect(url_for("home.contact"))

        try:
            contact = ContactMessage(
                name=name,
                phone=phone,
                email=email,
                message=message
            )

            db.session.add(contact)
            db.session.commit()

            flash("Message sent successfully!", "success")

        except Exception as e:
            db.session.rollback()
            print(e)
            flash("Something went wrong. Try again.", "danger")

        return redirect(url_for("home.contact"))

    return render_template("contact.html", hide_sidebar=True)