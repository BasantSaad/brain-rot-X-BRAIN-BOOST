from __future__ import annotations

from dataclasses import dataclass

from shared.schemas import (
    ChartSeries,
    DashboardSnapshot,
    FocusMetric,
    FocusPlan,
    HabitCard,
    InsightCard,
    ParentGuidance,
    ProfileField,
    TrendPoint,
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
        insights = self._insights(profile, language)
        habits = self._habits(profile, language)
        metrics = self._metrics(profile, score, language, mode)
        guidance = self._parent_guidance(language)
        headline = self._brain_banner(profile.account.first_name, score, language)

        return DashboardSnapshot(
            generated_at=utc_now_iso(),
            app_name="Bboo",
            language=language,
            mode=mode,
            headline=headline,
            focus_score=score,
            current_state=self._state_label(score, language),
            profile_summary=self._profile_summary(profile, language),
            metrics=metrics,
            habits=habits,
            insights=insights,
            charts=self._charts(profile, language, mode),
            parent_guidance=guidance if mode == "parent" else None,
        )

    def build_personalized_plan(self, profile: UserProfile, language: str = "en") -> FocusPlan:
        score = self._focus_score(profile)
        duration = 25 if score < 70 else 40
        return FocusPlan(
            generated_at=utc_now_iso(),
            title=self._text(language, en="Bboo focus recovery plan", ar="خطة Bboo لاستعادة التركيز"),
            recommended_session_minutes=duration,
            focus_theme=self._text(language, en="Electric momentum", ar="زخم كهربائي"),
            steps=[
                self._text(
                    language,
                    en=f"Start with {duration}-minute focus blocks right after login and silence distracting apps.",
                    ar=f"ابدأ بجلسات تركيز لمدة {duration} دقيقة بعد تسجيل الدخول مباشرة مع كتم التطبيقات المشتتة.",
                ),
                self._text(
                    language,
                    en="Use one attention game after each session to train recall, switching control, and patience.",
                    ar="استخدم لعبة انتباه واحدة بعد كل جلسة لتدريب التذكر والتحكم في التحول والصبر.",
                ),
                self._text(
                    language,
                    en="Review the graphs each evening and adjust tomorrow's habits from the dashboard.",
                    ar="راجع الرسوم البيانية كل مساء وعدل عادات الغد من داخل اللوحة.",
                ),
            ],
            attention_game=self._text(
                language,
                en="Pattern Pulse: memorize the glowing sequence before the timer ends.",
                ar="Pattern Pulse: احفظ التسلسل المضيء قبل انتهاء المؤقت.",
            ),
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

    def _profile_summary(self, profile: UserProfile, language: str) -> list[ProfileField]:
        return [
            ProfileField(self._text(language, en="Name", ar="الاسم"), f"{profile.account.first_name} {profile.account.last_name}"),
            ProfileField(self._text(language, en="Email", ar="البريد"), profile.account.email),
            ProfileField(self._text(language, en="Country", ar="الدولة"), profile.account.country),
            ProfileField(self._text(language, en="Role", ar="الدور"), profile.account.role.title()),
            ProfileField(self._text(language, en="Age group", ar="الفئة العمرية"), profile.account.age_group.replace("_", " ")),
        ]

    def _metrics(self, profile: UserProfile, score: int, language: str, mode: str) -> list[FocusMetric]:
        metrics = [
            FocusMetric(self._text(language, en="Focus score", ar="درجة التركيز"), str(score), self._state_label(score, language)),
            FocusMetric(self._text(language, en="Notifications", ar="الإشعارات"), str(profile.daily_notifications), self._permission_note(profile, language)),
            FocusMetric(self._text(language, en="Deep sessions", ar="الجلسات العميقة"), str(profile.completed_focus_sessions_last_week), self._text(language, en="Last 7 days", ar="آخر 7 أيام")),
            FocusMetric(self._text(language, en="Screen time", ar="وقت الشاشة"), f"{profile.social_media_hours:.1f}h", self._text(language, en="Daily average", ar="متوسط يومي")),
        ]
        if mode == "parent":
            metrics.append(
                FocusMetric(
                    self._text(language, en="Guardian oversight", ar="إشراف ولي الأمر"),
                    self._text(language, en="Active", ar="نشط"),
                    self._text(language, en="Supportive monitoring enabled", ar="تم تفعيل المتابعة الداعمة"),
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
                    en="Three quiet minutes before social apps reduces random switching.",
                    ar="ثلاث دقائق هادئة قبل التطبيقات الاجتماعية تقلل التنقل العشوائي.",
                ),
            ),
            HabitCard(
                title=self._text(language, en="Focus streak", ar="سلسلة التركيز"),
                progress=min(100, profile.completed_focus_sessions_last_week * 8),
                encouragement=self._text(
                    language,
                    en="Small daily wins repair attention faster than rare intense days.",
                    ar="الانتصارات اليومية الصغيرة تعيد بناء الانتباه أسرع من الأيام الشديدة النادرة.",
                ),
            ),
            HabitCard(
                title=self._text(language, en="Sleep protection", ar="حماية النوم"),
                progress=min(100, int(profile.sleep_hours / 8 * 100)),
                encouragement=self._text(
                    language,
                    en="Protect the last hour before sleep from notifications and doomscrolling.",
                    ar="احم الساعة الأخيرة قبل النوم من الإشعارات والتمرير المرهق.",
                ),
            ),
        ]

    def _insights(self, profile: UserProfile, language: str) -> list[InsightCard]:
        return [
            InsightCard(
                title=self._text(language, en="Highest-risk window", ar="الفترة الأعلى خطرا"),
                detail=self._text(
                    language,
                    en="Bboo predicts the highest distraction pressure between 8 PM and 10 PM after notification spikes.",
                    ar="يتوقع Bboo أعلى ضغط تشتيت بين الثامنة والعاشرة مساء بعد ارتفاع الإشعارات.",
                ),
                action=self._text(
                    language,
                    en="Trigger a focus shield and replace feed time with a 2-minute attention challenge.",
                    ar="فعّل درع التركيز واستبدل وقت المنصات بتحدي انتباه لمدة دقيقتين.",
                ),
            ),
            InsightCard(
                title=self._text(language, en="Planning gap", ar="فجوة التخطيط"),
                detail=self._text(
                    language,
                    en=f"Planning consistency is {profile.planning_consistency}%, which increases unfinished tasks and late-night scrolling.",
                    ar=f"ثبات التخطيط هو {profile.planning_consistency}% وهذا يزيد المهام غير المكتملة والتمرير الليلي.",
                ),
                action=self._text(
                    language,
                    en="Offer one-tap planning templates directly after sign-in.",
                    ar="قدّم قوالب تخطيط بضغطة واحدة مباشرة بعد تسجيل الدخول.",
                ),
            ),
        ]

    def _charts(self, profile: UserProfile, language: str, mode: str) -> list[ChartSeries]:
        focus_points = [
            TrendPoint("Mon", 2.4),
            TrendPoint("Tue", 3.1),
            TrendPoint("Wed", 2.8),
            TrendPoint("Thu", 3.6),
            TrendPoint("Fri", 4.2),
            TrendPoint("Sat", 4.8),
            TrendPoint("Sun", round(max(1.8, profile.completed_focus_sessions_last_week * 0.55), 1)),
        ]
        distraction_points = [
            TrendPoint("Mon", 44),
            TrendPoint("Tue", 51),
            TrendPoint("Wed", 49),
            TrendPoint("Thu", 58),
            TrendPoint("Fri", 64),
            TrendPoint("Sat", 69),
            TrendPoint("Sun", self._focus_score(profile)),
        ]
        charts = [
            ChartSeries(
                title=self._text(language, en="Focus hours in the past 7 days", ar="ساعات التركيز في آخر 7 أيام"),
                subtitle=self._text(language, en="Hours of focused work or study per day", ar="ساعات العمل أو الدراسة المركزة لكل يوم"),
                chart_type="bar",
                points=focus_points,
            ),
            ChartSeries(
                title=self._text(language, en="Weekly focus score", ar="درجة التركيز الأسبوعية"),
                subtitle=self._text(language, en="Daily score trend after login and interventions", ar="اتجاه الدرجة اليومية بعد تسجيل الدخول والتدخلات"),
                chart_type="line",
                points=distraction_points,
            ),
        ]
        if mode == "parent":
            charts.append(
                ChartSeries(
                    title=self._text(language, en="Guardian watch", ar="مراقبة ولي الأمر"),
                    subtitle=self._text(language, en="Risk intensity across the day", ar="شدة الخطر على مدار اليوم"),
                    chart_type="area",
                    points=[
                        TrendPoint("8A", 24),
                        TrendPoint("12P", 41),
                        TrendPoint("4P", 57),
                        TrendPoint("8P", 79),
                        TrendPoint("10P", 72),
                    ],
                )
            )
        return charts

    def _parent_guidance(self, language: str) -> ParentGuidance:
        return ParentGuidance(
            summary=self._text(
                language,
                en="Use coaching, routines, and shared goals instead of punishment. Bboo highlights trends, not surveillance for its own sake.",
                ar="استخدم التوجيه والروتين والأهداف المشتركة بدلا من العقاب. يعرض Bboo الاتجاهات لا المراقبة لمجرد المراقبة.",
            ),
            recommended_actions=[
                self._text(language, en="Approve a study-hours shield schedule from the parent dashboard.", ar="اعتمد جدولا لدرع الدراسة من لوحة ولي الأمر."),
                self._text(language, en="Review weekly graph changes with the child using supportive language.", ar="راجع تغيرات الرسوم الأسبوعية مع الطفل بلغة داعمة."),
                self._text(language, en="Escalate only when overload patterns remain high for several days.", ar="قم بالتصعيد فقط عندما تبقى مؤشرات الضغط مرتفعة عدة أيام."),
            ],
        )

    def _state_label(self, score: int, language: str) -> str:
        if score >= 80:
            return self._text(language, en="Focused", ar="مركز")
        if score >= 60:
            return self._text(language, en="Recovering", ar="يتحسن")
        return self._text(language, en="Overloaded", ar="مرهق رقميا")

    def _brain_banner(self, first_name: str, score: int, language: str) -> str:
        if score >= 60:
            return self._text(
                language,
                en=f"{first_name}, your brain is currently Boost.",
                ar=f"{first_name}، دماغك الآن في حالة Boost.",
            )
        return self._text(
            language,
            en=f"{first_name}, your brain is currently Rot.",
            ar=f"{first_name}، دماغك الآن في حالة Rot.",
        )

    def _permission_note(self, profile: UserProfile, language: str) -> str:
        if profile.permissions_granted:
            return self._text(language, en="Live device signals", ar="بيانات مباشرة من الجهاز")
        return self._text(language, en="Estimated from profile input", ar="تقدير من بيانات الملف الشخصي")

    def _text(self, language: str, en: str, ar: str) -> str:
        return ar if language == "ar" else en
