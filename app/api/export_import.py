import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, Response
from app.extensions import db
from app.models import Prompt, Tag

bp = Blueprint("export_import_api", __name__)


@bp.route("/export", methods=["GET"])
def export_prompts():
    fmt = request.args.get("format", "json")
    ids = request.args.get("ids")
    category_id = request.args.get("category_id", type=int)
    tag = request.args.get("tag")

    query = Prompt.query
    if ids:
        id_list = [int(i) for i in ids.split(",")]
        query = query.filter(Prompt.id.in_(id_list))
    if category_id:
        query = query.filter(Prompt.category_id == category_id)
    if tag:
        query = query.filter(Prompt.tags.any(Tag.name == tag))

    prompts = query.all()

    if fmt == "markdown":
        return _export_markdown(prompts)
    return _export_json(prompts)


def _export_json(prompts):
    data = {
        "version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "prompts": [
            {
                "title": p.title,
                "content": p.content,
                "category": p.category.name if p.category else None,
                "tags": [t.name for t in p.tags],
                "model_used": p.model_used,
                "result_quality": p.result_quality,
                "notes": p.notes,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in prompts
        ],
    }
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=prompts_export.json"},
    )


def _export_markdown(prompts):
    lines = []
    for p in prompts:
        lines.append(f"# Prompt: {p.title}")
        if p.category:
            lines.append(f"**Category:** {p.category.name}")
        if p.tags:
            lines.append(f"**Tags:** {', '.join(t.name for t in p.tags)}")
        if p.result_quality:
            lines.append(f"**Rating:** {'*' * p.result_quality}")
        if p.model_used:
            lines.append(f"**Model:** {p.model_used}")
        lines.append("---")
        lines.append(p.content)
        lines.append("---")
        if p.notes:
            lines.append(f"**Notes:** {p.notes}")
        lines.append("")
        lines.append("---")
        lines.append("")

    content = "\n".join(lines)
    return Response(
        content,
        mimetype="text/markdown",
        headers={"Content-Disposition": "attachment; filename=prompts_export.md"},
    )


@bp.route("/import", methods=["POST"])
def import_prompts():
    if "file" not in request.files:
        msg = "No file selected"
        if request.headers.get("HX-Request"):
            return f'<span class="text-red-600">{msg}</span>', 400
        return jsonify({"error": msg}), 400

    file = request.files["file"]
    if not file.filename:
        msg = "No file selected"
        if request.headers.get("HX-Request"):
            return f'<span class="text-red-600">{msg}</span>', 400
        return jsonify({"error": msg}), 400

    filename = file.filename.lower()

    try:
        if filename.endswith(".json"):
            result = _import_json(file)
        elif filename.endswith(".md"):
            result = _import_markdown(file)
        else:
            msg = "Unsupported format, use .json or .md"
            if request.headers.get("HX-Request"):
                return f'<span class="text-red-600">{msg}</span>', 400
            return jsonify({"error": msg}), 400
    except Exception as e:
        msg = f"Import failed: {str(e)}"
        if request.headers.get("HX-Request"):
            return f'<span class="text-red-600">{msg}</span>', 400
        return jsonify({"error": msg}), 400

    data = result.get_json()
    if request.headers.get("HX-Request"):
        imported = data.get("imported", 0)
        skipped = data.get("skipped", 0)
        if imported > 0:
            return f'<span class="text-green-600">Imported {imported} prompt(s){f", skipped {skipped}" if skipped else ""}</span>'
        else:
            return f'<span class="text-yellow-600">No prompts imported</span>'

    return result


def _import_json(file):
    data = json.loads(file.read().decode("utf-8"))
    prompts_data = data.get("prompts", [])
    imported = 0
    errors = []

    for i, pd in enumerate(prompts_data):
        if not pd.get("title") or not pd.get("content"):
            errors.append(f"item {i}: missing title or content")
            continue

        prompt = Prompt(
            title=pd["title"],
            content=pd["content"],
            model_used=pd.get("model_used"),
            result_quality=pd.get("result_quality"),
            notes=pd.get("notes"),
            source="imported",
        )

        if pd.get("category"):
            from app.models import Category
            cat = Category.query.filter_by(name=pd["category"]).first()
            if cat:
                prompt.category_id = cat.id

        if pd.get("tags"):
            tags = []
            for tag_name in pd["tags"]:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                tags.append(tag)
            prompt.tags = tags

        db.session.add(prompt)
        imported += 1

    db.session.commit()
    return jsonify({"imported": imported, "skipped": len(errors), "errors": errors})


def _import_markdown(file):
    content = file.read().decode("utf-8")
    blocks = content.split("\n# Prompt: ")
    imported = 0
    errors = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        lines = block.split("\n", 1)
        title = lines[0].strip()
        body = lines[1] if len(lines) > 1 else ""

        # Extract content between --- markers
        content_parts = body.split("---")
        prompt_content = ""
        notes = None

        if len(content_parts) >= 3:
            prompt_content = content_parts[1].strip()
            notes_part = content_parts[2].strip()
            if notes_part.startswith("**Notes:**"):
                notes = notes_part.replace("**Notes:**", "").strip()
        else:
            prompt_content = body

        if not title or not prompt_content:
            errors.append(f"block '{title}': missing content")
            continue

        prompt = Prompt(title=title, content=prompt_content, notes=notes, source="imported")
        db.session.add(prompt)
        imported += 1

    db.session.commit()
    return jsonify({"imported": imported, "skipped": len(errors), "errors": errors})
