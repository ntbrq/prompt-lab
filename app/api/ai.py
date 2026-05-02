import json
from flask import Blueprint, request, jsonify, Response
from app.extensions import db
from app.models import AIConfig, OptimizationLog, Prompt
from app.services.openai_compatible import OpenAICompatibleProvider
from app.services.optimizer import PromptOptimizer

bp = Blueprint("ai_api", __name__)


def _get_provider(provider_name=None, model=None):
    if provider_name:
        config = AIConfig.query.filter_by(provider=provider_name, is_active=True).first()
    else:
        config = AIConfig.query.filter_by(is_active=True).first()

    if not config:
        return None

    return OpenAICompatibleProvider(
        api_key=config.api_key,
        base_url=config.base_url,
        default_model=model or config.default_model,
    )


@bp.route("/optimize", methods=["POST"])
def optimize():
    data = request.get_json()
    if not data or not data.get("content"):
        return jsonify({"error": "content is required"}), 400

    provider = _get_provider(data.get("provider"), data.get("model"))
    if not provider:
        return jsonify({"error": "no active AI provider configured"}), 400

    optimizer = PromptOptimizer(provider)
    opt_type = data.get("optimization_type", "improve")

    def generate():
        full_text = ""
        for chunk in optimizer.optimize_stream(
            content=data["content"],
            optimization_type=opt_type,
            context=data.get("context"),
            target_language=data.get("target_language"),
        ):
            full_text += chunk
            yield f"event: chunk\ndata: {json.dumps({'text': chunk})}\n\n"
        yield f"event: done\ndata: {json.dumps({'full_text': full_text})}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@bp.route("/compare", methods=["POST"])
def compare():
    data = request.get_json()
    if not data or not data.get("original") or not data.get("optimized") or not data.get("test_input"):
        return jsonify({"error": "original, optimized, and test_input are required"}), 400

    provider = _get_provider(data.get("provider"), data.get("model"))
    if not provider:
        return jsonify({"error": "no active AI provider configured"}), 400

    original_output = provider.chat([
        {"role": "system", "content": data["original"]},
        {"role": "user", "content": data["test_input"]},
    ])
    optimized_output = provider.chat([
        {"role": "system", "content": data["optimized"]},
        {"role": "user", "content": data["test_input"]},
    ])

    return jsonify({
        "original_output": original_output,
        "optimized_output": optimized_output,
    })


@bp.route("/test", methods=["POST"])
def test_models():
    data = request.get_json()
    if not data or not data.get("content") or not data.get("test_input"):
        return jsonify({"error": "content and test_input are required"}), 400

    models = data.get("models", [])
    if not models:
        return jsonify({"error": "models list is required"}), 400

    results = []
    for m in models:
        provider = _get_provider(m.get("provider"), m.get("model"))
        if not provider:
            results.append({"provider": m.get("provider"), "model": m.get("model"), "error": "provider not found"})
            continue

        import time
        start = time.time()
        output = provider.chat([
            {"role": "system", "content": data["content"]},
            {"role": "user", "content": data["test_input"]},
        ])
        latency = int((time.time() - start) * 1000)

        results.append({
            "provider": m.get("provider"),
            "model": m.get("model"),
            "output": output,
            "latency_ms": latency,
        })

    return jsonify({"results": results})


@bp.route("/configs", methods=["GET"])
def list_configs():
    configs = AIConfig.query.all()
    return jsonify([c.to_dict() for c in configs])


@bp.route("/configs", methods=["POST"])
def create_config():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    required = ("provider", "display_name", "api_key", "base_url", "default_model")
    if not data or not all(data.get(f) for f in required):
        return jsonify({"error": f"required fields: {', '.join(required)}"}), 400

    # Test connection first
    provider = OpenAICompatibleProvider(
        api_key=data["api_key"],
        base_url=data["base_url"],
        default_model=data["default_model"],
    )
    try:
        provider.chat([{"role": "user", "content": "Say OK"}], max_tokens=5)
    except Exception as e:
        return jsonify({"error": f"Connection test failed: {str(e)}"}), 400

    config = AIConfig(
        provider=data["provider"],
        display_name=data["display_name"],
        api_key=data["api_key"],
        base_url=data["base_url"],
        default_model=data["default_model"],
        available_models=data.get("available_models"),
    )
    db.session.add(config)
    db.session.commit()

    if request.headers.get("HX-Request"):
        return "", 201, {"HX-Redirect": "/settings"}

    return jsonify(config.to_dict()), 201


@bp.route("/configs/<int:config_id>", methods=["PUT"])
def update_config(config_id):
    config = db.get_or_404(AIConfig, config_id)
    data = request.get_json()
    if not data:
        return jsonify({"error": "request body required"}), 400

    for field in ("api_key", "base_url", "default_model", "available_models", "is_active", "display_name"):
        if field in data:
            setattr(config, field, data[field])

    db.session.commit()
    return jsonify(config.to_dict())


@bp.route("/test-connection", methods=["POST"])
def test_connection():
    data = request.get_json()
    if not data or not data.get("base_url") or not data.get("api_key"):
        return jsonify({"error": "base_url and api_key are required"}), 400

    provider = OpenAICompatibleProvider(
        api_key=data["api_key"],
        base_url=data["base_url"],
        default_model=data.get("default_model", "gpt-3.5-turbo"),
    )
    try:
        result = provider.chat([{"role": "user", "content": "Say 'OK' in one word."}], max_tokens=10)
        return jsonify({"success": True, "response": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
