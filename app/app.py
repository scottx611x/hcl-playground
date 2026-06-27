from flask import Flask, abort, jsonify, render_template, request

from backend.terraform_utils import (
    ENGINES,
    MAX_CODE_BYTES,
    EvaluationError,
    evaluate,
    installed_versions,
    list_functions,
)

app = Flask(__name__)

# Cap request bodies (Flask returns 413 past this). Headroom over MAX_CODE_BYTES
# for the small JSON envelope.
app.config["MAX_CONTENT_LENGTH"] = MAX_CODE_BYTES + 8 * 1024

DEFAULT_ENGINE = "terraform"


def _versions_by_engine():
    return {engine: installed_versions(engine) for engine in ENGINES}


@app.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html",
        versions=_versions_by_engine(),
        default_engine=DEFAULT_ENGINE,
    )


@app.route("/evaluate", methods=["POST"])
def evaluate_route():
    # JSON-only: a cross-site HTML form can't set application/json without a CORS
    # preflight, so this also resists CSRF (there's no session/cookie anyway).
    if not request.is_json:
        abort(415)
    data = request.get_json(silent=True) or {}
    engine = (data.get("engine") or DEFAULT_ENGINE).strip()
    version = (data.get("version") or "").strip()
    code = data.get("code") or ""

    try:
        output = evaluate(engine, version, code)
    except EvaluationError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"output": output})


@app.route("/functions", methods=["GET"])
def functions_route():
    engine = (request.args.get("engine") or DEFAULT_ENGINE).strip()
    version = (request.args.get("version") or "").strip()
    try:
        functions = list_functions(engine, version)
    except EvaluationError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"functions": functions})


@app.route("/health", methods=["GET"])
def health():
    return "healthy", 200


@app.after_request
def security_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        # Monaco (from cdnjs) needs eval + blob workers.
        "script-src 'self' 'unsafe-eval' https://cdnjs.cloudflare.com https://unpkg.com; "
        "worker-src 'self' blob:; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "connect-src 'self' https://cdnjs.cloudflare.com; "
        "img-src 'self' data:; "
        "frame-ancestors 'none'; base-uri 'self'"
    )
    return resp
