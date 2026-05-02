from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Category

bp = Blueprint("categories_api", __name__)


@bp.route("", methods=["GET"])
def list_categories():
    categories = Category.query.order_by(Category.sort_order, Category.name).all()
    return jsonify([c.to_dict() for c in categories])


@bp.route("", methods=["POST"])
def create_category():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "name is required"}), 400

    existing = Category.query.filter_by(name=data["name"]).first()
    if existing:
        return jsonify({"error": "category already exists"}), 409

    cat = Category(
        name=data["name"],
        description=data.get("description"),
        sort_order=data.get("sort_order", 0),
    )
    db.session.add(cat)
    db.session.commit()
    return jsonify(cat.to_dict()), 201


@bp.route("/<int:cat_id>", methods=["PUT"])
def update_category(cat_id):
    cat = db.get_or_404(Category, cat_id)
    data = request.get_json()
    if not data:
        return jsonify({"error": "request body required"}), 400

    for field in ("name", "description", "sort_order"):
        if field in data:
            setattr(cat, field, data[field])

    db.session.commit()
    return jsonify(cat.to_dict())


@bp.route("/<int:cat_id>", methods=["DELETE"])
def delete_category(cat_id):
    cat = db.get_or_404(Category, cat_id)
    db.session.delete(cat)
    db.session.commit()
    return "", 204
