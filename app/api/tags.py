from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Tag, prompt_tags

bp = Blueprint("tags_api", __name__)


@bp.route("", methods=["GET"])
def list_tags():
    tags = Tag.query.all()
    result = []
    for t in tags:
        count = db.session.query(db.func.count(prompt_tags.c.prompt_id)).filter(
            prompt_tags.c.tag_id == t.id
        ).scalar()
        d = t.to_dict()
        d["usage_count"] = count
        result.append(d)
    return jsonify(result)


@bp.route("", methods=["POST"])
def create_tag():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "name is required"}), 400

    existing = Tag.query.filter_by(name=data["name"]).first()
    if existing:
        return jsonify({"error": "tag already exists"}), 409

    tag = Tag(name=data["name"], color=data.get("color"))
    db.session.add(tag)
    db.session.commit()
    return jsonify(tag.to_dict()), 201


@bp.route("/<int:tag_id>", methods=["DELETE"])
def delete_tag(tag_id):
    tag = db.get_or_404(Tag, tag_id)
    db.session.delete(tag)
    db.session.commit()
    return "", 204
