const dashboardTranslations = {
  en: {
    dashboardEyebrow: "Bboo dashboard",
    switchAccount: "Switch account",
    brainState: "Brain state",
    scoreLabel: "Focus score",
    habitsTitle: "Habit booster",
    habitsSubtitle: "Small actions that train attention every day.",
    planTitle: "Personalized plan",
    planSubtitle: "Edit the plan yourself and shape it around your real routine.",
    insightsTitle: "Actionable insights",
    insightsSubtitle: "Recommendations backed by behavioral signals.",
    parentTitle: "Guardian guidance",
    parentSubtitle: "Healthy monitoring for younger users.",
    donutLabel: "Apps today",
    themeLabel: "Theme",
    minutesLabel: "Session minutes",
    stepsLabel: "Steps",
    savePlan: "Save my edits",
  },
  ar: {
    dashboardEyebrow: "لوحة Bboo",
    switchAccount: "تبديل الحساب",
    brainState: "حالة الدماغ",
    scoreLabel: "درجة التركيز",
    habitsTitle: "معزز العادات",
    habitsSubtitle: "خطوات صغيرة تدرب الانتباه كل يوم.",
    planTitle: "الخطة الشخصية",
    planSubtitle: "يمكنك تعديل الخطة بنفسك لتناسب روتينك الحقيقي.",
    insightsTitle: "رؤى عملية",
    insightsSubtitle: "توصيات مبنية على الإشارات السلوكية.",
    parentTitle: "إرشاد ولي الأمر",
    parentSubtitle: "متابعة صحية للمستخدمين الأصغر سنا.",
    donutLabel: "تطبيقات اليوم",
    themeLabel: "الثيمة",
    minutesLabel: "دقائق الجلسة",
    stepsLabel: "الخطوات",
    savePlan: "احفظ تعديلاتي",
  },
};

const sessionKey = "bboo-session";
const planEditKey = "bboo-plan-edits";
const session = JSON.parse(localStorage.getItem(sessionKey) || "null");

if (!session) {
  window.location.href = "/";
}

const dashEls = {
  topbarName: document.getElementById("topbarName"),
  headline: document.getElementById("headline"),
  focusScore: document.getElementById("focusScore"),
  stateBadge: document.getElementById("stateBadge"),
  metrics: document.getElementById("metrics"),
  charts: document.getElementById("charts"),
  habits: document.getElementById("habits"),
  plan: document.getElementById("plan"),
  insights: document.getElementById("insights"),
  parentGuidance: document.getElementById("parentGuidance"),
  guardianSection: document.getElementById("guardianSection"),
  backToAuth: document.getElementById("backToAuth"),
};

function t(key) {
  return dashboardTranslations[session.lang || "en"][key];
}

function applyDashboardI18n(language) {
  document.documentElement.lang = language;
  document.body.dir = language === "ar" ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = dashboardTranslations[language][node.dataset.i18n];
  });
}

function queryFromSession() {
  return new URLSearchParams(session);
}

function metricCard(metric) {
  return `<article class="glass metric-card"><small>${metric.label}</small><strong>${metric.value}</strong><p>${metric.hint}</p></article>`;
}

function habitCard(habit) {
  return `<div class="habit-card"><strong>${habit.title}</strong><div class="progress-track"><div class="progress-bar" style="width:${habit.progress}%"></div></div><p>${habit.encouragement}</p></div>`;
}

function insightCard(insight) {
  return `<div class="insight-card"><strong>${insight.title}</strong><p>${insight.detail}</p><p><strong>${insight.action}</strong></p></div>`;
}

function planCard(plan) {
  const savedPlan = JSON.parse(localStorage.getItem(planEditKey) || "null");
  const sessionMinutes = savedPlan?.minutes || plan.recommended_session_minutes;
  const focusTheme = savedPlan?.theme || plan.focus_theme;
  const steps = savedPlan?.steps || plan.steps;
  return `
    <div class="plan-card editable-plan">
      <strong>${plan.title}</strong>
      <label class="edit-field">
        <span>${t("themeLabel")}</span>
        <input id="planThemeInput" value="${focusTheme}">
      </label>
      <label class="edit-field">
        <span>${t("minutesLabel")}</span>
        <input id="planMinutesInput" type="number" min="10" max="120" value="${sessionMinutes}">
      </label>
      <label class="edit-field">
        <span>${t("stepsLabel")}</span>
        <textarea id="planStepsInput" rows="7">${steps.join("\n")}</textarea>
      </label>
      <p><strong>${plan.attention_game}</strong></p>
      <button id="savePlanEdits" class="ghost-btn save-plan-btn" type="button">${t("savePlan")}</button>
    </div>
  `;
}

function guidanceCard(guidance) {
  return `<div class="guidance-card"><p>${guidance.summary}</p><ul>${guidance.recommended_actions.map((step) => `<li>${step}</li>`).join("")}</ul></div>`;
}

function renderBars(points) {
  const max = Math.max(...points.map((point) => point.value), 6);
  return `
    <div class="chart-shell">
      <svg class="chart-svg" viewBox="0 0 560 190" preserveAspectRatio="none">
        ${points.map((point, index) => {
          const barWidth = 54;
          const gap = 20;
          const x = 20 + index * (barWidth + gap);
          const barHeight = (point.value / max) * 132;
          const y = 162 - barHeight;
          return `<g><rect x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" rx="18" fill="var(--accent)"></rect><text x="${x + barWidth / 2}" y="${y - 8}" text-anchor="middle" fill="var(--accent-bright)" font-size="12">${point.value}h</text></g>`;
        }).join("")}
      </svg>
      <div class="chart-labels">${points.map((point) => `<span>${point.label}</span>`).join("")}</div>
    </div>
  `;
}

function renderDonut(points) {
  const total = points.reduce((sum, point) => sum + point.value, 0) || 1;
  const colors = ["var(--accent)", "var(--secondary)", "var(--accent-soft)", "var(--secondary-soft)", "var(--accent-bright)"];
  let current = 0;
  const segments = points.map((point, index) => {
    const start = current / total * 360;
    current += point.value;
    const end = current / total * 360;
    return `${colors[index % colors.length]} ${start}deg ${end}deg`;
  }).join(", ");
  return `
    <div class="donut-layout">
      <div class="donut-chart" style="background:conic-gradient(${segments})">
        <div class="donut-hole">
          <strong>${total.toFixed(1)}h</strong>
          <span>${t("donutLabel")}</span>
        </div>
      </div>
      <div class="donut-legend">
        ${points.map((point, index) => `
          <div class="legend-row">
            <span class="legend-dot" style="background:${colors[index % colors.length]}"></span>
            <span>${point.label}</span>
            <strong>${point.value}h</strong>
          </div>
        `).join("")}
      </div>
    </div>
  `;
}

function chartCard(chart) {
  const visual = chart.chart_type === "bar" ? renderBars(chart.points) : renderDonut(chart.points);
  return `<article class="glass chart-card"><h3>${chart.title}</h3><p>${chart.subtitle}</p>${visual}</article>`;
}

function attachPlanEditor(plan) {
  const saveButton = document.getElementById("savePlanEdits");
  if (!saveButton) {
    return;
  }
  saveButton.addEventListener("click", () => {
    const steps = document.getElementById("planStepsInput").value
      .split("\n")
      .map((step) => step.trim())
      .filter(Boolean);
    localStorage.setItem(planEditKey, JSON.stringify({
      theme: document.getElementById("planThemeInput").value.trim() || plan.focus_theme,
      minutes: Number(document.getElementById("planMinutesInput").value) || plan.recommended_session_minutes,
      steps,
    }));
  });
}

async function loadDashboard() {
  applyDashboardI18n(session.lang || "en");
  document.body.dataset.mode = session.mode || "user";
  const query = queryFromSession();
  const [dashboardRes, planRes] = await Promise.all([
    fetch(`/api/dashboard?${query}`),
    fetch(`/api/plan?${query}`),
  ]);

  const dashboard = await dashboardRes.json();
  const plan = await planRes.json();

  dashEls.topbarName.textContent = session.first_name || "Bboo";
  dashEls.headline.textContent = dashboard.headline;
  dashEls.focusScore.textContent = dashboard.focus_score;
  dashEls.stateBadge.textContent = dashboard.current_state;
  dashEls.metrics.innerHTML = dashboard.metrics.map(metricCard).join("");
  dashEls.charts.innerHTML = dashboard.charts.map(chartCard).join("");
  dashEls.habits.innerHTML = dashboard.habits.map(habitCard).join("");
  dashEls.insights.innerHTML = dashboard.insights.map(insightCard).join("");
  dashEls.plan.innerHTML = planCard(plan);
  attachPlanEditor(plan);

  if (dashboard.parent_guidance) {
    dashEls.guardianSection.classList.remove("hidden");
    dashEls.parentGuidance.className = "stack";
    dashEls.parentGuidance.innerHTML = guidanceCard(dashboard.parent_guidance);
  } else {
    dashEls.guardianSection.classList.add("hidden");
  }
}

dashEls.backToAuth.addEventListener("click", () => {
  localStorage.removeItem(sessionKey);
  window.location.href = "/";
});

loadDashboard();
