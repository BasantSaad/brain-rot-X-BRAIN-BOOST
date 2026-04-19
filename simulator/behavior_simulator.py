from __future__ import annotations

from dataclasses import dataclass
from random import Random

from shared.schemas import AccountProfile, UserProfile


@dataclass(slots=True)
class BehaviorSimulationConfig:
    seed: int = 21


class BehaviorSimulator:
    def __init__(self, config: BehaviorSimulationConfig) -> None:
        self.random = Random(config.seed)

    def build_profile(
        self,
        audience: str,
        permissions_granted: bool,
        first_name: str = "",
        last_name: str = "",
        email: str = "",
        country: str = "Egypt",
        preferred_language: str = "en",
        role: str = "user",
    ) -> UserProfile:
        presets = {
            "student": dict(name="Lina", surname="Hassan", age_group="teen", notifications=86, social=4.4, sleep=6.3, planning=58, sessions=7),
            "young-adult": dict(name="Adam", surname="Nour", age_group="young_adult", notifications=73, social=3.7, sleep=6.9, planning=63, sessions=8),
            "child": dict(name="Youssef", surname="Samir", age_group="child", notifications=48, social=2.2, sleep=8.1, planning=52, sessions=6),
        }
        preset = presets.get(audience, presets["student"])
        notification_adjustment = self.random.randint(-6, 6)
        social_adjustment = round(self.random.uniform(-0.4, 0.4), 1)
        planning_adjustment = self.random.randint(-4, 4)
        if not permissions_granted:
            notification_adjustment += 8
            social_adjustment += 0.3

        account = AccountProfile(
            first_name=first_name or preset["name"],
            last_name=last_name or preset["surname"],
            email=email or f"{(first_name or preset['name']).lower()}@bboo.app",
            country=country,
            preferred_language=preferred_language,
            role=role,
            age_group=preset["age_group"],
        )

        return UserProfile(
            account=account,
            permissions_granted=permissions_granted,
            daily_notifications=max(18, preset["notifications"] + notification_adjustment),
            social_media_hours=max(0.6, round(preset["social"] + social_adjustment, 1)),
            sleep_hours=max(4.5, round(preset["sleep"] + self.random.uniform(-0.3, 0.3), 1)),
            planning_consistency=max(25, min(95, preset["planning"] + planning_adjustment)),
            completed_focus_sessions_last_week=max(2, preset["sessions"] + self.random.randint(-2, 2)),
        )
