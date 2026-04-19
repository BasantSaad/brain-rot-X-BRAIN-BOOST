const translations = {
  en: {
    eyebrow: "Smart anti-distraction platform",
    title: "Bboo turns profile data and behavior signals into real focus recovery.",
    subtitle: "Create an account, build your profile, then enter a bilingual dashboard with intervention tools, habit coaching, graphs, and parent guidance.",
    profileTitle: "Create profile",
    profileSubtitle: "Important data first, then Bboo opens your dashboard with a personalized account.",
    firstName: "First name",
    lastName: "Last name",
    email: "Email",
    country: "Country",
    language: "Language",
    audience: "Audience",
    view: "Dashboard",
    permissions: "Device permission",
    enterDashboard: "Enter Bboo",
    liveOverview: "Account overview",
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
    eyebrow: "منصة ذكية لمقاومة التشتت",
    title: "Bboo يحول بيانات الملف الشخصي وإشارات السلوك إلى استعادة حقيقية للتركيز.",
    subtitle: "أنشئ حسابا واملأ ملفك الشخصي ثم ادخل إلى لوحة ثنائية اللغة فيها أدوات تدخل وعادات ورسوم بيانية وإرشاد للأهل.",
    profileTitle: "إنشاء الملف الشخصي",
    profileSubtitle: "ابدأ بالبيانات المهمة أولا ثم يفتح Bboo لوحتك بحساب مخصص.",
    firstName: "الاسم الأول",
    lastName: "اسم العائلة",
    email: "البريد الإلكتروني",
    country: "الدولة",
    language: "اللغة",
    audience: "الفئة",
    view: "نوع اللوحة",
    permissions: "صلاحية الجهاز",
    enterDashboard: "الدخول إلى Bboo",
    liveOverview: "نظرة الحساب",
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

const els = {
  language: document.getElementById("language"),
  audience: document.getElementById("audience"),
  mode: document.getElementById("mode"),
  permissions: document.getElementById("permissions"),
  firstName: document.getElementById("firstName"),
  lastName: document.getElementById("lastName"),
  email: document.getElementById("email"),
  country: document.getElementById("country"),
  enterDashboard: document.getElementById("enterDashboard"),
  headline: document.getElementById("headline"),
  focusScore: document.getElementById("focusScore"),
  stateBadge: document.getElementById("stateBadge"),
  profileSummary: document.getElementById("profileSummary"),
  metrics: document.getElementById("metrics"),
  charts: document.getElementById("charts"),
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

function currentQuery() {
  return new URLSearchParams({
    lang: els.language.value,
    audience: els.audience.value,
    mode: els.mode.value,
    permissions: String(els.permissions.checked),
    first_name: els.firstName.value.trim(),
    last_name: els.lastName.value.trim(),
    email: els.email.value.trim(),
    country: els.country.value.trim(),
  });
}

function profileCard(field) {
  return `
    <article class="glass profile-card">
      <small>${field.label}</small>
      <strong>${field.value}</strong>
    </article>
  `;
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

function renderLineOrArea(points, area = false) {
  const w = 560;
  const h = 190;
  const pad = 26;
  const max = Math.max(...points.map((point) => point.value), 100);
  const xStep = points.length > 1 ? (w - pad * 2) / (points.length - 1) : 0;
  const coords = points.map((point, index) => {
    const x = pad + xStep * index;
    const y = h - pad - (point.value / max) * (h - pad * 2);
    return { x, y, label: point.label };
  });
  const path = coords.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
  const areaPath = `${path} L ${coords[coords.length - 1].x} ${h - pad} L ${coords[0].x} ${h - pad} Z`;
  return `
    <svg class="chart-svg" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
      <defs>
        <linearGradient id="chartFill" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="var(--accent-soft)" stop-opacity="0.55"></stop>
          <stop offset="100%" stop-color="var(--accent-soft)" stop-opacity="0.02"></stop>
        </linearGradient>
      </defs>
      <path d="${area ? areaPath : path}" fill="${area ? "url(#chartFill)" : "none"}" stroke="${area ? "none" : "var(--accent-soft)"}"></path>
      <path d="${path}" fill="none" stroke="var(--accent)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"></path>
      ${coords.map((point) => `<circle cx="${point.x}" cy="${point.y}" r="5" fill="var(--secondary-soft)"></circle>`).join("")}
    </svg>
  `;
}

function renderBars(points) {
  const max = Math.max(...points.map((point) => point.value), 100);
  return `
    <div class="chart-shell">
      <svg class="chart-svg" viewBox="0 0 560 190" preserveAspectRatio="none">
        ${points.map((point, index) => {
          const barWidth = 82;
          const gap = 42;
          const x = 28 + index * (barWidth + gap);
          const barHeight = (point.value / max) * 132;
          const y = 162 - barHeight;
          return `<rect x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" rx="18" fill="var(--accent)"></rect>`;
        }).join("")}
      </svg>
      <div class="chart-labels">${points.map((point) => `<span>${point.label}</span>`).join("")}</div>
    </div>
  `;
}

function chartCard(chart) {
  const visual = chart.chart_type === "bar"
    ? renderBars(chart.points)
    : `<div class="chart-shell">${renderLineOrArea(chart.points, chart.chart_type === "area")}<div class="chart-labels">${chart.points.map((point) => `<span>${point.label}</span>`).join("")}</div></div>`;
  return `
    <article class="glass chart-card">
      <h3>${chart.title}</h3>
      <p>${chart.subtitle}</p>
      ${visual}
    </article>
  `;
}

async function loadDashboard() {
  const lang = els.language.value;
  applyI18n(lang);
  document.body.dataset.mode = els.mode.value;
  const query = currentQuery();
  const [dashboardRes, planRes] = await Promise.all([
    fetch(`/api/dashboard?${query}`),
    fetch(`/api/plan?${query}`),
  ]);

  const dashboard = await dashboardRes.json();
  const plan = await planRes.json();

  els.headline.textContent = dashboard.headline;
  els.focusScore.textContent = dashboard.focus_score;
  els.stateBadge.textContent = dashboard.current_state;
  els.profileSummary.innerHTML = dashboard.profile_summary.map(profileCard).join("");
  els.metrics.innerHTML = dashboard.metrics.map(metricCard).join("");
  els.charts.innerHTML = dashboard.charts.map(chartCard).join("");
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

els.enterDashboard.addEventListener("click", loadDashboard);
els.language.addEventListener("change", loadDashboard);
els.audience.addEventListener("change", loadDashboard);
els.mode.addEventListener("change", loadDashboard);
els.permissions.addEventListener("change", loadDashboard);

loadDashboard();
