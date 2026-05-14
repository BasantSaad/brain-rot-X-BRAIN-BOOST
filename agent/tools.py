from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(slots=True)
class AgentTool:
    name: str
    description: str
    handler: Callable[..., dict[str, Any]]


class BbooToolRegistry:
    def __init__(self, service) -> None:
        self.service = service
        self._tools = {
            "get_dashboard_summary": AgentTool(
                name="get_dashboard_summary",
                description="Load the current dashboard state for the signed-in user.",
                handler=self._dashboard_summary,
            ),
            "get_weekly_summary": AgentTool(
                name="get_weekly_summary",
                description="Load the user's weekly summary and streak data.",
                handler=self._weekly_summary,
            ),
            "get_suggestions": AgentTool(
                name="get_suggestions",
                description="Load best study time, sleep protection time, and risk window data.",
                handler=self._suggestions,
            ),
            "get_app_usage_summary": AgentTool(
                name="get_app_usage_summary",
                description="Load the 7-day app usage summary.",
                handler=self._app_usage_summary,
            ),
            "update_session_minutes": AgentTool(
                name="update_session_minutes",
                description="Update default focus session minutes in user settings.",
                handler=self._update_session_minutes,
            ),
            "update_app_name": AgentTool(
                name="update_app_name",
                description="Rename the application for the signed-in user.",
                handler=self._update_app_name,
            ),
            "update_bedtime_target": AgentTool(
                name="update_bedtime_target",
                description="Update the bedtime target time for the signed-in user.",
                handler=self._update_bedtime_target,
            ),
            "update_sleep_target_hours": AgentTool(
                name="update_sleep_target_hours",
                description="Update the sleep target hours for the signed-in user.",
                handler=self._update_sleep_target_hours,
            ),
            "start_focus_timer": AgentTool(
                name="start_focus_timer",
                description="Start a focus timer for the signed-in user.",
                handler=self._start_focus_timer,
            ),
            "stop_focus_timer": AgentTool(
                name="stop_focus_timer",
                description="Stop the current active focus timer for the signed-in user.",
                handler=self._stop_focus_timer,
            ),
        }

    def get(self, name: str) -> AgentTool:
        return self._tools[name]

    def names(self) -> list[str]:
        return list(self._tools)

    def _dashboard_summary(self, *, session: dict[str, Any], **_: Any) -> dict[str, Any]:
        return {"dashboard": self.service.dashboard_payload(session=session, lang=session["lang"], mode=session["mode"])}

    def _weekly_summary(self, *, session: dict[str, Any], **_: Any) -> dict[str, Any]:
        return {"summary": self.service.repository.weekly_summary(session["user_id"])}

    def _suggestions(self, *, session: dict[str, Any], **_: Any) -> dict[str, Any]:
        settings = self.service.repository.load_settings(session["user_id"])
        return {"suggestions": self.service.repository.suggestion_engine(session["user_id"], settings)}

    def _app_usage_summary(self, *, session: dict[str, Any], **_: Any) -> dict[str, Any]:
        return {"usage": self.service.repository.app_usage_summary(session["user_id"])}

    def _update_session_minutes(self, *, session: dict[str, Any], minutes: int, **_: Any) -> dict[str, Any]:
        return {"settings": self.service.update_settings_field(session["user_id"], "default_session_minutes", minutes)}

    def _update_app_name(self, *, session: dict[str, Any], app_name: str, **_: Any) -> dict[str, Any]:
        return {"settings": self.service.update_settings_field(session["user_id"], "app_name", app_name)}

    def _update_bedtime_target(self, *, session: dict[str, Any], bedtime_target: str, **_: Any) -> dict[str, Any]:
        return {"settings": self.service.update_settings_field(session["user_id"], "bedtime_target", bedtime_target)}

    def _update_sleep_target_hours(self, *, session: dict[str, Any], sleep_target_hours: int, **_: Any) -> dict[str, Any]:
        return {"settings": self.service.update_settings_field(session["user_id"], "sleep_target_hours", sleep_target_hours)}

    def _start_focus_timer(self, *, session: dict[str, Any], minutes: int, label: str, **_: Any) -> dict[str, Any]:
        self.service.repository.start_focus_timer(session["user_id"], minutes, label)
        return {"timers": self.service.repository.recent_timers(session["user_id"])}

    def _stop_focus_timer(self, *, session: dict[str, Any], completed: bool = False, **_: Any) -> dict[str, Any]:
        active_timer = self.service.repository.active_timer(session["user_id"])
        if not active_timer:
            raise ValueError("There is no active focus timer to stop right now.")
        self.service.repository.complete_focus_timer(session["user_id"], active_timer["id"], completed)
        return {
            "stopped_timer": active_timer,
            "timers": self.service.repository.recent_timers(session["user_id"]),
        }
