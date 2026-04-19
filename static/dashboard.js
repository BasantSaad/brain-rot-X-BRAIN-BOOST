const dashboardTranslations = {
  en: {
    dashboardEyebrow: "Bboo dashboard",
    switchAccount: "Switch account",
    brainState: "Brain state",
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
    dashboardEyebrow: "لوحة Bboo",
    switchAccount: "تبديل الحساب",
    brainState: "حالة الدماغ",
    scoreLabel: "درجة التركيز",
    habitsTitle: "معزز العادات",
    habitsSubtitle: "خطوات صغيرة تدرب الانتباه كل يوم.",
    planTitle: "الخطة الشخصية",
    planSubtitle: "جلسات تركيز وحدود ذكية وطقوس استعادة.",
    insightsTitle: "رؤى عملية",
    insightsSubtitle: "توصيات مبنية على الإشارات السلوكية.",
    parentTitle: "إرشاد ولي الأمر",
    parentSubtitle: "متابعة صحية للمستخدمين الأصغر سنا.",
    noParent: "بدل إلى وضع ولي الأمر لرؤية الإرشادات.",
  },
};

const sessionKey = "bboo-session";
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
  backToAuth: document.getElementById("backToAuth"),
};

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
  return `<div class="plan-card"><strong>${plan.title}</strong><p>${plan.focus_theme} · ${plan.recommended_session_minutes} min</p><ul>${plan.steps.map((step) => `<li>${step}</li>`).join("")}</ul><p><strong>${plan.attention_game}</strong></p></div>`;
}

function guidanceCard(guidance) {
  return `<div class="guidance-card"><p>${guidance.summary}</p><ul>${guidance.recommended_actions.map((step) => `<li>${step}</li>`).join("")}</ul></div>`;
}

function renderLineOrArea(points, area = false) {
  const w = 560;
  const h = 190;
  const pad = 26;
  const max = Math.max(...points.map((point) => point.value), 100);
  const xStep = points.length > 1 ? (w - pad * 2) / (points.length - 1) : 0;
  const coords = points.map((point, index) => {
    const x = pad + xStep * index;
    const y = h - pad - (point.value / max) * (h - pad * 2);
    return { x, y };
  });
  const path = coords.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
  const areaPath = `${path} L ${coords[coords.length - 1].x} ${h - pad} L ${coords[0].x} ${h - pad} Z`;
  return `<svg class="chart-svg" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><defs><linearGradient id="chartFill" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="var(--accent-soft)" stop-opacity="0.65"></stop><stop offset="100%" stop-color="var(--accent-soft)" stop-opacity="0.04"></stop></linearGradient></defs><path d="${area ? areaPath : path}" fill="${area ? "url(#chartFill)" : "none"}" stroke="${area ? "none" : "var(--accent-soft)"}"></path><path d="${path}" fill="none" stroke="var(--accent)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"></path>${coords.map((point) => `<circle cx="${point.x}" cy="${point.y}" r="5" fill="var(--secondary-soft)"></circle>`).join("")}</svg>`;
}

function renderBars(points) {
  const max = Math.max(...points.map((point) => point.value), 100);
  return `<div class="chart-shell"><svg class="chart-svg" viewBox="0 0 560 190" preserveAspectRatio="none">${points.map((point, index) => {
    const barWidth = 82;
    const gap = 42;
    const x = 28 + index * (barWidth + gap);
    const barHeight = (point.value / max) * 132;
    const y = 162 - barHeight;
    return `<rect x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" rx="18" fill="var(--accent)"></rect>`;
  }).join("")}</svg><div class="chart-labels">${points.map((point) => `<span>${point.label}</span>`).join("")}</div></div>`;
}

function chartCard(chart) {
  const visual = chart.chart_type === "bar"
    ? renderBars(chart.points)
    : `<div class="chart-shell">${renderLineOrArea(chart.points, chart.chart_type === "area")}<div class="chart-labels">${chart.points.map((point) => `<span>${point.label}</span>`).join("")}</div></div>`;
  return `<article class="glass chart-card"><h3>${chart.title}</h3><p>${chart.subtitle}</p>${visual}</article>`;
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

  dashEls.topbarName.textContent = `${session.first_name || "Bboo"} ${session.last_name || ""}`.trim();
  dashEls.topbarName.textContent = session.first_name || "Bboo";
  dashEls.headline.textContent = dashboard.headline;
  dashEls.focusScore.textContent = dashboard.focus_score;
  dashEls.stateBadge.textContent = dashboard.current_state;
  dashEls.metrics.innerHTML = dashboard.metrics.map(metricCard).join("");
  dashEls.charts.innerHTML = dashboard.charts.map(chartCard).join("");
  dashEls.habits.innerHTML = dashboard.habits.map(habitCard).join("");
  dashEls.insights.innerHTML = dashboard.insights.map(insightCard).join("");
  dashEls.plan.innerHTML = planCard(plan);

  if (dashboard.parent_guidance) {
    dashEls.parentGuidance.className = "stack";
    dashEls.parentGuidance.innerHTML = guidanceCard(dashboard.parent_guidance);
  } else {
    dashEls.parentGuidance.className = "stack empty-state";
    dashEls.parentGuidance.textContent = dashboardTranslations[session.lang || "en"].noParent;
  }
}

dashEls.backToAuth.addEventListener("click", () => {
  localStorage.removeItem(sessionKey);
  window.location.href = "/";
});

loadDashboard();
