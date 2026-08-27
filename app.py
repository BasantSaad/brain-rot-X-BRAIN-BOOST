from __future__ import annotations
#
import argparse
import json
import re
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from agent.langgraph_runtime import BbooLangGraphAgent
from services.app_service import BbooAppService
from shared.schemas import FocusPlan, utc_now_iso
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
        self.repository = MySQLRepository(MySQLConfig())
        self.service = BbooAppService(self.repository)
        self.assistant = BbooLangGraphAgent(self.service)
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
            if parsed.path == "/api/settings":
                self._handle_settings()
                return
            if parsed.path == "/api/plan-history":
                self._handle_plan_history()
                return
            if parsed.path == "/api/weekly-summary":
                self._handle_weekly_summary()
                return
            if parsed.path == "/api/checkins":
                self._handle_checkins()
                return
            if parsed.path == "/api/timers":
                self._handle_timers()
                return
            if parsed.path == "/api/app-usage":
                self._handle_app_usage()
                return
            if parsed.path == "/api/app-usage-detail":
                self._handle_app_usage_detail(parsed.query)
                return
            if parsed.path == "/api/children":
                self._handle_children()
                return
            if parsed.path == "/api/suggestions":
                self._handle_suggestions()
                return
            if parsed.path == "/api/agent/history":
                self._handle_agent_history()
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
            if parsed.path == "/api/logout-all-devices":
                self._handle_logout_all_devices()
                return
            if parsed.path == "/api/checkins":
                self._handle_record_checkin()
                return
            if parsed.path == "/api/app-usage":
                self._handle_save_app_usage()
                return
            if parsed.path == "/api/focus-timer/start":
                self._handle_timer_start()
                return
            if parsed.path == "/api/focus-timer/complete":
                self._handle_timer_complete()
                return
            if parsed.path == "/api/guardian-link":
                self._handle_guardian_link()
                return
            if parsed.path == "/api/agent/chat":
                self._handle_agent_chat()
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
            if parsed.path == "/api/settings":
                self._handle_update_settings()
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except RuntimeError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_dashboard(self, query: str) -> None:
        params = parse_qs(query)
        session = self._require_session()
        self._send_json(
            self.service.dashboard_payload(
                session=session,
                lang=self._single(params, "lang", session["lang"]),
                mode=self._single(params, "mode", session["mode"]),
            )
        )

    def _handle_plan(self, query: str) -> None:
        params = parse_qs(query)
        session = self._require_session()
        self._send_json(
            self.service.plan_payload(
                session=session,
                lang=self._single(params, "lang", session["lang"]),
            )
        )

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

    def _handle_settings(self) -> None:
        session = self._require_session()
        self._send_json({"settings": self.repository.load_settings(session["user_id"])})

    def _handle_plan_history(self) -> None:
        session = self._require_session()
        self._send_json({"items": self.repository.load_plan_history(session["user_id"])})

    def _handle_weekly_summary(self) -> None:
        session = self._require_session()
        self._send_json({"summary": self.repository.weekly_summary(session["user_id"])})

    def _handle_checkins(self) -> None:
        session = self._require_session()
        self._send_json({"items": self.repository.recent_checkins(session["user_id"])})

    def _handle_timers(self) -> None:
        session = self._require_session()
        self._send_json({"items": self.repository.recent_timers(session["user_id"])})

    def _handle_app_usage(self) -> None:
        session = self._require_session()
        self._send_json({"usage": self.repository.app_usage_summary(session["user_id"])})

    def _handle_app_usage_detail(self, query: str) -> None:
        session = self._require_session()
        params = parse_qs(query)
        app_name = self._single(params, "app", "").strip()
        if not app_name:
            raise ValueError("App name is required.")
        self._send_json({"detail": self.repository.app_usage_detail(session["user_id"], app_name)})

    def _handle_children(self) -> None:
        session = self._require_session()
        self._send_json({"items": self.repository.linked_children(session["user_id"])})

    def _handle_suggestions(self) -> None:
        session = self._require_session()
        settings = self.repository.load_settings(session["user_id"])
        self._send_json({"suggestions": self.repository.suggestion_engine(session["user_id"], settings)})

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

    def _handle_logout_all_devices(self) -> None:
        session = self._require_session()
        self.repository.delete_other_sessions(session["user_id"], session["token"])
        self._send_json({"ok": True, "message": "Other sessions were signed out."})

    def _handle_update_profile(self) -> None:
        session = self._require_session()
        payload = self._read_json()
        required = ["first_name", "last_name", "country", "lang", "audience", "mode", "permissions"]
        missing = [field for field in required if not str(payload.get(field, "")).strip()]
        if missing:
            self._send_json({"error": f"Missing required fields: {', '.join(missing)}"}, status=HTTPStatus.BAD_REQUEST)
            return
        payload["token"] = session["token"]
        updated_session = self.repository.update_profile(session["user_id"], payload)
        self._send_json({"session": updated_session})
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#update that happens in the setting page or the Assistant that can update the profile data for the user and save it in the MYSQL
    def _handle_update_settings(self) -> None:
        session = self._require_session()
        payload = self._read_json()
        #🚩🚩🚩🚩🚩🚩🚩🚩🚩🚩
        app_name = str(payload.get("app_name", "")).strip() or "Bboo"
        #-------------------------------------------------------------
        study_start = str(payload.get("study_start", "")).strip() or "16:00"
        bedtime_target = str(payload.get("bedtime_target", "")).strip() or "22:30"
        sleep_target_hours = int(payload.get("sleep_target_hours", 8))
        default_session_minutes = int(payload.get("default_session_minutes", 30))
        for value in [study_start, bedtime_target]:
            if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
                raise ValueError("Times must use HH:MM format.")
        if sleep_target_hours < 3 or sleep_target_hours > 12:
            raise ValueError("Sleep target must be between 3 and 12 hours.")
        if default_session_minutes < 10 or default_session_minutes > 120:
            raise ValueError("Default session minutes must be between 10 and 120.")
        settings = self.repository.update_settings(session["user_id"], {
            "app_name": app_name,
            "study_start": study_start,
            "bedtime_target": bedtime_target,
            "sleep_target_hours": sleep_target_hours,
            "default_session_minutes": default_session_minutes,
        })
        self._send_json({"settings": settings, "message": "Your app settings were updated."})
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#---=---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

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
        settings = self.repository.load_settings(session["user_id"])
        plan = FocusPlan(
            generated_at=utc_now_iso(),
            title=str(payload.get("title", "")).strip() or f"{settings['app_name']} focus recovery plan",
            recommended_session_minutes=minutes,
            focus_theme=str(payload.get("focus_theme", "")).strip() or "Electric momentum",
            steps=clean_steps or ["Start with one distraction-free session."],
            attention_game=str(payload.get("attention_game", "")).strip() or "Pattern Pulse: memorize the glowing sequence before the timer ends.",
        )
        saved = self.repository.save_focus_plan(session["user_id"], plan)
        self._send_json({"plan": saved.to_dict(), "message": "Your plan was saved to MySQL."})

    def _handle_record_checkin(self) -> None:
        session = self._require_session()
        payload = self._read_json()
        mood = int(payload.get("mood", 0))
        energy = int(payload.get("energy", 0))
        notes = str(payload.get("notes", "")).strip()
        if mood < 1 or mood > 5 or energy < 1 or energy > 5:
            raise ValueError("Mood and energy must be between 1 and 5.")
        self.repository.record_checkin(session["user_id"], mood, energy, notes)
        self._send_json({"items": self.repository.recent_checkins(session["user_id"]), "message": "Daily check-in saved."})

    def _handle_save_app_usage(self) -> None:
        session = self._require_session()
        payload = self._read_json()
        app_name = str(payload.get("app_name", "")).strip()
        usage_date = str(payload.get("usage_date", "")).strip()
        usage_hours = float(payload.get("usage_hours", 0))
        if not app_name:
            raise ValueError("Application name is required.")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", usage_date):
            raise ValueError("Usage date must use YYYY-MM-DD format.")
        if usage_hours < 0 or usage_hours > 24:
            raise ValueError("Usage hours must be between 0 and 24.")
        reminders = self.service.save_app_usage_with_reminders(
            session=session,
            app_name=app_name,
            usage_date=usage_date,
            usage_hours=usage_hours,
        )
        self._send_json(
            {
                "usage": self.repository.app_usage_summary(session["user_id"]),
                "message": self._app_usage_message(reminders),
                "reminders": reminders,
            }
        )

    def _handle_timer_start(self) -> None:
        session = self._require_session()
        payload = self._read_json()
        minutes = int(payload.get("minutes", 0))
        label = str(payload.get("label", "")).strip() or "Deep work session"
        if minutes < 10 or minutes > 120:
            raise ValueError("Timer minutes must be between 10 and 120.")
        self.repository.start_focus_timer(session["user_id"], minutes, label)
        self._send_json({"items": self.repository.recent_timers(session["user_id"]), "message": "Focus timer started."})

    def _handle_timer_complete(self) -> None:
        session = self._require_session()
        payload = self._read_json()
        timer_id = int(payload.get("timer_id", 0))
        completed = bool(payload.get("completed", True))
        if timer_id <= 0:
            raise ValueError("Timer id is required.")
        self.repository.complete_focus_timer(session["user_id"], timer_id, completed)
        self._send_json({"items": self.repository.recent_timers(session["user_id"]), "message": "Focus timer updated."})

    def _handle_guardian_link(self) -> None:
        session = self._require_session()
        payload = self._read_json()
        child_email = str(payload.get("child_email", "")).strip()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", child_email):
            raise ValueError("Please enter a valid child email address.")
        self.repository.link_child_account(session["user_id"], child_email)
        self._send_json({"items": self.repository.linked_children(session["user_id"]), "message": "Child account linked."})

    def _handle_agent_history(self) -> None:
        session = self._require_session()
        self._send_json({"items": self.repository.agent_history(session["user_id"])})

    def _handle_agent_chat(self) -> None:
        session = self._require_session()
        payload = self._read_json()
        message = str(payload.get("message", "")).strip()
        if not message:
            raise ValueError("Please enter a message for the assistant.")

        settings = self.repository.load_settings(session["user_id"])

        conversation_id = self.repository.ensure_agent_conversation(session["user_id"])
        self.repository.record_agent_message(conversation_id, "user", message)

        try:
            response = self.assistant.run(
                message=message,
                session=session,
                settings=settings,
            )
        except ValueError as exc:
            self.repository.record_agent_message(conversation_id, "assistant", str(exc), intent="error")
            raise

        self.repository.record_agent_message(
            conversation_id,
            "assistant",
            response["reply"],
            intent=response["intent"],
            tool_name=response.get("tool_name"),
        )
        if response.get("tool_name"):
            self.repository.record_agent_action(
                user_id=session["user_id"],
                conversation_id=conversation_id,
                tool_name=response["tool_name"],
                status=response["tool_status"],
                input_payload={"message": message},
                output_payload=response.get("action_payload", {}),
            )

        refreshed_settings = self.repository.load_settings(session["user_id"])
        refreshed_dashboard = self._build_dashboard_payload(session=session, lang=session["lang"], mode=session["mode"])
        self._send_json(
            {
                "assistant": response,
                "history": self.repository.agent_history(session["user_id"]),
                "settings": refreshed_settings,
                "dashboard": refreshed_dashboard,
            }
        )

    def _build_dashboard_payload(self, *, session: dict, lang: str, mode: str) -> dict:
        return self.service.dashboard_payload(session=session, lang=lang, mode=mode)

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

    def _app_usage_message(self, reminders: dict) -> str:
        if reminders.get("sent_thresholds"):
            return "App usage was saved and screen time reminder email was sent."
        if reminders.get("failed_thresholds"):
            return "App usage was saved, but the reminder email could not be sent."
        if reminders.get("skipped_thresholds"):
            return "App usage was saved. Configure SMTP settings to send screen time reminder emails."
        return "App usage was saved."

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
