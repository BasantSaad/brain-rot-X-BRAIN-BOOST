from __future__ import annotations

import re
from dataclasses import dataclass, field
import os
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from agent.ollama_client import OllamaPlannerClient
from agent.rag_store import FaissRagStore
from agent.tools import BbooToolRegistry


class AgentGraphState(TypedDict):
    user_message: str
    session: dict[str, Any]
    settings: dict[str, Any]
    intent: str
    tool_name: str | None
    tool_args: dict[str, Any]
    retrieved_context: list[dict[str, Any]]
    tool_result: dict[str, Any]
    reply: str


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


class BbooLangGraphAgent:
    """Assistant runtime implemented as a real LangGraph StateGraph."""

    def __init__(self, service) -> None:
        self.service = service
        self.rag_store = FaissRagStore()
        self.tools = BbooToolRegistry(service)
        self.provider = os.getenv("BBOO_LLM_PROVIDER", "local").strip().lower()
        self.ollama = OllamaPlannerClient()
        self.graph = self._build_graph()

    def run(self, *, message: str, session: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
        state = self.graph.invoke(
            {
                "user_message": message.strip(),
                "session": session,
                "settings": settings,
                "intent": "fallback",
                "tool_name": None,
                "tool_args": {},
                "retrieved_context": [],
                "tool_result": {},
                "reply": "",
            }
        )
        return {
            "reply": state["reply"],
            "intent": state["intent"],
            "tool_name": state["tool_name"],
            "tool_status": "success" if state["tool_name"] else "none",
            "action_payload": state["tool_result"],
            "retrieved_notes": state["retrieved_context"],
        }

    def _build_graph(self):
        workflow = StateGraph(AgentGraphState)
        workflow.add_node("retrieve_context", self._retrieve_context_node)
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("execute_tool", self._execute_tool_node)
        workflow.add_node("compose_reply", self._compose_reply_node)

        workflow.add_edge(START, "retrieve_context")
        workflow.add_edge("retrieve_context", "plan")
        workflow.add_edge("plan", "execute_tool")
        workflow.add_edge("execute_tool", "compose_reply")
        workflow.add_edge("compose_reply", END)

        return workflow.compile()

    def _retrieve_context_node(self, state: AgentGraphState) -> dict[str, Any]:
        return {"retrieved_context": self.rag_store.query(state["user_message"], limit=2)}

    def _plan_node(self, state: AgentGraphState) -> dict[str, Any]:
        runtime_state = self._runtime_state(state)
        self._plan(runtime_state)
        return self._state_update(runtime_state)

    def _execute_tool_node(self, state: AgentGraphState) -> dict[str, Any]:
        runtime_state = self._runtime_state(state)
        self._execute_tool(runtime_state)
        return self._state_update(runtime_state)

    def _compose_reply_node(self, state: AgentGraphState) -> dict[str, Any]:
        runtime_state = self._runtime_state(state)
        self._compose_reply(runtime_state)
        return self._state_update(runtime_state)

    def _runtime_state(self, state: AgentGraphState) -> GraphState:
        return GraphState(
            user_message=state["user_message"],
            session=state["session"],
            settings=state["settings"],
            intent=state["intent"],
            tool_name=state["tool_name"],
            tool_args=dict(state["tool_args"]),
            retrieved_context=list(state["retrieved_context"]),
            tool_result=dict(state["tool_result"]),
            reply=state["reply"],
        )

    def _state_update(self, state: GraphState) -> dict[str, Any]:
        return {
            "intent": state.intent,
            "tool_name": state.tool_name,
            "tool_args": state.tool_args,
            "retrieved_context": state.retrieved_context,
            "tool_result": state.tool_result,
            "reply": state.reply,
        }

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
    #--------------------------------------------------------------------------------------------------------------------
    # Here we can customize the assistant's reply based on the intent and tool results, to make it more informative and personalized for the user.
    #---------------------------------------------------------------------------------------------------------------------
        if state.intent == "update_session_minutes":
            state.tool_result.get("settings", {}).get("session_minutes")
            state.reply = state.reply or f"Your default focus session is now {state.tool_args['minutes']} minutes."
            return
        #🚩🚩🚩🚩 need to removed
        if state.intent == "update_app_name":
            name = state.tool_result.get("settings", {}).get("app_name", state.tool_args.get("app_name", "Bboo"))
            state.reply = state.reply or f"The application name is now {name}."
            return
        #-----------------------------
        if state.intent == "update_bedtime_target":
            bedtime = (
                state.tool_result.get("settings", {}).get("bedtime_target")
                or state.tool_args.get("bedtime_target", "updated")
            )
            state.reply = state.reply or f"Your bedtime target is now {bedtime}."
            return
        if state.intent == "update_sleep_target_hours":
            hours = (
                state.tool_result.get("settings", {}).get("sleep_target_hours")
                or state.tool_args.get("sleep_target_hours", "updated")
            )
            state.reply = state.reply or f"Your sleep target is now {hours} hours."
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


# Backward-compatible alias for older imports and diagrams.
LocalLangGraphAgent = BbooLangGraphAgent
