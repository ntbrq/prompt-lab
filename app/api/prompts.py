from flask import Blueprint, request, jsonify, render_template
from app.extensions import db
from app.models import Prompt, Tag

bp = Blueprint("prompts_api", __name__)


@bp.route("", methods=["GET"])
def list_prompts():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    category_id = request.args.get("category_id", type=int)
    tag = request.args.get("tag")
    source = request.args.get("source")
    is_favorite = request.args.get("is_favorite")
    sort_by = request.args.get("sort_by", "updated_at")

    query = Prompt.query

    if category_id:
        query = query.filter(Prompt.category_id == category_id)
    if tag:
        query = query.filter(Prompt.tags.any(Tag.name == tag))
    if source:
        query = query.filter(Prompt.source == source)
    if is_favorite is not None:
        query = query.filter(Prompt.is_favorite == (is_favorite == "true"))

    sort_col = getattr(Prompt, sort_by, Prompt.updated_at)
    query = query.order_by(sort_col.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # HTMX request: return HTML partial
    if request.headers.get("HX-Request"):
        return render_template(
            "prompts/_prompt_list.html",
            prompts=pagination.items,
            page=pagination.page,
            pages=pagination.pages,
            total=pagination.total,
        )

    return jsonify({
        "items": [p.to_dict() for p in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
    })


@bp.route("", methods=["POST"])
def create_prompt():
    # Support both JSON and form data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
        data["tag_ids"] = [int(x) for x in request.form.getlist("tag_ids")]
        if data.get("category_id") == "":
            data["category_id"] = None
        elif data.get("category_id"):
            data["category_id"] = int(data["category_id"])
        if data.get("result_quality") == "":
            data["result_quality"] = None
        elif data.get("result_quality"):
            data["result_quality"] = int(data["result_quality"])

    if not data or not data.get("title") or not data.get("content"):
        return jsonify({"error": "title and content are required"}), 400

    prompt = Prompt(
        title=data["title"],
        content=data["content"],
        category_id=data.get("category_id"),
        model_used=data.get("model_used") or None,
        result_quality=data.get("result_quality"),
        notes=data.get("notes") or None,
        source=data.get("source", "user"),
    )

    if data.get("tag_ids"):
        tags = Tag.query.filter(Tag.id.in_(data["tag_ids"])).all()
        prompt.tags = tags

    db.session.add(prompt)
    db.session.commit()

    if request.headers.get("HX-Request"):
        return "", 201, {"HX-Redirect": f"/prompts/{prompt.id}"}

    return jsonify(prompt.to_dict()), 201


@bp.route("/<int:prompt_id>", methods=["GET"])
def get_prompt(prompt_id):
    prompt = db.get_or_404(Prompt, prompt_id)
    return jsonify(prompt.to_dict())


@bp.route("/<int:prompt_id>", methods=["PUT"])
def update_prompt(prompt_id):
    prompt = db.get_or_404(Prompt, prompt_id)

    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
        data["tag_ids"] = [int(x) for x in request.form.getlist("tag_ids")]
        if data.get("category_id") == "":
            data["category_id"] = None
        elif data.get("category_id"):
            data["category_id"] = int(data["category_id"])
        if data.get("result_quality") == "":
            data["result_quality"] = None
        elif data.get("result_quality"):
            data["result_quality"] = int(data["result_quality"])

    if not data:
        return jsonify({"error": "request body required"}), 400

    for field in ("title", "content", "category_id", "model_used", "result_quality", "notes", "source"):
        if field in data:
            setattr(prompt, field, data[field])

    if "is_favorite" in data:
        prompt.is_favorite = data["is_favorite"]

    if "tag_ids" in data:
        tags = Tag.query.filter(Tag.id.in_(data["tag_ids"])).all() if data["tag_ids"] else []
        prompt.tags = tags

    db.session.commit()

    if request.headers.get("HX-Request"):
        return "", 200, {"HX-Redirect": f"/prompts/{prompt.id}"}

    return jsonify(prompt.to_dict())


@bp.route("/<int:prompt_id>", methods=["DELETE"])
def delete_prompt(prompt_id):
    prompt = db.get_or_404(Prompt, prompt_id)
    db.session.delete(prompt)
    db.session.commit()

    if request.headers.get("HX-Request"):
        return "", 204, {"HX-Redirect": "/prompts"}

    return "", 204


@bp.route("/<int:prompt_id>/favorite", methods=["POST"])
def toggle_favorite(prompt_id):
    prompt = db.get_or_404(Prompt, prompt_id)
    prompt.is_favorite = not prompt.is_favorite
    db.session.commit()
    return jsonify({"is_favorite": prompt.is_favorite})
