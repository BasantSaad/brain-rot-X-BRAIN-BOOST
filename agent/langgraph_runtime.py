from __future__ import annotations

import re
from dataclasses import dataclass, field
import os
from typing import Any

from agent.ollama_client import OllamaPlannerClient
from agent.rag_store import LocalChromaStore
from agent.tools import BbooToolRegistry


@dataclass(slots=True)
class GraphState:
    user_message: str
    session: dict[str, Any]
    settings: dict[str, Any]
    intent: str = "fallback"
    tool_name: str | None = None
    tool_args: dict[str, Any] = field(default_factory=dict)
    retrieved_context: list[dict[str, Any]] = field(default_factory=list)
    tool_result: dict[str, Any] = field(default_factory=dict)
    reply: str = ""


class LocalLangGraphAgent:
    """A small state-machine that mirrors a LangGraph-style agent workflow offline."""

    def __init__(self, service) -> None:
        self.service = service
        self.rag_store = LocalChromaStore()
        self.tools = BbooToolRegistry(service)
        self.provider = os.getenv("BBOO_LLM_PROVIDER", "local").strip().lower()
        self.ollama = OllamaPlannerClient()

    def run(self, *, message: str, session: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
        state = GraphState(user_message=message.strip(), session=session, settings=settings)
        self._retrieve_context(state)
        self._plan(state)
        self._execute_tool(state)
        self._compose_reply(state)
        return {
            "reply": state.reply,
            "intent": state.intent,
            "tool_name": state.tool_name,
            "tool_status": "success" if state.tool_name else "none",
            "action_payload": state.tool_result,
            "retrieved_notes": state.retrieved_context,
        }

    def _retrieve_context(self, state: GraphState) -> None:
        state.retrieved_context = self.rag_store.query(state.user_message, limit=2)

    def _plan(self, state: GraphState) -> None:
        if self._force_direct_action(state):
            return
        if self.provider == "ollama":
            try:
                self._plan_with_ollama(state)
                if self._normalize_planned_action(state):
                    return
                if state.tool_name:
                    return
                return
            except RuntimeError:
                pass
        self._plan_intent(state)
        self._select_tool(state)

    def _force_direct_action(self, state: GraphState) -> bool:
        lowered = state.user_message.lower()

        timer_match = re.search(r"(?:start|begin)\s+(?:a\s+)?(?:focus\s+)?timer(?:\s+for)?\D{0,10}(\d{1,3})", lowered)
        if timer_match:
            state.intent = "start_focus_timer"
            state.tool_name = "start_focus_timer"
            state.tool_args = {
                "minutes": max(10, min(180, int(timer_match.group(1)))),
                "label": "Agent-started focus timer",
            }
            return True

        stop_timer_match = re.search(r"\b(stop|end|finish|cancel)\b.*\b(timer|session)\b", lowered)
        if stop_timer_match or lowered.strip() in {"stop it", "end it", "finish it", "cancel it"}:
            state.intent = "stop_focus_timer"
            state.tool_name = "stop_focus_timer"
            state.tool_args = {"completed": False}
            return True

        session_match = re.search(r"(?:change|set|update)\s+.*(?:session|focus)\s+(?:time|minutes?)\D{0,10}(\d{1,3})", lowered)
        if session_match:
            state.intent = "update_session_minutes"
            state.tool_name = "update_session_minutes"
            state.tool_args = {"minutes": max(10, min(120, int(session_match.group(1))))}
            return True

        rename_match = re.search(r"(?:rename|change|set)\s+(?:the\s+)?app(?:lication)?\s+name\s+(?:to\s+)?(.+)", state.user_message, re.IGNORECASE)
        if rename_match:
            state.intent = "update_app_name"
            state.tool_name = "update_app_name"
            state.tool_args = {"app_name": rename_match.group(1).strip().strip(".")[:120] or "Bboo"}
            return True

        bedtime_match = re.search(r"(?:set|change|move|update)\s+.*(?:bedtime|sleep protection time|sleep time).{0,16}?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", lowered)
        if bedtime_match:
            hour = int(bedtime_match.group(1))
            minute = int(bedtime_match.group(2) or 0)
            meridiem = bedtime_match.group(3)
            if meridiem == "pm" and hour < 12:
                hour += 12
            if meridiem == "am" and hour == 12:
                hour = 0
            state.intent = "update_bedtime_target"
            state.tool_name = "update_bedtime_target"
            state.tool_args = {"bedtime_target": f"{hour:02d}:{minute:02d}"}
            return True

        sleep_target_match = re.search(r"(?:set|change|update)\s+.*sleep\s+(?:target|goal|hours?).{0,12}?(\d{1,2})", lowered)
        if sleep_target_match:
            state.intent = "update_sleep_target_hours"
            state.tool_name = "update_sleep_target_hours"
            state.tool_args = {"sleep_target_hours": max(4, min(12, int(sleep_target_match.group(1))))}
            return True

        return False

    def _normalize_planned_action(self, state: GraphState) -> bool:
        lowered = state.user_message.lower()
        if "timer" in lowered and any(word in lowered for word in ("start", "begin")):
            match = re.search(r"(\d{1,3})", lowered)
            state.intent = "start_focus_timer"
            state.tool_name = "start_focus_timer"
            state.tool_args = {
                "minutes": max(10, min(180, int(match.group(1)) if match else 25)),
                "label": "Agent-started focus timer",
            }
            return True
        if any(phrase in lowered for phrase in ("stop timer", "end timer", "finish timer", "cancel timer", "stop it", "end it", "finish it", "cancel it")):
            state.intent = "stop_focus_timer"
            state.tool_name = "stop_focus_timer"
            state.tool_args = {"completed": False}
            return True
        return False

    def _plan_with_ollama(self, state: GraphState) -> None:
        available_tools = [
            {"name": name, "description": self.tools.get(name).description}
            for name in self.tools.names()
        ]
        planned = self.ollama.plan(
            message=state.user_message,
            session=state.session,
            settings=state.settings,
            retrieved_context=state.retrieved_context,
            available_tools=available_tools,
        )
        state.intent = planned["intent"]
        state.tool_name = planned["tool_name"]
        state.tool_args = planned["tool_args"] if isinstance(planned["tool_args"], dict) else {}
        if planned["reply"]:
            state.reply = planned["reply"]

    def _plan_intent(self, state: GraphState) -> None:
        lowered = state.user_message.lower()
        if re.search(r"(?:session|focus)\s+(?:time|minutes?)\D{0,10}(\d{2,3})", lowered):
            state.intent = "update_session_minutes"
            return
        if re.search(r"(?:rename|change)\s+(?:the\s+)?app(?:lication)?\s+name", lowered):
            state.intent = "update_app_name"
            return
        if "bedtime" in lowered or "sleep protection time" in lowered:
            state.intent = "update_bedtime_target"
            return
        if re.search(r"sleep\s+(?:target|goal|hours?)", lowered):
            state.intent = "update_sleep_target_hours"
            return
        if "start" in lowered and "timer" in lowered:
            state.intent = "start_focus_timer"
            return
        if any(phrase in lowered for phrase in ("weekly summary", "weekly progress", "show my progress")):
            state.intent = "get_weekly_summary"
            return
        if any(phrase in lowered for phrase in ("focus score", "brain state", "how am i doing")):
            state.intent = "get_dashboard_summary"
            return
        if any(phrase in lowered for phrase in ("best study time", "risk window", "sleep protection")):
            state.intent = "get_suggestions"
            return
        if any(phrase in lowered for phrase in ("app usage", "screen time", "most used app")):
            state.intent = "get_app_usage_summary"

    def _select_tool(self, state: GraphState) -> None:
        lowered = state.user_message.lower()
        if state.intent == "update_session_minutes":
            match = re.search(r"(?:session|focus)\s+(?:time|minutes?)\D{0,10}(\d{2,3})", lowered)
            minutes = int(match.group(1)) if match else 30
            state.tool_name = "update_session_minutes"
            state.tool_args = {"minutes": max(10, min(120, minutes))}
        elif state.intent == "update_app_name":
            match = re.search(r"(?:rename|change)\s+(?:the\s+)?app(?:lication)?\s+name\s+(?:to\s+)?(.+)", state.user_message, re.IGNORECASE)
            state.tool_name = "update_app_name"
            state.tool_args = {"app_name": (match.group(1).strip().strip(".") if match else "Bboo")[:120]}
        elif state.intent == "update_bedtime_target":
            match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", lowered)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2) or 0)
                meridiem = match.group(3)
                if meridiem == "pm" and hour < 12:
                    hour += 12
                if meridiem == "am" and hour == 12:
                    hour = 0
                state.tool_name = "update_bedtime_target"
                state.tool_args = {"bedtime_target": f"{hour:02d}:{minute:02d}"}
        elif state.intent == "update_sleep_target_hours":
            match = re.search(r"sleep\s+(?:target|goal|hours?).{0,12}?(\d{1,2})", lowered)
            if match:
                state.tool_name = "update_sleep_target_hours"
                state.tool_args = {"sleep_target_hours": max(4, min(12, int(match.group(1))))}
        elif state.intent == "start_focus_timer":
            match = re.search(r"(\d{2,3})", lowered)
            minutes = int(match.group(1)) if match else 25
            state.tool_name = "start_focus_timer"
            state.tool_args = {"minutes": max(10, min(180, minutes)), "label": "Agent-started focus timer"}
        elif state.intent == "stop_focus_timer":
            state.tool_name = "stop_focus_timer"
            state.tool_args = {"completed": False}
        elif state.intent in self.tools.names():
            state.tool_name = state.intent

    def _execute_tool(self, state: GraphState) -> None:
        if not state.tool_name:
            return
        if state.tool_name not in self.tools.names():
            state.tool_name = None
            state.tool_args = {}
            state.intent = "fallback"
            return
        self._hydrate_missing_tool_args(state)
        tool = self.tools.get(state.tool_name)
        state.tool_result = tool.handler(session=state.session, **state.tool_args)

    def _hydrate_missing_tool_args(self, state: GraphState) -> None:
        lowered = state.user_message.lower()
        if state.tool_name == "start_focus_timer":
            match = re.search(r"(\d{1,3})", lowered)
            state.tool_args.setdefault("minutes", max(10, min(180, int(match.group(1)) if match else 25)))
            state.tool_args.setdefault("label", "Agent-started focus timer")
        elif state.tool_name == "stop_focus_timer":
            state.tool_args.setdefault("completed", False)
        elif state.tool_name == "update_session_minutes":
            match = re.search(r"(\d{1,3})", lowered)
            if match:
                state.tool_args.setdefault("minutes", max(10, min(120, int(match.group(1)))))
        elif state.tool_name == "update_app_name":
            match = re.search(r"(?:rename|change|set)\s+(?:the\s+)?app(?:lication)?\s+name\s+(?:to\s+)?(.+)", state.user_message, re.IGNORECASE)
            if match:
                state.tool_args.setdefault("app_name", match.group(1).strip().strip(".")[:120] or "Bboo")
        elif state.tool_name == "update_bedtime_target":
            match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", lowered)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2) or 0)
                meridiem = match.group(3)
                if meridiem == "pm" and hour < 12:
                    hour += 12
                if meridiem == "am" and hour == 12:
                    hour = 0
                state.tool_args.setdefault("bedtime_target", f"{hour:02d}:{minute:02d}")
        elif state.tool_name == "update_sleep_target_hours":
            match = re.search(r"(\d{1,2})", lowered)
            if match:
                state.tool_args.setdefault("sleep_target_hours", max(4, min(12, int(match.group(1)))))

    def _compose_reply(self, state: GraphState) -> None:
        if state.reply and state.tool_name is None and state.intent in {"knowledge_answer", "fallback"}:
            return
        if state.intent == "update_session_minutes":
            state.reply = state.reply or f"Your default focus session is now {state.tool_args['minutes']} minutes."
            return
        if state.intent == "update_app_name":
            name = state.tool_result.get("settings", {}).get("app_name", state.tool_args.get("app_name", "Bboo"))
            state.reply = state.reply or f"The application name is now {name}."
            return
        if state.intent == "update_bedtime_target":
            state.reply = state.reply or f"Your bedtime target is now {state.tool_args['bedtime_target']}."
            return
        if state.intent == "update_sleep_target_hours":
            state.reply = state.reply or f"Your sleep target is now {state.tool_args['sleep_target_hours']} hours."
            return
        if state.intent == "start_focus_timer":
            state.reply = state.reply or f"I started a {state.tool_args['minutes']}-minute focus timer for you."
            return
        if state.intent == "stop_focus_timer":
            stopped = state.tool_result.get("stopped_timer", {})
            label = stopped.get("label", "your active timer")
            state.reply = state.reply or f"I stopped {label} for you."
            return
        if state.intent == "get_weekly_summary":
            summary = state.tool_result["summary"]
            state.reply = state.reply or (
                f"{summary['headline']} You completed {summary['completed_sessions_this_week']} sessions this week, "
                f"your check-in streak is {summary['checkin_streak']} day(s), and your weekly goal is {summary['weekly_goal_completion']}% complete."
            )
            return
        if state.intent == "get_dashboard_summary":
            dashboard = state.tool_result["dashboard"]
            state.reply = state.reply or f"Your current focus score is {dashboard['focus_score']} and your brain state is {dashboard['current_state']}. {dashboard['headline']}"
            return
        if state.intent == "get_suggestions":
            suggestions = state.tool_result["suggestions"]
            state.reply = state.reply or (
                f"Your best study time is around {suggestions['best_study_time']}, "
                f"your sleep protection time is {suggestions['sleep_protection_time']}, "
                f"and your risk window is {suggestions['risk_window']}."
            )
            return
        if state.intent == "get_app_usage_summary":
            usage = state.tool_result["usage"]
            if usage["apps"]:
                lead = usage["apps"][0]
                state.reply = state.reply or f"Your most active app in the last 7 days is {lead['app_name']} with {lead['total_hours']} hours."
            else:
                state.reply = state.reply or "You do not have app usage data yet. Add a few entries and I can analyze them for you."
            return
        if state.retrieved_context:
            state.reply = state.reply or f"{state.retrieved_context[0]['content']} If you want, I can also make a direct change for you here."
            state.intent = "knowledge_answer"
            return
        state.reply = state.reply or "I can update settings, start timers, explain summaries, and analyze usage. Try asking me to change your session time or show your weekly summary."
