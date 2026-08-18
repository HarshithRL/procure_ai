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


@views_bp.route("/projects/new")
def new_project_chooser():
    """Path chooser: Option 1 (chat) or Option 2 (form)."""
    return render_template("new_project_chooser.html")


@views_bp.route("/projects/new/form")
def new_project_form():
    """Manual form builder."""
    return render_template("new_project.html")


@views_bp.route("/projects/new/chat")
def new_project_chat():
    """Chat-based builder."""
    return render_template("new_project_chat.html")


@views_bp.route("/projects/<int:project_id>")
def workspace(project_id):
    """3-pane workspace: sources, chat, studio."""
    return render_template("workspace.html", project_id=project_id)
