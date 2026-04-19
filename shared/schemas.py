from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class UserProfile:
    first_name: str
    age_group: str
    permissions_granted: bool
    daily_notifications: int
    social_media_hours: float
    sleep_hours: float
    planning_consistency: int
    completed_focus_sessions_last_week: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FocusMetric:
    label: str
    value: str
    hint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class HabitCard:
    title: str
    progress: int
    encouragement: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class InsightCard:
    title: str
    detail: str
    action: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ParentGuidance:
    summary: str
    recommended_actions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DashboardSnapshot:
    generated_at: str
    app_name: str
    language: str
    mode: str
    headline: str
    focus_score: int
    current_state: str
    metrics: list[FocusMetric] = field(default_factory=list)
    habits: list[HabitCard] = field(default_factory=list)
    insights: list[InsightCard] = field(default_factory=list)
    parent_guidance: ParentGuidance | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return data


@dataclass(slots=True)
class FocusPlan:
    generated_at: str
    title: str
    recommended_session_minutes: int
    focus_theme: str
    steps: list[str]
    attention_game: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
