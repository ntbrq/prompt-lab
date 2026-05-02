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

    # Escape double quotes in query for FTS5
    safe_q = q.replace('"', '""')

    # Trigram tokenizer requires >= 3 chars; short queries go directly to LIKE
    use_fts = len(q) >= 3
    results = []

    if use_fts:
        # Trigram tokenizer: column filter for substring matching
        fts_query = f'title : "{safe_q}" OR content : "{safe_q}" OR notes : "{safe_q}"'

        sql = """
            SELECT rowid, rank
            FROM prompts_fts
            WHERE prompts_fts MATCH :query
            ORDER BY rank
            LIMIT 50
        """

        try:
            conn = db.engine.raw_connection()
            cursor = conn.cursor()
            cursor.execute(sql, {"query": fts_query})
            rows = cursor.fetchall()
            conn.close()

            ids = [row[0] for row in rows]
            if ids:
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
            pass

    # Fallback to LIKE if FTS returned nothing (including short queries)
    if not results:
        query = Prompt.query.filter(
            db.or_(
                Prompt.title.ilike(f"%{q}%"),
                Prompt.content.ilike(f"%{q}%"),
                Prompt.notes.ilike(f"%{q}%"),
            )
        )
        if category_id:
            query = query.filter(Prompt.category_id == category_id)
        if tag:
            query = query.filter(Prompt.tags.any(Tag.name == tag))
        results = query.limit(50).all()

    if request.headers.get("HX-Request"):
        return render_template("prompts/_prompt_list.html", prompts=results, page=1, pages=1, total=len(results))

    return jsonify({
        "items": [p.to_dict() for p in results],
        "total": len(results),
    })
