from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, render_template
from app.extensions import db
from app.models import Resource, Prompt, Tag

bp = Blueprint("resources_api", __name__)


@bp.route("", methods=["GET"])
def list_resources():
    status = request.args.get("status", "pending_review")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = Resource.query
    if status != "all":
        query = query.filter(Resource.status == status)
    query = query.order_by(Resource.collected_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    if request.headers.get("HX-Request"):
        return render_template("resources/_resource_list.html", resources=pagination.items, status=status)

    return jsonify({
        "items": [r.to_dict() for r in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
    })


@bp.route("", methods=["POST"])
def create_resource():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    if not data or not data.get("content"):
        return jsonify({"error": "content is required"}), 400

    resource = Resource(
        title=data.get("title", "Untitled"),
        url=data.get("url") or None,
        content=data["content"],
        summary=data.get("summary"),
        suggested_tags=data.get("suggested_tags"),
        source_query=data.get("source_query"),
        status="pending_review",
    )
    db.session.add(resource)
    db.session.commit()

    if request.headers.get("HX-Request"):
        return "", 201, {"HX-Redirect": "/resources"}

    return jsonify(resource.to_dict()), 201


@bp.route("/<int:resource_id>", methods=["GET"])
def get_resource(resource_id):
    resource = db.get_or_404(Resource, resource_id)
    return jsonify(resource.to_dict())


@bp.route("/<int:resource_id>/review", methods=["PUT"])
def review_resource(resource_id):
    resource = db.get_or_404(Resource, resource_id)
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    if not data or data.get("status") not in ("approved", "rejected"):
        return jsonify({"error": "status must be 'approved' or 'rejected'"}), 400

    resource.status = data["status"]
    resource.reviewed_at = datetime.now(timezone.utc)
    if data.get("edited_title"):
        resource.title = data["edited_title"]
    if data.get("edited_summary"):
        resource.summary = data["edited_summary"]

    db.session.commit()

    if request.headers.get("HX-Request"):
        return "", 200, {"HX-Redirect": "/resources"}

    return jsonify(resource.to_dict())


@bp.route("/<int:resource_id>/import", methods=["POST"])
def import_resource(resource_id):
    resource = db.get_or_404(Resource, resource_id)
    if resource.status != "approved":
        return jsonify({"error": "resource must be approved before import"}), 400

    data = request.get_json(silent=True) or {}

    prompt = Prompt(
        title=data.get("title", resource.title),
        content=data.get("content", resource.content),
        category_id=data.get("category_id"),
        notes=f"Imported from resource: {resource.url or 'manual'}",
        source="resource",
    )

    if data.get("tag_ids"):
        tags = Tag.query.filter(Tag.id.in_(data["tag_ids"])).all()
        prompt.tags = tags

    db.session.add(prompt)
    db.session.flush()

    resource.status = "imported"
    resource.imported_prompt_id = prompt.id
    db.session.commit()

    if request.headers.get("HX-Request"):
        return "", 201, {"HX-Redirect": f"/prompts/{prompt.id}"}

    return jsonify({"prompt_id": prompt.id, "resource_id": resource.id}), 201
