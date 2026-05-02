from flask import Blueprint, render_template, request
from app.models import AIConfig, Prompt

bp = Blueprint("optimize_pages", __name__)


@bp.route("/")
def workbench():
    configs = AIConfig.query.filter_by(is_active=True).all()
    prompt = None
    prompt_id = request.args.get("prompt_id", type=int)
    if prompt_id:
        prompt = Prompt.query.get(prompt_id)
    return render_template("optimize/workbench.html", ai_configs=configs, prompt=prompt)
