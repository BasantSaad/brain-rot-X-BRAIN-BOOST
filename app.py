from __future__ import annotations

import argparse
import json
import re
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from agent.focus_engine import FocusCoachConfig, FocusCoachEngine
from shared.schemas import FocusPlan, utc_now_iso
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
        try:
            if parsed.path == "/api/dashboard":
                self._handle_dashboard(parsed.query)
                return
            if parsed.path == "/api/plan":
                self._handle_plan(parsed.query)
                return
            if parsed.path == "/api/profile":
                self._handle_profile()
                return
            if parsed.path == "/api/health":
                self._send_json({"status": "ok", "service": "bboo-demo"})
                return
            if parsed.path == "/":
                self.path = "/index.html"
            return super().do_GET()
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.UNAUTHORIZED)
        except RuntimeError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/register":
                self._handle_register()
                return
            if parsed.path == "/api/login":
                self._handle_login()
                return
            if parsed.path == "/api/logout":
                self._handle_logout()
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except RuntimeError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_PUT(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/profile":
                self._handle_update_profile()
                return
            if parsed.path == "/api/plan":
                self._handle_save_plan()
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except RuntimeError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_dashboard(self, query: str) -> None:
        params = parse_qs(query)
        session = self._require_session()
        profile = self._build_profile(query, session["user_id"])
        dashboard = self.engine.build_dashboard(
            profile=profile,
            language=self._single(params, "lang", session["lang"]),
            mode=self._single(params, "mode", session["mode"]),
        )
        self._send_json(dashboard.to_dict())

    def _handle_plan(self, query: str) -> None:
        params = parse_qs(query)
        session = self._require_session()
        profile = self._build_profile(query, session["user_id"])
        plan = self.repository.load_focus_plan(session["user_id"]) or self.engine.build_personalized_plan(
            profile=profile,
            language=self._single(params, "lang", session["lang"]),
        )
        self._send_json(plan.to_dict())

    def _handle_profile(self) -> None:
        session = self._require_session()
        profile = self.repository.load_profile_by_user_id(session["user_id"])
        if profile is None:
            raise ValueError("We could not find your profile. Please log in again.")
        self._send_json({
            "profile": {
                "first_name": profile.account.first_name,
                "last_name": profile.account.last_name,
                "email": profile.account.email,
                "country": profile.account.country,
                "lang": profile.account.preferred_language,
                "audience": session["audience"],
                "mode": profile.account.role,
                "permissions": str(profile.permissions_granted).lower(),
            }
        })

    def _handle_register(self) -> None:
        payload = self._read_json()
        required = ["first_name", "last_name", "email", "password", "country", "lang", "audience", "mode", "permissions"]
        missing = [field for field in required if not str(payload.get(field, "")).strip()]
        if missing:
            self._send_json({"error": f"Missing required fields: {', '.join(missing)}"}, status=HTTPStatus.BAD_REQUEST)
            return
        self._validate_registration_payload(payload)

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

    def _handle_logout(self) -> None:
        token = self._bearer_token()
        if not token:
            self._send_json({"ok": True})
            return
        self.repository.delete_session(token)
        self._send_json({"ok": True})

    def _handle_update_profile(self) -> None:
        session = self._require_session()
        payload = self._read_json()
        required = ["first_name", "last_name", "country", "lang", "audience", "mode", "permissions"]
        missing = [field for field in required if not str(payload.get(field, "")).strip()]
        if missing:
            self._send_json({"error": f"Missing required fields: {', '.join(missing)}"}, status=HTTPStatus.BAD_REQUEST)
            return
        payload["token"] = session["token"]
        updated_session = self.repository.update_profile(user_id=session["user_id"], payload=payload)
        self._send_json({"session": updated_session})

    def _handle_save_plan(self) -> None:
        session = self._require_session()
        payload = self._read_json()
        steps = payload.get("steps", [])
        if not isinstance(steps, list):
            raise ValueError("Plan steps must be a list of lines.")
        clean_steps = [str(step).strip() for step in steps if str(step).strip()]
        minutes = int(payload.get("recommended_session_minutes", 0))
        if minutes < 10 or minutes > 120:
            raise ValueError("Session minutes must be between 10 and 120.")
        plan = FocusPlan(
            generated_at=utc_now_iso(),
            title=str(payload.get("title", "")).strip() or "Bboo focus recovery plan",
            recommended_session_minutes=minutes,
            focus_theme=str(payload.get("focus_theme", "")).strip() or "Electric momentum",
            steps=clean_steps or ["Start with one distraction-free session."],
            attention_game=str(payload.get("attention_game", "")).strip() or "Pattern Pulse: memorize the glowing sequence before the timer ends.",
        )
        saved = self.repository.save_focus_plan(user_id=session["user_id"], plan=plan)
        self._send_json({"plan": saved.to_dict(), "message": "Your plan was saved to MySQL."})

    def _build_profile(self, query: str, user_id: int | None = None):
        params = parse_qs(query)
        lang = self._single(params, "lang", "en")
        permissions = self._single(params, "permissions", "true").lower() == "true"
        audience = self._single(params, "audience", "student")
        if user_id is not None:
            stored_profile = self.repository.load_profile_by_user_id(user_id)
            if stored_profile is not None:
                return stored_profile
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

    def _bearer_token(self) -> str | None:
        header = self.headers.get("Authorization", "")
        prefix = "Bearer "
        if header.startswith(prefix):
            return header[len(prefix):].strip() or None
        return None

    def _require_session(self) -> dict:
        token = self._bearer_token()
        if not token:
            raise ValueError("Please log in again. Your session token is missing.")
        return self.repository.load_session(token)

    def _validate_registration_payload(self, payload: dict) -> None:
        email = str(payload.get("email", "")).strip()
        password = str(payload.get("password", ""))
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("Please enter a valid email address.")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Za-z]", password):
            raise ValueError("Password must include at least one letter.")
        if not re.search(r"\d", password):
            raise ValueError("Password must include at least one number.")

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            return


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
