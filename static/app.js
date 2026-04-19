const translations = {
  en: {
    eyebrow: "Digital wellness platform",
    title: "FocusGuard helps people escape brain rot with smart focus recovery.",
    subtitle:
      "A bilingual application for students, young adults, and parents with intervention tools, habit coaching, attention games, and practical insights.",
    language: "Language",
    audience: "Audience",
    view: "Dashboard",
    permissions: "Device permission",
    refresh: "Refresh dashboard",
    liveOverview: "Live overview",
    scoreLabel: "Focus score",
    habitsTitle: "Habit booster",
    habitsSubtitle: "Small actions that train attention every day.",
    planTitle: "Personalized plan",
    planSubtitle: "Adaptive focus sessions, friction, and recovery rituals.",
    insightsTitle: "Actionable insights",
    insightsSubtitle: "Recommendations backed by behavioral signals.",
    parentTitle: "Guardian guidance",
    parentSubtitle: "Healthy monitoring for younger users.",
    noParent: "Switch to parent mode to see guardian guidance.",
  },
  ar: {
    eyebrow: "منصة عافية رقمية",
    title: "FocusGuard يساعد المستخدمين على مقاومة الـ brain rot باستعادة التركيز بذكاء.",
    subtitle:
      "تطبيق ثنائي اللغة للطلاب والشباب والأهالي مع أدوات تدخل وعادات يومية وألعاب انتباه ورؤى عملية.",
    language: "اللغة",
    audience: "الفئة",
    view: "نوع اللوحة",
    permissions: "صلاحية الجهاز",
    refresh: "تحديث اللوحة",
    liveOverview: "نظرة مباشرة",
    scoreLabel: "درجة التركيز",
    habitsTitle: "معزز العادات",
    habitsSubtitle: "خطوات صغيرة تعيد تدريب الانتباه كل يوم.",
    planTitle: "الخطة الشخصية",
    planSubtitle: "جلسات تركيز وحدود ذكية وطقوس استعادة.",
    insightsTitle: "رؤى عملية",
    insightsSubtitle: "توصيات مبنية على سلوك المستخدم.",
    parentTitle: "إرشاد ولي الأمر",
    parentSubtitle: "متابعة صحية للمستخدمين الأصغر سنا.",
    noParent: "بدل إلى وضع ولي الأمر لرؤية الإرشادات.",
  },
};

const els = {
  language: document.getElementById("language"),
  audience: document.getElementById("audience"),
  mode: document.getElementById("mode"),
  permissions: document.getElementById("permissions"),
  refresh: document.getElementById("refresh"),
  headline: document.getElementById("headline"),
  focusScore: document.getElementById("focusScore"),
  stateBadge: document.getElementById("stateBadge"),
  metrics: document.getElementById("metrics"),
  habits: document.getElementById("habits"),
  plan: document.getElementById("plan"),
  insights: document.getElementById("insights"),
  parentGuidance: document.getElementById("parentGuidance"),
};

function applyI18n(language) {
  document.documentElement.lang = language;
  document.body.dir = language === "ar" ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = translations[language][node.dataset.i18n];
  });
}

function metricCard(metric) {
  return `
    <article class="glass metric-card">
      <small>${metric.label}</small>
      <strong>${metric.value}</strong>
      <p>${metric.hint}</p>
    </article>
  `;
}

function habitCard(habit) {
  return `
    <div class="habit-card">
      <strong>${habit.title}</strong>
      <div class="progress-track"><div class="progress-bar" style="width:${habit.progress}%"></div></div>
      <p>${habit.encouragement}</p>
    </div>
  `;
}

function insightCard(insight) {
  return `
    <div class="insight-card">
      <strong>${insight.title}</strong>
      <p>${insight.detail}</p>
      <p><strong>${insight.action}</strong></p>
    </div>
  `;
}

function planCard(plan) {
  return `
    <div class="plan-card">
      <strong>${plan.title}</strong>
      <p>${plan.focus_theme} · ${plan.recommended_session_minutes} min</p>
      <ul>${plan.steps.map((step) => `<li>${step}</li>`).join("")}</ul>
      <p><strong>${plan.attention_game}</strong></p>
    </div>
  `;
}

function guidanceCard(guidance) {
  return `
    <div class="guidance-card">
      <p>${guidance.summary}</p>
      <ul>${guidance.recommended_actions.map((step) => `<li>${step}</li>`).join("")}</ul>
    </div>
  `;
}

async function loadDashboard() {
  const lang = els.language.value;
  const audience = els.audience.value;
  const mode = els.mode.value;
  const permissions = els.permissions.checked;
  applyI18n(lang);

  const query = new URLSearchParams({
    lang,
    audience,
    mode,
    permissions: String(permissions),
  });

  const [dashboardRes, planRes] = await Promise.all([
    fetch(`/api/dashboard?${query}`),
    fetch(`/api/plan?${new URLSearchParams({ lang, audience, permissions: String(permissions) })}`),
  ]);

  const dashboard = await dashboardRes.json();
  const plan = await planRes.json();

  els.headline.textContent = dashboard.headline;
  els.focusScore.textContent = dashboard.focus_score;
  els.stateBadge.textContent = dashboard.current_state;
  els.metrics.innerHTML = dashboard.metrics.map(metricCard).join("");
  els.habits.innerHTML = dashboard.habits.map(habitCard).join("");
  els.insights.innerHTML = dashboard.insights.map(insightCard).join("");
  els.plan.innerHTML = planCard(plan);

  if (dashboard.parent_guidance) {
    els.parentGuidance.className = "stack";
    els.parentGuidance.innerHTML = guidanceCard(dashboard.parent_guidance);
  } else {
    els.parentGuidance.className = "stack empty-state";
    els.parentGuidance.textContent = translations[lang].noParent;
  }
}

els.refresh.addEventListener("click", loadDashboard);
els.language.addEventListener("change", loadDashboard);
els.audience.addEventListener("change", loadDashboard);
els.mode.addEventListener("change", loadDashboard);
els.permissions.addEventListener("change", loadDashboard);

loadDashboard();
