from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn

from agent.langgraph_runtime import LocalLangGraphAgent
from app import BASE_DIR, STATIC_DIR, load_dotenv
from services.app_service import BbooAppService
from storage.mysql_repository import MySQLConfig, MySQLRepository


load_dotenv(BASE_DIR / ".env")
repository = MySQLRepository(MySQLConfig())
repository.initialize()
service = BbooAppService(repository)
agent_runtime = LocalLangGraphAgent(service)

app = FastAPI(title="Bboo Agent API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_session(authorization: str | None) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Please log in again. Your session token is missing.")
    token = authorization[len("Bearer "):].strip()
    try:
        return repository.load_session(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


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
