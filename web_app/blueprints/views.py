from flask import Blueprint, render_template

views_bp = Blueprint("views", __name__)


@views_bp.route("/")
def index():
    return render_template("index.html")


@views_bp.route("/profile")
def profile():
    return render_template("profile.html")


@views_bp.route("/login")
def login():
    return render_template("login.html")


@views_bp.route("/chat")
def chat():
    return render_template("chat.html")
