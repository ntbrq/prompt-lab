from flask import Blueprint, render_template
from app.models import Prompt, Tag, Category

bp = Blueprint("prompt_pages", __name__)


@bp.route("/")
def list_prompts():
    tags = Tag.query.all()
    categories = Category.query.order_by(Category.sort_order, Category.name).all()
    return render_template("prompts/list.html", tags=tags, categories=categories)


@bp.route("/new")
def new_prompt():
    tags = Tag.query.all()
    categories = Category.query.order_by(Category.sort_order, Category.name).all()
    return render_template("prompts/form.html", prompt=None, tags=tags, categories=categories)


@bp.route("/<int:prompt_id>")
def detail(prompt_id):
    prompt = Prompt.query.get_or_404(prompt_id)
    tags = Tag.query.all()
    categories = Category.query.order_by(Category.sort_order, Category.name).all()
    return render_template("prompts/detail.html", prompt=prompt, tags=tags, categories=categories)


@bp.route("/<int:prompt_id>/edit")
def edit(prompt_id):
    prompt = Prompt.query.get_or_404(prompt_id)
    tags = Tag.query.all()
    categories = Category.query.order_by(Category.sort_order, Category.name).all()
    return render_template("prompts/form.html", prompt=prompt, tags=tags, categories=categories)
