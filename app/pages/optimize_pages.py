from flask import Blueprint, render_template
from app.models import AIConfig

bp = Blueprint("optimize_pages", __name__)


@bp.route("/")
def workbench():
    configs = AIConfig.query.filter_by(is_active=True).all()
    return render_template("optimize/workbench.html", ai_configs=configs)
