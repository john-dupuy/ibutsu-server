from importlib import import_module
from pathlib import Path

from connexion import App
from dynaconf import FlaskDynaconf
from flask import redirect
from flask import request
from flask_cors import CORS
from ibutsu_server.db.base import db
from ibutsu_server.encoder import JSONEncoder
from ibutsu_server.tasks import create_celery_app

FRONTEND_PATH = Path("/app/frontend")


def get_app(**extra_config):
    """Create the WSGI application"""

    app = App(__name__, specification_dir="./openapi/")
    app.app.json_encoder = JSONEncoder
    app.app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", True)
    FlaskDynaconf(app.app)
    app.app.config.update(extra_config)

    create_celery_app(app.app)
    app.add_api(
        "openapi.yaml", arguments={"title": "Ibutsu"}, base_path="/api", pythonic_params=True
    )

    CORS(app.app)
    db.init_app(app.app)

    with app.app.app_context():
        db.create_all()

    @app.route("/")
    def index():
        return redirect("/api/ui/", code=302)

    @app.route("/admin/run-task", methods=["POST"])
    def run_task():
        params = request.get_json(force=True, silent=True)
        if not params:
            return "Bad request", 400
        task_path = params.get("task")
        task_params = params.get("params", {})
        if not task_path:
            return "Bad request", 400
        task_module, task_name = task_path.split(".", 2)
        try:
            mod = import_module(f"ibutsu_server.tasks.{task_module}")
        except ImportError:
            return "Not found", 404
        if not hasattr(mod, task_name):
            return "Not found", 404
        task = getattr(mod, task_name)
        task.delay(**task_params)
        return "Accepted", 202

    return app
