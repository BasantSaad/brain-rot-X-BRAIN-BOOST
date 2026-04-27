from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class AccountProfile:
    first_name: str
    last_name: str
    email: str
    country: str
    preferred_language: str
    role: str
    age_group: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class UserProfile:
    account: AccountProfile
    permissions_granted: bool
    daily_notifications: int
    social_media_hours: float
    sleep_hours: float
    planning_consistency: int
    completed_focus_sessions_last_week: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AppSettings:
    app_name: str
    study_start_time: str
    study_end_time: str
    sleep_target_hours: float
    focus_session_minutes: int
    short_break_minutes: int
    long_break_minutes: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ExtendedProfile:
    age: int | None
    schedule_type: str
    goals: list[str]
    distraction_triggers: list[str]
    sleep_target_hours: float
    mood_baseline: str
    energy_baseline: str

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
class ProfileField:
    label: str
    value: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TrendPoint:
    label: str
    value: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ChartSeries:
    title: str
    subtitle: str
    chart_type: str
    points: list[TrendPoint]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PlanHistoryItem:
    saved_at: str
    recommended_session_minutes: int
    focus_theme: str
    steps: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class WeeklySummary:
    headline: str
    improvement_percent: int
    streak_days: int
    completed_sessions: int
    average_focus_minutes: int
    recommendation: str

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
    profile_summary: list[ProfileField] = field(default_factory=list)
    metrics: list[FocusMetric] = field(default_factory=list)
    habits: list[HabitCard] = field(default_factory=list)
    insights: list[InsightCard] = field(default_factory=list)
    charts: list[ChartSeries] = field(default_factory=list)
    parent_guidance: ParentGuidance | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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
