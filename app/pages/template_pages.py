from flask import Blueprint, render_template

bp = Blueprint("template_pages", __name__)


@bp.route("/")
def list_templates():
    return render_template("templates/list.html")
