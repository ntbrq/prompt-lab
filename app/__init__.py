import os
from flask import Flask
from app.extensions import db, migrate
from config import Config


def create_app(config_class=None):
    app = Flask(__name__)

    if config_class:
        app.config.from_object(config_class)
    else:
        app.config.from_object(Config)

    # Ensure data directory exists
    db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if "sqlite:///" in db_uri and ":memory:" not in db_uri:
        db_path = db_uri.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)

    # Import models so they're registered
    from app import models  # noqa: F401

    # Register blueprints
    from app.api import register_api_blueprints
    from app.pages import register_page_blueprints
    register_api_blueprints(app)
    register_page_blueprints(app)

    # Create tables and FTS triggers
    with app.app_context():
        db.create_all()
        _create_fts_triggers()
        _seed_defaults()

    return app


def _create_fts_triggers():
    """Create FTS5 virtual table with trigram tokenizer (supports CJK substring matching) and sync triggers."""
    conn = db.engine.raw_connection()
    try:
        cursor = conn.cursor()

        # Check if existing FTS table uses trigram; if not, recreate it
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='prompts_fts'")
        row = cursor.fetchone()
        needs_rebuild = row is not None and "trigram" not in (row[0] or "")

        if needs_rebuild:
            cursor.execute("DROP TABLE IF EXISTS prompts_fts")
            cursor.execute("DROP TRIGGER IF EXISTS prompts_fts_ai")
            cursor.execute("DROP TRIGGER IF EXISTS prompts_fts_ad")
            cursor.execute("DROP TRIGGER IF EXISTS prompts_fts_au")

        cursor.executescript("""
            CREATE VIRTUAL TABLE IF NOT EXISTS prompts_fts USING fts5(
                title,
                content,
                notes,
                content=prompts,
                content_rowid=id,
                tokenize='trigram'
            );

            CREATE TRIGGER IF NOT EXISTS prompts_fts_ai AFTER INSERT ON prompts BEGIN
                INSERT INTO prompts_fts(rowid, title, content, notes)
                VALUES (new.id, new.title, new.content, new.notes);
            END;

            CREATE TRIGGER IF NOT EXISTS prompts_fts_ad AFTER DELETE ON prompts BEGIN
                INSERT INTO prompts_fts(prompts_fts, rowid, title, content, notes)
                VALUES ('delete', old.id, old.title, old.content, old.notes);
            END;

            CREATE TRIGGER IF NOT EXISTS prompts_fts_au AFTER UPDATE ON prompts BEGIN
                INSERT INTO prompts_fts(prompts_fts, rowid, title, content, notes)
                VALUES ('delete', old.id, old.title, old.content, old.notes);
                INSERT INTO prompts_fts(rowid, title, content, notes)
                VALUES (new.id, new.title, new.content, new.notes);
            END;
        """)

        # Rebuild index if we recreated the table
        if needs_rebuild:
            cursor.execute("INSERT INTO prompts_fts(prompts_fts) VALUES('rebuild')")

        conn.commit()
    finally:
        conn.close()


def _seed_defaults():
    """Seed default categories and templates if none exist."""
    import json
    from app.models import Category, Tag, Template

    if Category.query.count() == 0:
        seed_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "seed", "default_categories.json")
        if os.path.exists(seed_path):
            with open(seed_path) as f:
                categories = json.load(f)
            for cat_data in categories:
                db.session.add(Category(**cat_data))
            db.session.commit()

    if Template.query.count() == 0:
        seed_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "seed", "builtin_templates.json")
        if os.path.exists(seed_path):
            with open(seed_path) as f:
                templates = json.load(f)
            for tmpl in templates:
                category = Category.query.filter_by(name=tmpl.get("category")).first() if tmpl.get("category") else None
                template = Template(
                    title=tmpl["title"],
                    content=tmpl["content"],
                    description=tmpl.get("description"),
                    category_id=category.id if category else None,
                    source="builtin",
                )
                # Handle tags
                for tag_name in tmpl.get("tags", []):
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    template.tags.append(tag)
                db.session.add(template)
            db.session.commit()
