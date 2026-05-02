from flask import Blueprint, render_template
from app.models import Prompt, Tag, Category

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    recent_prompts = Prompt.query.order_by(Prompt.updated_at.desc()).limit(5).all()
    prompt_count = Prompt.query.count()
    tag_count = Tag.query.count()
    category_count = Category.query.count()
    favorite_count = Prompt.query.filter_by(is_favorite=True).count()

    return render_template(
        "dashboard.html",
        recent_prompts=recent_prompts,
        prompt_count=prompt_count,
        tag_count=tag_count,
        category_count=category_count,
        favorite_count=favorite_count,
    )
