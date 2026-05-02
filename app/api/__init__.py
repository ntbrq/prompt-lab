def register_api_blueprints(app):
    from app.api.prompts import bp as prompts_bp
    from app.api.tags import bp as tags_bp
    from app.api.categories import bp as categories_bp
    from app.api.search import bp as search_bp
    from app.api.templates import bp as templates_bp
    from app.api.ai import bp as ai_bp
    from app.api.resources import bp as resources_bp
    from app.api.export_import import bp as export_bp

    app.register_blueprint(prompts_bp, url_prefix="/api/prompts")
    app.register_blueprint(tags_bp, url_prefix="/api/tags")
    app.register_blueprint(categories_bp, url_prefix="/api/categories")
    app.register_blueprint(search_bp, url_prefix="/api/search")
    app.register_blueprint(templates_bp, url_prefix="/api/templates")
    app.register_blueprint(ai_bp, url_prefix="/api/ai")
    app.register_blueprint(resources_bp, url_prefix="/api/resources")
    app.register_blueprint(export_bp, url_prefix="/api")
