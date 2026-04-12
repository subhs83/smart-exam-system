# smart_exam_system/blueprints/home.py
from flask import render_template, redirect, url_for,request
from flask_login import current_user
from smart_exam_system.blueprints.footer import footer_bp
 

 #=============== Privacy =================
@footer_bp.route("/privacy")
def privacy():
    return render_template("privacy.html", hide_sidebar=True)


 
# ================= Terms&Conditions =================
@footer_bp.route("/terms&conditions")
def termsconditions():
    return render_template("termsconditions.html", hide_sidebar=True)


# ================= Support =================
@footer_bp.route("/support")
def support():
    if request.method == "POST":
        # later: save or send mail
        flash("Message sent successfully!", "success")
        return redirect(url_for("main.contact"))

    return render_template("support.html", hide_sidebar=True)