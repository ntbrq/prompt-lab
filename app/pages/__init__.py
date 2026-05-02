def register_page_blueprints(app):
    from app.pages.dashboard import bp as dashboard_bp
    from app.pages.prompt_pages import bp as prompts_bp
    from app.pages.template_pages import bp as templates_bp
    from app.pages.resource_pages import bp as resources_bp
    from app.pages.optimize_pages import bp as optimize_bp
    from app.pages.settings_pages import bp as settings_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(prompts_bp, url_prefix="/prompts")
    app.register_blueprint(templates_bp, url_prefix="/templates")
    app.register_blueprint(resources_bp, url_prefix="/resources")
    app.register_blueprint(optimize_bp, url_prefix="/optimize")
    app.register_blueprint(settings_bp, url_prefix="/settings")
