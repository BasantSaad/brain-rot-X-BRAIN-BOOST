from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib import error, request


@dataclass(slots=True)
class OllamaConfig:
    base_url: str = os.getenv("BBOO_OLLAMA_URL", "http://127.0.0.1:11434")
    model: str = os.getenv("BBOO_OLLAMA_MODEL", "qwen2.5:7b-instruct")
    timeout_seconds: int = int(os.getenv("BBOO_OLLAMA_TIMEOUT_SECONDS", "45"))


class OllamaPlannerClient:
    def __init__(self, config: OllamaConfig | None = None) -> None:
        self.config = config or OllamaConfig()

    def plan(self, *, message: str, session: dict[str, Any], settings: dict[str, Any], retrieved_context: list[dict[str, Any]], available_tools: list[dict[str, str]]) -> dict[str, Any]:
        tool_catalog = "\n".join(f"- {tool['name']}: {tool['description']}" for tool in available_tools)
        context_text = "\n".join(
            f"- {item['title']}: {item['content']}" for item in retrieved_context
        ) or "- No retrieved context."
        prompt = f"""
You are the planning model inside the Bboo agent system.

User profile context:
- first_name: {session.get('first_name', '')}
- language: {session.get('lang', 'en')}
- mode: {session.get('mode', 'user')}
- app_name: {settings.get('app_name', 'Bboo')}
- study_start: {settings.get('study_start', '16:00')}
- bedtime_target: {settings.get('bedtime_target', '22:30')}
- sleep_target_hours: {settings.get('sleep_target_hours', 8)}
- default_session_minutes: {settings.get('default_session_minutes', 30)}

Retrieved context:
{context_text}

Available tools:
{tool_catalog}

Your job:
1. Understand the user's intent.
2. If a safe tool should be used, choose exactly one tool from the list and provide tool arguments.
3. If no tool is needed, leave tool_name empty.
4. Always answer in valid JSON only.

Return JSON with exactly these keys:
{{
  "intent": "short_intent_name",
  "tool_name": "tool name or empty string",
  "tool_args": {{}},
  "reply": "short helpful reply for the user"
}}

User message:
{message}
""".strip()

        payload = {
            "model": self.config.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": "Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
        }
        endpoint = f"{self.config.base_url.rstrip('/')}/api/chat"
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Ollama planner request failed: {exc}") from exc

        content = ((body.get("message") or {}).get("content") or "").strip()
        if not content:
            raise RuntimeError("Ollama returned an empty planner response.")
        try:
            planned = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Ollama returned invalid JSON: {content}") from exc

        return {
            "intent": str(planned.get("intent", "fallback")).strip() or "fallback",
            "tool_name": str(planned.get("tool_name", "")).strip() or None,
            "tool_args": planned.get("tool_args") or {},
            "reply": str(planned.get("reply", "")).strip(),
        }
