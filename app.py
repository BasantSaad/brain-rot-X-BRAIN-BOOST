from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from agent.focus_engine import FocusCoachConfig, FocusCoachEngine
from simulator.behavior_simulator import BehaviorSimulationConfig, BehaviorSimulator
from storage.mysql_repository import MySQLConfig, MySQLRepository


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


def load_dotenv(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            __import__("os").environ.setdefault(key, value)


class BbooRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.engine = FocusCoachEngine(FocusCoachConfig())
        self.simulator = BehaviorSimulator(BehaviorSimulationConfig())
        self.repository = MySQLRepository(MySQLConfig())
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
            self._send_json({"status": "ok", "service": "bboo-demo"})
            return
        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/register":
            self._handle_register()
            return
        if parsed.path == "/api/login":
            self._handle_login()
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

    def _handle_dashboard(self, query: str) -> None:
        params = parse_qs(query)
        profile = self._build_profile(query)
        dashboard = self.engine.build_dashboard(
            profile=profile,
            language=self._single(params, "lang", "en"),
            mode=self._single(params, "mode", "user"),
        )
        self._send_json(dashboard.to_dict())

    def _handle_plan(self, query: str) -> None:
        params = parse_qs(query)
        profile = self._build_profile(query)
        plan = self.engine.build_personalized_plan(
            profile=profile,
            language=self._single(params, "lang", "en"),
        )
        self._send_json(plan.to_dict())

    def _handle_register(self) -> None:
        payload = self._read_json()
        required = ["first_name", "last_name", "email", "password", "country", "lang", "audience", "mode", "permissions"]
        missing = [field for field in required if not str(payload.get(field, "")).strip()]
        if missing:
            self._send_json({"error": f"Missing required fields: {', '.join(missing)}"}, status=HTTPStatus.BAD_REQUEST)
            return

        profile = self.simulator.build_profile(
            audience=payload["audience"],
            permissions_granted=str(payload["permissions"]).lower() == "true",
            first_name=payload["first_name"].strip(),
            last_name=payload["last_name"].strip(),
            email=payload["email"].strip(),
            country=payload["country"].strip(),
            preferred_language=payload["lang"].strip(),
            role=payload["mode"].strip(),
        )
        try:
            session = self.repository.create_user(payload=payload, profile=profile)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.CONFLICT)
            return
        self._send_json({"session": session}, status=HTTPStatus.CREATED)

    def _handle_login(self) -> None:
        payload = self._read_json()
        email = str(payload.get("email", "")).strip()
        password = str(payload.get("password", "")).strip()
        if not email or not password:
            self._send_json({"error": "Email and password are required."}, status=HTTPStatus.BAD_REQUEST)
            return
        try:
            session = self.repository.authenticate_user(
                email=email,
                password=password,
                language=str(payload.get("lang", "")).strip() or None,
            )
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.UNAUTHORIZED)
            return
        self._send_json({"session": session})

    def _build_profile(self, query: str):
        params = parse_qs(query)
        lang = self._single(params, "lang", "en")
        permissions = self._single(params, "permissions", "true").lower() == "true"
        audience = self._single(params, "audience", "student")
        email = self._single(params, "email", "")
        if email:
            stored_profile = self.repository.load_profile(email=email)
            if stored_profile is not None:
                return stored_profile
        return self.simulator.build_profile(
            audience=audience,
            permissions_granted=permissions,
            first_name=self._single(params, "first_name", ""),
            last_name=self._single(params, "last_name", ""),
            email=email,
            country=self._single(params, "country", "Egypt"),
            preferred_language=lang,
            role=self._single(params, "mode", "user"),
        )

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _single(self, params: dict[str, list[str]], key: str, default: str) -> str:
        values = params.get(key)
        return values[0] if values else default

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Bboo anti-distraction application locally.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind the local server.")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the local server.")
    return parser.parse_args()


def main() -> None:
    load_dotenv(BASE_DIR / ".env")
    args = parse_args()
    repository = MySQLRepository(MySQLConfig())
    repository.initialize()
    server = ThreadingHTTPServer((args.host, args.port), BbooRequestHandler)
    print(f"Bboo running at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
