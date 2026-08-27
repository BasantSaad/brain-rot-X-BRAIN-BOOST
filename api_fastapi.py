from __future__ import annotations

import re
from typing import Any

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from agent.langgraph_runtime import BbooLangGraphAgent
from app import BASE_DIR, STATIC_DIR, load_dotenv
from services.app_service import BbooAppService
from shared.schemas import FocusPlan, utc_now_iso
from storage.mysql_repository import MySQLConfig, MySQLRepository


load_dotenv(BASE_DIR / ".env")
repository = MySQLRepository(MySQLConfig())
repository.initialize()
service = BbooAppService(repository)
agent_runtime = BbooLangGraphAgent(service)

app = FastAPI(title="Bboo Agent API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def no_store_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})


@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.exception_handler(RuntimeError)
async def runtime_error_handler(_: Request, exc: RuntimeError):
    return JSONResponse(status_code=500, content={"error": str(exc)})


def require_session(authorization: str | None) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Please log in again. Your session token is missing.")
    token = authorization[len("Bearer "):].strip()
    try:
        return repository.load_session(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def optional_token(authorization: str | None) -> str | None:
    if authorization and authorization.startswith("Bearer "):
        return authorization[len("Bearer "):].strip() or None
    return None


def validate_registration_payload(payload: dict[str, Any]) -> None:
    email = str(payload.get("email", "")).strip()
    password = str(payload.get("password", ""))
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")
    if not re.search(r"[A-Za-z]", password):
        raise HTTPException(status_code=400, detail="Password must include at least one letter.")
    if not re.search(r"\d", password):
        raise HTTPException(status_code=400, detail="Password must include at least one number.")


def ensure_required(payload: dict[str, Any], fields: list[str]) -> None:
    missing = [field for field in fields if not str(payload.get(field, "")).strip()]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required fields: {', '.join(missing)}")


def profile_payload(session: dict[str, Any]) -> dict[str, Any]:
    profile = repository.load_profile_by_user_id(session["user_id"])
    if profile is None:
        raise HTTPException(status_code=401, detail="We could not find your profile. Please log in again.")
    return {
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
    }


@app.get("/")
def root() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/dashboard.html")
def dashboard_page() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "dashboard.html"))


@app.get("/assistant.html")
def assistant_page() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "assistant.html"))


@app.get("/usage.html")
def usage_page() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "usage.html"))


@app.get("/profile.html")
def profile_page() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "profile.html"))


@app.get("/summary.html")
def summary_page() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "summary.html"))


@app.get("/checkins.html")
def checkins_page() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "checkins.html"))


@app.get("/plan.html")
def plan_page() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "plan.html"))


@app.get("/insights.html")
def insights_page() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "insights.html"))


@app.get("/styles.css")
def styles_asset() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "styles.css"))


@app.get("/dashboard.js")
def dashboard_script() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "dashboard.js"))


@app.get("/auth.js")
def auth_script() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "auth.js"))


@app.get("/icon.svg")
def icon_asset() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "icon.svg"))


@app.post("/api/register")
def register(payload: dict[str, Any]):
    ensure_required(payload, ["first_name", "last_name", "email", "password", "country", "lang", "audience", "mode", "permissions"])
    validate_registration_payload(payload)
    profile = service.simulator.build_profile(
        audience=payload["audience"],
        permissions_granted=str(payload["permissions"]).lower() == "true",
        first_name=str(payload["first_name"]).strip(),
        last_name=str(payload["last_name"]).strip(),
        email=str(payload["email"]).strip(),
        country=str(payload["country"]).strip(),
        preferred_language=str(payload["lang"]).strip(),
        role=str(payload["mode"]).strip(),
    )
    try:
        session = repository.create_user(payload=payload, profile=profile)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return JSONResponse(status_code=201, content={"session": session})


@app.post("/api/login")
def login(payload: dict[str, Any]):
    email = str(payload.get("email", "")).strip()
    password = str(payload.get("password", "")).strip()
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required.")
    try:
        session = repository.authenticate_user(
            email=email,
            password=password,
            language=str(payload.get("lang", "")).strip() or None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return {"session": session}


@app.post("/api/logout")
def logout(authorization: str | None = Header(default=None)):
    token = optional_token(authorization)
    if token:
        repository.delete_session(token)
    return {"ok": True}


@app.post("/api/logout-all-devices")
def logout_all_devices(authorization: str | None = Header(default=None)):
    session = require_session(authorization)
    repository.delete_other_sessions(session["user_id"], session["token"])
    return {"ok": True, "message": "Other sessions were signed out."}


@app.get("/api/profile")
def get_profile(authorization: str | None = Header(default=None)):
    session = require_session(authorization)
    return profile_payload(session)

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#update that happens in the setting page or the Assistant that can update the setting for the user and save it in the MYSQL
@app.put("/api/profile")
def update_profile(payload: dict[str, Any], authorization: str | None = Header(default=None)):
    session = require_session(authorization)
    ensure_required(payload, ["first_name", "last_name", "country", "lang", "audience", "mode", "permissions"])
    payload["token"] = session["token"]
    updated_session = repository.update_profile(session["user_id"], payload)
    return {"session": updated_session}


@app.get("/api/dashboard")
def get_dashboard(lang: str = "en", mode: str = "user", authorization: str | None = Header(default=None)):
    session = require_session(authorization)
    return service.dashboard_payload(session=session, lang=lang or session["lang"], mode=mode or session["mode"])


@app.get("/api/plan")
def get_plan(lang: str = "en", authorization: str | None = Header(default=None)):
    session = require_session(authorization)
    return service.plan_payload(session=session, lang=lang or session["lang"])


@app.put("/api/plan")
def save_plan(payload: dict[str, Any], authorization: str | None = Header(default=None)):
    session = require_session(authorization)
    steps = payload.get("steps", [])
    if not isinstance(steps, list):
        raise HTTPException(status_code=400, detail="Plan steps must be a list of lines.")
    clean_steps = [str(step).strip() for step in steps if str(step).strip()]
    minutes = int(payload.get("recommended_session_minutes", 0))
    if minutes < 10 or minutes > 120:
        raise HTTPException(status_code=400, detail="Session minutes must be between 10 and 120.")
    settings = repository.load_settings(session["user_id"])
    plan = FocusPlan(
        generated_at=utc_now_iso(),
        title=str(payload.get("title", "")).strip() or f"{settings['app_name']} focus recovery plan",
        recommended_session_minutes=minutes,
        focus_theme=str(payload.get("focus_theme", "")).strip() or "Electric momentum",
        steps=clean_steps or ["Start with one distraction-free session."],
        attention_game=str(payload.get("attention_game", "")).strip() or "Pattern Pulse: memorize the glowing sequence before the timer ends.",
    )
    saved = repository.save_focus_plan(session["user_id"], plan)
    return {"plan": saved.to_dict(), "message": "Your plan was saved to MySQL."}


@app.get("/api/settings")
def get_settings(authorization: str | None = Header(default=None)):
    session = require_session(authorization)
    return {"settings": repository.load_settings(session["user_id"])}


#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#update that happens in the setting page or the Assistant that can update the profile data for the user and save it in the MYSQL
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.put("/api/settings")
#_handle_update_settings in app.py or in fastapi.py both of them can update the setting for the user and save it in the MYSQL, but the one in the fastapi.py is more complete and have more validation for the input data, so we will keep the one in the fastapi.py and remove the one in the app.py
def update_settings(payload: dict[str, Any], authorization: str | None = Header(default=None)):
    session = require_session(authorization)
    #🚩🚩🚩 need to removed
    app_name = str(payload.get("app_name", "")).strip() or "Bboo"
    #===------------------------------------------
    study_start = str(payload.get("study_start", "")).strip() or "16:00"
    bedtime_target = str(payload.get("bedtime_target", "")).strip() or "22:30"
    sleep_target_hours = int(payload.get("sleep_target_hours", 8))
    default_session_minutes = int(payload.get("default_session_minutes", 30))
    for value in [study_start, bedtime_target]:
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
            raise HTTPException(status_code=400, detail="Times must use HH:MM format.")
    if sleep_target_hours < 3 or sleep_target_hours > 12:
        raise HTTPException(status_code=400, detail="Sleep target must be between 5 and 12 hours.")
    if default_session_minutes < 10 or default_session_minutes > 120:
        raise HTTPException(status_code=400, detail="Default session minutes must be between 10 and 120.")
    settings = repository.update_settings(
        session["user_id"],
        {
            "app_name": app_name,
            "study_start": study_start,
            "bedtime_target": bedtime_target,
            "sleep_target_hours": sleep_target_hours,
            "default_session_minutes": default_session_minutes,
        },
    )
    return {"settings": settings, "message": "Your app settings were updated."}
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@app.get("/api/plan-history")
def get_plan_history(authorization: str | None = Header(default=None)):
    session = require_session(authorization)
    return {"items": repository.load_plan_history(session["user_id"])}

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#weekly summary retrieval----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#it used in the Dashboard page and the Assistant can show the weekly summary to the user,
@app.get("/api/weekly-summary")
def get_weekly_summary(authorization: str | None = Header(default=None)):
    session = require_session(authorization)
    return {"summary": repository.weekly_summary(session["user_id"])}
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@app.get("/api/checkins")
def get_checkins(authorization: str | None = Header(default=None)):
    session = require_session(authorization)
    return {"items": repository.recent_checkins(session["user_id"])}


@app.post("/api/checkins")
def record_checkin(payload: dict[str, Any], authorization: str | None = Header(default=None)):
    session = require_session(authorization)
    mood = int(payload.get("mood", 0))
    energy = int(payload.get("energy", 0))
    notes = str(payload.get("notes", "")).strip()
    if mood < 1 or mood > 5 or energy < 1 or energy > 5:
        raise HTTPException(status_code=400, detail="Mood and energy must be between 1 and 5.")
    repository.record_checkin(session["user_id"], mood, energy, notes)
    return {"items": repository.recent_checkins(session["user_id"]), "message": "Daily check-in saved."}


@app.get("/api/timers")
def get_timers(authorization: str | None = Header(default=None)):
    session = require_session(authorization)
    return {"items": repository.recent_timers(session["user_id"])}


@app.post("/api/focus-timer/start")
def start_timer(payload: dict[str, Any], authorization: str | None = Header(default=None)):
    session = require_session(authorization)
    minutes = int(payload.get("minutes", 0))
    label = str(payload.get("label", "")).strip() or "Deep work session"
    if minutes < 10 or minutes > 120:
        raise HTTPException(status_code=400, detail="Timer minutes must be between 10 and 120.")
    repository.start_focus_timer(session["user_id"], minutes, label)
    return {"items": repository.recent_timers(session["user_id"]), "message": "Focus timer started."}


@app.post("/api/focus-timer/complete")
def complete_timer(payload: dict[str, Any], authorization: str | None = Header(default=None)):
    session = require_session(authorization)
    timer_id = int(payload.get("timer_id", 0))
    completed = bool(payload.get("completed", True))
    if timer_id <= 0:
        raise HTTPException(status_code=400, detail="Timer id is required.")
    repository.complete_focus_timer(session["user_id"], timer_id, completed)
    return {"items": repository.recent_timers(session["user_id"]), "message": "Focus timer updated."}


@app.get("/api/app-usage")
def get_app_usage(authorization: str | None = Header(default=None)):
    session = require_session(authorization)
    return {"usage": repository.app_usage_summary(session["user_id"])}


@app.get("/api/app-usage-detail")
def get_app_usage_detail(app: str = "", authorization: str | None = Header(default=None)):
    session = require_session(authorization)
    app_name = app.strip()
    if not app_name:
        raise HTTPException(status_code=400, detail="App name is required.")
    return {"detail": repository.app_usage_detail(session["user_id"], app_name)}


@app.post("/api/app-usage")
def save_app_usage(payload: dict[str, Any], authorization: str | None = Header(default=None)):
    session = require_session(authorization)
    app_name = str(payload.get("app_name", "")).strip()
    usage_date = str(payload.get("usage_date", "")).strip()
    usage_hours = float(payload.get("usage_hours", 0))
    if not app_name:
        raise HTTPException(status_code=400, detail="Application name is required.")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", usage_date):
        raise HTTPException(status_code=400, detail="Usage date must use YYYY-MM-DD format.")
    if usage_hours < 0 or usage_hours > 24:
        raise HTTPException(status_code=400, detail="Usage hours must be between 0 and 24.")
    reminders = service.save_app_usage_with_reminders(
        session=session,
        app_name=app_name,
        usage_date=usage_date,
        usage_hours=usage_hours,
    )
    if reminders["sent_thresholds"]:
        message = "App usage was saved and screen time reminder email was sent."
    elif reminders["failed_thresholds"]:
        message = "App usage was saved, but the reminder email could not be sent."
    elif reminders["skipped_thresholds"]:
        message = "App usage was saved. Configure SMTP settings to send screen time reminder emails."
    else:
        message = "App usage was saved."
    return {"usage": repository.app_usage_summary(session["user_id"]), "message": message, "reminders": reminders}


@app.get("/api/children")
def get_children(authorization: str | None = Header(default=None)):
    session = require_session(authorization)
    return {"items": repository.linked_children(session["user_id"])}


@app.post("/api/guardian-link")
def guardian_link(payload: dict[str, Any], authorization: str | None = Header(default=None)):
    session = require_session(authorization)
    child_email = str(payload.get("child_email", "")).strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", child_email):
        raise HTTPException(status_code=400, detail="Please enter a valid child email address.")
    repository.link_child_account(session["user_id"], child_email)
    return {"items": repository.linked_children(session["user_id"]), "message": "Child account linked."}


@app.get("/api/suggestions")
def get_suggestions(authorization: str | None = Header(default=None)):
    session = require_session(authorization)
    settings = repository.load_settings(session["user_id"])
    return {"suggestions": repository.suggestion_engine(session["user_id"], settings)}


@app.post("/api/agent/chat")
def agent_chat(payload: dict[str, Any], authorization: str | None = Header(default=None)) -> dict[str, Any]:
    session = require_session(authorization)
    message = str(payload.get("message", "")).strip()
    if not message:
        raise HTTPException(status_code=400, detail="Please enter a message for the assistant.")
    settings = repository.load_settings(session["user_id"])
    conversation_id = repository.ensure_agent_conversation(session["user_id"])
    repository.record_agent_message(conversation_id, "user", message)
    response = agent_runtime.run(message=message, session=session, settings=settings)
    repository.record_agent_message(
        conversation_id,
        "assistant",
        response["reply"],
        intent=response["intent"],
        tool_name=response.get("tool_name"),
    )
    if response.get("tool_name"):
        repository.record_agent_action(
            user_id=session["user_id"],
            conversation_id=conversation_id,
            tool_name=response["tool_name"],
            status=response["tool_status"],
            input_payload={"message": message},
            output_payload=response.get("action_payload", {}),
        )
    return {
        "assistant": response,
        "history": repository.agent_history(session["user_id"]),
        "settings": repository.load_settings(session["user_id"]),
        "dashboard": service.dashboard_payload(session=session, lang=session["lang"], mode=session["mode"]),
    }


@app.get("/api/agent/history")
def agent_history(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    session = require_session(authorization)
    return {"items": repository.agent_history(session["user_id"])}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "bboo-fastapi"}


if __name__ == "__main__":
    uvicorn.run("api_fastapi:app", host="127.0.0.1", port=8010, reload=False)
