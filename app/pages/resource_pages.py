from flask import Blueprint, render_template

bp = Blueprint("resource_pages", __name__)


@bp.route("/")
def list_resources():
    return render_template("resources/list.html")
