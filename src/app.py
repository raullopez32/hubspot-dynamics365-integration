from __future__ import annotations

from collections.abc import Callable

from flask import Flask, jsonify

from src.config import Settings
from src.sync.factory import build_sync_workflow


def create_app(
    workflow_builder: Callable[[Settings], object] = build_sync_workflow,
) -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.post("/sync")
    def sync():
        try:
            settings = Settings.from_env()
            workflow = workflow_builder(settings)
            result = workflow.run(settings.hubspot_list_id)
            return jsonify({"status": "ok", **result}), 200
        except ValueError as exc:
            return jsonify({"status": "error", "error": str(exc)}), 400
        except Exception:
            app.logger.exception("Synchronization failed")
            return jsonify({"status": "error", "error": "Synchronization failed"}), 500

    return app


app = create_app()
