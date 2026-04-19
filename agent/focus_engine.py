from __future__ import annotations

from dataclasses import dataclass

from shared.schemas import (
    DashboardSnapshot,
    FocusMetric,
    FocusPlan,
    HabitCard,
    InsightCard,
    ParentGuidance,
    UserProfile,
    utc_now_iso,
)


@dataclass(slots=True)
class FocusCoachConfig:
    notification_risk_weight: float = 0.35
    social_risk_weight: float = 0.30
    sleep_risk_weight: float = 0.15
    planning_risk_weight: float = 0.20


class FocusCoachEngine:
    def __init__(self, config: FocusCoachConfig) -> None:
        self.config = config

    def build_dashboard(
        self,
        profile: UserProfile,
        language: str = "en",
        mode: str = "user",
    ) -> DashboardSnapshot:
        score = self._focus_score(profile)
        streak = max(2, int(profile.completed_focus_sessions_last_week / 2))
        insights = self._insights(profile, language)
        habits = self._habits(profile, language)
        metrics = self._metrics(profile, score, language, mode)
        guidance = self._parent_guidance(profile, language)
        headline = self._text(
            language,
            en=f"{profile.first_name}'s focus is improving with structured friction.",
            ar=f"تركيز {profile.first_name} يتحسن عند إضافة حدود ذكية ومهام قصيرة.",
        )

        return DashboardSnapshot(
            generated_at=utc_now_iso(),
            app_name="FocusGuard",
            language=language,
            mode=mode,
            headline=headline,
            focus_score=score,
            current_state=self._state_label(score, language),
            metrics=metrics,
            habits=habits,
            insights=insights,
            parent_guidance=guidance if mode == "parent" else None,
        )

    def build_personalized_plan(self, profile: UserProfile, language: str = "en") -> FocusPlan:
        score = self._focus_score(profile)
        duration = 25 if score < 70 else 40
        plan_title = self._text(
            language,
            en="Personal focus recovery plan",
            ar="خطة شخصية لاستعادة التركيز",
        )
        steps = [
            self._text(
                language,
                en=f"Start with {duration}-minute deep-focus blocks and auto-silence distracting apps.",
                ar=f"ابدأ بجلسات تركيز عميق لمدة {duration} دقيقة مع كتم التطبيقات المشتتة تلقائيا.",
            ),
            self._text(
                language,
                en="Replace scrolling with one micro-habit: breathing, journaling, or memory cards.",
                ar="استبدل التمرير بعادة صغيرة واحدة: تنفس أو كتابة سريعة أو بطاقات ذاكرة.",
            ),
            self._text(
                language,
                en="Review the evening dashboard and celebrate streak progress, not just raw study hours.",
                ar="راجع لوحة المساء واحتفل بتقدم السلسلة وليس فقط بعدد ساعات الدراسة.",
            ),
        ]
        game = self._text(
            language,
            en="Attention game: remember the pattern and repeat it under a 20-second timer.",
            ar="لعبة الانتباه: تذكر النمط ثم أعده خلال عشرين ثانية.",
        )
        return FocusPlan(
            generated_at=utc_now_iso(),
            title=plan_title,
            recommended_session_minutes=duration,
            focus_theme=self._text(language, en="Calm momentum", ar="زخم هادئ"),
            steps=steps,
            attention_game=game,
        )

    def _focus_score(self, profile: UserProfile) -> int:
        notification_risk = min(profile.daily_notifications / 120.0, 1.0)
        social_risk = min(profile.social_media_hours / 7.0, 1.0)
        sleep_risk = 1.0 - min(profile.sleep_hours / 8.0, 1.0)
        planning_risk = 1.0 - min(profile.planning_consistency / 100.0, 1.0)
        risk = (
            notification_risk * self.config.notification_risk_weight
            + social_risk * self.config.social_risk_weight
            + sleep_risk * self.config.sleep_risk_weight
            + planning_risk * self.config.planning_risk_weight
        )
        recovery_bonus = min(profile.completed_focus_sessions_last_week / 14.0, 1.0) * 18
        return max(28, min(96, int(round((1.0 - risk) * 100 + recovery_bonus))))

    def _metrics(
        self,
        profile: UserProfile,
        score: int,
        language: str,
        mode: str,
    ) -> list[FocusMetric]:
        labels = {
            "score": self._text(language, en="Focus score", ar="درجة التركيز"),
            "notifications": self._text(language, en="Notifications", ar="الإشعارات"),
            "sessions": self._text(language, en="Deep sessions", ar="جلسات عميقة"),
            "screen": self._text(language, en="Screen time", ar="وقت الشاشة"),
        }
        metrics = [
            FocusMetric(labels["score"], str(score), self._state_label(score, language)),
            FocusMetric(labels["notifications"], str(profile.daily_notifications), self._permission_note(profile, language)),
            FocusMetric(labels["sessions"], str(profile.completed_focus_sessions_last_week), self._text(language, en="Last 7 days", ar="آخر 7 أيام")),
            FocusMetric(labels["screen"], f"{profile.social_media_hours:.1f}h", self._text(language, en="Daily average", ar="متوسط يومي")),
        ]
        if mode == "parent":
            metrics.append(
                FocusMetric(
                    self._text(language, en="Guardian mode", ar="وضع ولي الأمر"),
                    self._text(language, en="Enabled", ar="مفعل"),
                    self._text(language, en="Age-aware monitoring", ar="متابعة تراعي العمر"),
                )
            )
        return metrics

    def _habits(self, profile: UserProfile, language: str) -> list[HabitCard]:
        return [
            HabitCard(
                title=self._text(language, en="Morning planning", ar="تخطيط الصباح"),
                progress=min(100, profile.planning_consistency + 8),
                encouragement=self._text(
                    language,
                    en="A 3-minute plan lowers random app switching.",
                    ar="خطة لمدة 3 دقائق تقلل التنقل العشوائي بين التطبيقات.",
                ),
            ),
            HabitCard(
                title=self._text(language, en="Focus streak", ar="سلسلة التركيز"),
                progress=min(100, profile.completed_focus_sessions_last_week * 8),
                encouragement=self._text(
                    language,
                    en="Consistency beats intensity for attention repair.",
                    ar="الاستمرارية أفضل من الشدة لاستعادة الانتباه.",
                ),
            ),
            HabitCard(
                title=self._text(language, en="Sleep protection", ar="حماية النوم"),
                progress=min(100, int(profile.sleep_hours / 8 * 100)),
                encouragement=self._text(
                    language,
                    en="Sleep recovery improves memory and academic performance.",
                    ar="تحسين النوم يرفع الذاكرة والأداء الدراسي.",
                ),
            ),
        ]

    def _insights(self, profile: UserProfile, language: str) -> list[InsightCard]:
        return [
            InsightCard(
                title=self._text(language, en="Peak distraction window", ar="فترة التشتت الأعلى"),
                detail=self._text(
                    language,
                    en="Most interruptions happen between 8 PM and 10 PM after notification spikes.",
                    ar="أغلب المقاطعات تحدث بين الثامنة والعاشرة مساء بعد ارتفاع الإشعارات.",
                ),
                action=self._text(
                    language,
                    en="Schedule auto-focus mode and light gamified tasks during that period.",
                    ar="جدول وضع التركيز التلقائي ومهام لعب خفيفة خلال هذه الفترة.",
                ),
            ),
            InsightCard(
                title=self._text(language, en="Planning gap", ar="فجوة التخطيط"),
                detail=self._text(
                    language,
                    en=f"Planning consistency is {profile.planning_consistency}%, which predicts unfinished tasks.",
                    ar=f"ثبات التخطيط هو {profile.planning_consistency}% وهذا يتنبأ بزيادة المهام غير المكتملة.",
                ),
                action=self._text(
                    language,
                    en="Offer one-tap daily planning templates.",
                    ar="قدم قوالب تخطيط يومي بضغطة واحدة.",
                ),
            ),
        ]

    def _parent_guidance(self, profile: UserProfile, language: str) -> ParentGuidance:
        return ParentGuidance(
            summary=self._text(
                language,
                en="Use supportive coaching instead of punishment. Focus on routines, sleep, and app boundaries.",
                ar="استخدم التوجيه الداعم بدلا من العقاب وركز على الروتين والنوم وحدود التطبيقات.",
            ),
            recommended_actions=[
                self._text(language, en="Approve a distraction shield schedule for study hours.", ar="اعتمد جدولا لدرع التشتت أثناء ساعات الدراسة."),
                self._text(language, en="Review weekly progress with the child using positive language.", ar="راجع التقدم الأسبوعي مع الطفل بلغة إيجابية."),
                self._text(language, en="Escalate alerts only when sustained overload lasts for several days.", ar="ارفع التنبيه فقط عند استمرار الضغط الرقمي لعدة أيام."),
            ],
        )

    def _state_label(self, score: int, language: str) -> str:
        if score >= 80:
            return self._text(language, en="Focused", ar="مركز")
        if score >= 60:
            return self._text(language, en="Recovering", ar="يتحسن")
        return self._text(language, en="Overloaded", ar="مرهق رقميا")

    def _permission_note(self, profile: UserProfile, language: str) -> str:
        if profile.permissions_granted:
            return self._text(language, en="Live device signals", ar="بيانات مباشرة من الجهاز")
        return self._text(language, en="Estimated from manual input", ar="تقدير من إدخال المستخدم")

    def _text(self, language: str, en: str, ar: str) -> str:
        return ar if language == "ar" else en
