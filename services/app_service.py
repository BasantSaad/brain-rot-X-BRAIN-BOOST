from __future__ import annotations

from dataclasses import replace
from smtplib import SMTPException
from typing import Any

from agent.focus_engine import FocusCoachConfig, FocusCoachEngine
from services.email_service import EmailService
from shared.schemas import FocusPlan
from simulator.behavior_simulator import BehaviorSimulationConfig, BehaviorSimulator


class BbooAppService:
    def __init__(self, repository, email_service: EmailService | None = None) -> None:
        self.repository = repository
        self.email_service = email_service or EmailService()
        self.engine = FocusCoachEngine(FocusCoachConfig())
        self.simulator = BehaviorSimulator(BehaviorSimulationConfig())

    def build_profile(self, *, query_params: dict[str, Any] | None = None, user_id: int | None = None):
        params = query_params or {}
        lang = params.get("lang", "en")
        permissions = str(params.get("permissions", "true")).lower() == "true"
        audience = params.get("audience", "student")
        if user_id is not None:
            stored_profile = self.repository.load_profile_by_user_id(user_id)
            if stored_profile is not None:
                return self._profile_with_live_signals(user_id=user_id, profile=stored_profile)
        email = params.get("email", "")
        if email:
            stored_profile = self.repository.load_profile(email)
            if stored_profile is not None:
                return stored_profile
        return self.simulator.build_profile(
            audience=audience,
            permissions_granted=permissions,
            first_name=params.get("first_name", ""),
            last_name=params.get("last_name", ""),
            email=email,
            country=params.get("country", "Egypt"),
            preferred_language=lang,
            role=params.get("mode", "user"),
        )

    def dashboard_payload(self, *, session: dict[str, Any], lang: str, mode: str) -> dict[str, Any]:
        profile = self.build_profile(user_id=session["user_id"])
        settings = self.repository.load_settings(session["user_id"])
        dashboard = self.engine.build_dashboard(profile=profile, language=lang, mode=mode)
        dashboard.app_name = settings["app_name"]
        self.repository.record_dashboard_snapshot(session["user_id"], dashboard)
        return dashboard.to_dict()

    def plan_payload(self, *, session: dict[str, Any], lang: str) -> dict[str, Any]:
        profile = self.build_profile(user_id=session["user_id"])
        settings = self.repository.load_settings(session["user_id"])
        plan = self.repository.load_focus_plan(session["user_id"])
        if plan is None:
            plan = self.engine.build_personalized_plan(profile=profile, language=lang)
            plan.title = f"{settings['app_name']} focus recovery plan"
            plan.recommended_session_minutes = int(settings["default_session_minutes"])
            plan = self.repository.save_focus_plan(session["user_id"], plan)
        return plan.to_dict()

    def update_settings_field(self, user_id: int, field: str, value: Any) -> dict[str, Any]:
        settings = self.repository.load_settings(user_id)
        settings[field] = value
        return self.repository.update_settings(user_id, settings)

    def save_focus_plan(self, user_id: int, payload: dict[str, Any]) -> FocusPlan:
        plan = FocusPlan(
            generated_at=payload.get("generated_at") or "",
            title=str(payload["title"]).strip(),
            recommended_session_minutes=int(payload["recommended_session_minutes"]),
            focus_theme=str(payload["focus_theme"]).strip(),
            steps=[str(step).strip() for step in payload.get("steps", []) if str(step).strip()],
            attention_game=str(payload["attention_game"]).strip(),
        )
        return self.repository.save_focus_plan(user_id, plan)

    def save_app_usage_with_reminders(
        self,
        *,
        session: dict[str, Any],
        app_name: str,
        usage_date: str,
        usage_hours: float,
    ) -> dict[str, Any]:
        self.repository.save_app_usage(session["user_id"], app_name, usage_date, usage_hours)
        total_minutes = int(round(usage_hours * 60))
        due_thresholds = self.repository.due_app_usage_reminder_thresholds(
            session["user_id"],
            app_name,
            usage_date,
            total_minutes,
        )
        sent_thresholds: list[int] = []
        skipped_thresholds: list[int] = []
        failed_thresholds: list[int] = []
        for threshold in due_thresholds:
            try:
                sent = self.email_service.send_screen_time_reminder(
                    to_email=session["email"],
                    first_name=session.get("first_name", ""),
                    app_name=app_name,
                    usage_date=usage_date,
                    threshold_minutes=threshold,
                    total_minutes=total_minutes,
                )
            except (OSError, SMTPException):
                failed_thresholds.append(threshold)
                continue
            if sent:
                self.repository.record_app_usage_reminder(session["user_id"], app_name, usage_date, threshold)
                sent_thresholds.append(threshold)
            else:
                skipped_thresholds.append(threshold)
        return {
            "sent_thresholds": sent_thresholds,
            "skipped_thresholds": skipped_thresholds,
            "failed_thresholds": failed_thresholds,
            "email_configured": self.email_service.is_configured(),
        }

    def _profile_with_live_signals(self, *, user_id: int, profile):
        signals = self.repository.live_behavior_signals(user_id)
        reactive_social_hours = max(
            float(profile.social_media_hours),
            float(signals["today_usage_hours"]),
            float(signals["average_daily_usage_hours"]),
        )
        reactive_focus_sessions = max(
            int(profile.completed_focus_sessions_last_week),
            int(signals["completed_focus_sessions_last_week"]),
        )
        return replace(
            profile,
            social_media_hours=reactive_social_hours,
            completed_focus_sessions_last_week=reactive_focus_sessions,
        )
