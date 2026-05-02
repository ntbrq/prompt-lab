from flask import Blueprint, render_template
from app.models import AIConfig

bp = Blueprint("settings_pages", __name__)


@bp.route("/")
def settings():
    configs = AIConfig.query.all()
    return render_template("settings.html", ai_configs=configs)
