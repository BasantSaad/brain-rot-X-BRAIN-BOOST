from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from agent.focus_engine import FocusCoachConfig, FocusCoachEngine
from simulator.behavior_simulator import BehaviorSimulationConfig, BehaviorSimulator


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


class FocusRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.engine = FocusCoachEngine(FocusCoachConfig())
        self.simulator = BehaviorSimulator(BehaviorSimulationConfig())
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/dashboard":
            self._handle_dashboard(parsed.query)
            return
        if parsed.path == "/api/plan":
            self._handle_plan(parsed.query)
            return
        if parsed.path == "/api/health":
            self._send_json({"status": "ok", "service": "focusguard-demo"})
            return
        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def _handle_dashboard(self, query: str) -> None:
        params = parse_qs(query)
        lang = self._single(params, "lang", "en")
        permissions = self._single(params, "permissions", "true").lower() == "true"
        audience = self._single(params, "audience", "student")
        mode = self._single(params, "mode", "user")

        profile = self.simulator.build_profile(audience=audience, permissions_granted=permissions)
        dashboard = self.engine.build_dashboard(profile=profile, language=lang, mode=mode)
        self._send_json(dashboard.to_dict())

    def _handle_plan(self, query: str) -> None:
        params = parse_qs(query)
        lang = self._single(params, "lang", "en")
        permissions = self._single(params, "permissions", "true").lower() == "true"
        audience = self._single(params, "audience", "student")

        profile = self.simulator.build_profile(audience=audience, permissions_granted=permissions)
        plan = self.engine.build_personalized_plan(profile=profile, language=lang)
        self._send_json(plan.to_dict())

    def _single(self, params: dict[str, list[str]], key: str, default: str) -> str:
        values = params.get(key)
        return values[0] if values else default

    def _send_json(self, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the FocusGuard anti-distraction application locally."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind the local server.")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the local server.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), FocusRequestHandler)
    print(f"FocusGuard running at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
