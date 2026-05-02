from flask import Blueprint, request, jsonify, render_template
from app.extensions import db
from app.models import Prompt, Tag

bp = Blueprint("search_api", __name__)


@bp.route("", methods=["GET"])
def search():
    q = request.args.get("q", "").strip()
    if not q:
        if request.headers.get("HX-Request"):
            return ""
        return jsonify({"items": [], "total": 0})

    category_id = request.args.get("category_id", type=int)
    tag = request.args.get("tag")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    # Use raw SQL for FTS5 search
    sql = """
        SELECT rowid, bm25(prompts_fts) as rank
        FROM prompts_fts
        WHERE prompts_fts MATCH :query
        ORDER BY rank
        LIMIT 50
    """

    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute(sql, {"query": q})
        rows = cursor.fetchall()
        conn.close()

        ids = [row[0] for row in rows]
        if not ids:
            if request.headers.get("HX-Request"):
                return '<div class="text-center py-6 text-gray-400">No results</div>'
            return jsonify({"items": [], "total": 0})

        query = Prompt.query.filter(Prompt.id.in_(ids))

        if category_id:
            query = query.filter(Prompt.category_id == category_id)
        if tag:
            query = query.filter(Prompt.tags.any(Tag.name == tag))
        if from_date:
            query = query.filter(Prompt.created_at >= from_date)
        if to_date:
            query = query.filter(Prompt.created_at <= to_date)

        results = query.all()
        # Preserve FTS ranking order
        id_to_rank = {row[0]: row[1] for row in rows}
        results.sort(key=lambda p: id_to_rank.get(p.id, 0))

    except Exception:
        # Fallback to LIKE search if FTS5 fails
        query = Prompt.query.filter(
            db.or_(
                Prompt.title.ilike(f"%{q}%"),
                Prompt.content.ilike(f"%{q}%"),
                Prompt.notes.ilike(f"%{q}%"),
            )
        )
        results = query.limit(50).all()

    if request.headers.get("HX-Request"):
        return render_template("prompts/_prompt_list.html", prompts=results, page=1, pages=1, total=len(results))

    return jsonify({
        "items": [p.to_dict() for p in results],
        "total": len(results),
    })
