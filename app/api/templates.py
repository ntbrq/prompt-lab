from flask import Blueprint, request, jsonify, render_template
from app.extensions import db
from app.models import Template, Tag, Prompt, Category

bp = Blueprint("templates_api", __name__)


@bp.route("", methods=["GET"])
def list_templates():
    category = request.args.get("category")
    source = request.args.get("source")

    query = Template.query
    if category:
        query = query.filter(Template.category.has(Category.name == category))
    if source:
        query = query.filter(Template.source == source)

    templates = query.order_by(Template.title).all()

    if request.headers.get("HX-Request"):
        return render_template("templates/_template_list.html", templates=templates)

    return jsonify([t.to_dict() for t in templates])


@bp.route("", methods=["POST"])
def create_template():
    data = request.get_json()
    if not data or not data.get("title") or not data.get("content"):
        return jsonify({"error": "title and content are required"}), 400

    template = Template(
        title=data["title"],
        content=data["content"],
        description=data.get("description"),
        category_id=data.get("category_id"),
        source="user",
    )

    if data.get("tag_ids"):
        tags = Tag.query.filter(Tag.id.in_(data["tag_ids"])).all()
        template.tags = tags

    db.session.add(template)
    db.session.commit()
    return jsonify(template.to_dict()), 201


@bp.route("/<int:template_id>/use", methods=["POST"])
def use_template(template_id):
    template = db.get_or_404(Template, template_id)
    data = request.get_json(silent=True) or {}

    # Create a new prompt from the template
    prompt = Prompt(
        title=data.get("title", f"From: {template.title}"),
        content=data.get("content", template.content),
        category_id=template.category_id,
        source="template",
    )
    prompt.tags = list(template.tags)

    db.session.add(prompt)
    db.session.commit()

    # HTMX: redirect to the new prompt
    if request.headers.get("HX-Request"):
        return "", 201, {"HX-Redirect": f"/prompts/{prompt.id}"}

    return jsonify({"prompt_id": prompt.id, "prompt": prompt.to_dict()}), 201
