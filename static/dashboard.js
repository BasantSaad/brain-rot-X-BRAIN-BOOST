const dashboardTranslations = {
  en: {
    dashboardEyebrow: "Bboo dashboard",
    switchAccount: "Switch account",
    brainState: "Brain state",
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
    saveProfile: "Save profile",
    profileTitle: "Profile settings",
    profileSubtitle: "Update the account details that shape your dashboard and saved plan.",
    sessionTitle: "Session status",
    sessionSubtitle: "This dashboard now uses a basic MySQL-backed session token.",
    sessionHintTitle: "How it works",
    sessionHintBody: "When you log in, the backend creates a token, stores it in MySQL, and the browser sends it with each request.",
    scoreLabel: "Focus score",
    firstName: "First name",
    lastName: "Last name",
    email: "Email",
    country: "Country",
    language: "Language",
    audience: "Audience",
    view: "Dashboard",
    permissions: "Device permission",
    loading: "Loading your dashboard...",
    savePlanSuccess: "Your plan was saved in MySQL.",
    saveProfileSuccess: "Your profile was updated successfully.",
    requestError: "We could not reach the server. Please try again.",
    loggedOut: "Your session ended. Please sign in again.",
  },
  ar: {
    dashboardEyebrow: "لوحة Bboo",
    switchAccount: "تبديل الحساب",
    brainState: "حالة الدماغ",
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
    saveProfile: "احفظ الملف",
    profileTitle: "إعدادات الملف",
    profileSubtitle: "حدّث بيانات الحساب التي تشكل لوحتك وخطتك المحفوظة.",
    sessionTitle: "حالة الجلسة",
    sessionSubtitle: "تستخدم هذه اللوحة الآن رمز جلسة أساسي محفوظا في MySQL.",
    sessionHintTitle: "كيف تعمل",
    sessionHintBody: "عند تسجيل الدخول ينشئ الخادم رمزا، ويحفظه في MySQL، ثم يرسله المتصفح مع كل طلب.",
    scoreLabel: "درجة التركيز",
    firstName: "الاسم الأول",
    lastName: "اسم العائلة",
    email: "البريد الإلكتروني",
    country: "الدولة",
    language: "اللغة",
    audience: "الفئة",
    view: "نوع اللوحة",
    permissions: "صلاحية الجهاز",
    loading: "يجري تحميل اللوحة...",
    savePlanSuccess: "تم حفظ الخطة في MySQL.",
    saveProfileSuccess: "تم تحديث الملف بنجاح.",
    requestError: "تعذر الوصول إلى الخادم. حاول مرة أخرى.",
    loggedOut: "انتهت جلستك. سجل الدخول مرة أخرى.",
  },
};

const sessionKey = "bboo-session";
const session = JSON.parse(localStorage.getItem(sessionKey) || "null");

if (!session?.token) {
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
  profileMessage: document.getElementById("profileMessage"),
  sessionMessage: document.getElementById("sessionMessage"),
  profileFirstName: document.getElementById("profileFirstName"),
  profileLastName: document.getElementById("profileLastName"),
  profileEmail: document.getElementById("profileEmail"),
  profileCountry: document.getElementById("profileCountry"),
  profileLanguage: document.getElementById("profileLanguage"),
  profileAudience: document.getElementById("profileAudience"),
  profileMode: document.getElementById("profileMode"),
  profilePermissions: document.getElementById("profilePermissions"),
  saveProfile: document.getElementById("saveProfile"),
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

function authHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${session.token}`,
  };
}

async function apiRequest(url, options = {}) {
  let response;
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        ...(options.headers || {}),
        Authorization: `Bearer ${session.token}`,
      },
    });
  } catch {
    throw new Error(t("requestError"));
  }

  let body = {};
  try {
    body = await response.json();
  } catch {
    body = {};
  }

  if (!response.ok) {
    const message = body.error || t("requestError");
    if (response.status === 401) {
      localStorage.removeItem(sessionKey);
      window.location.href = "/";
      throw new Error(message || t("loggedOut"));
    }
    throw new Error(message);
  }
  return body;
}

function setPanelMessage(element, message, isError = false) {
  element.textContent = message;
  element.classList.toggle("is-error", isError);
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
  return `
    <div class="plan-card editable-plan">
      <strong>${plan.title}</strong>
      <label class="edit-field">
        <span>${t("themeLabel")}</span>
        <input id="planThemeInput" value="${plan.focus_theme}">
      </label>
      <label class="edit-field">
        <span>${t("minutesLabel")}</span>
        <input id="planMinutesInput" type="number" min="10" max="120" value="${plan.recommended_session_minutes}">
      </label>
      <label class="edit-field">
        <span>${t("stepsLabel")}</span>
        <textarea id="planStepsInput" rows="7">${plan.steps.join("\n")}</textarea>
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

function applyProfileForm(profile) {
  dashEls.profileFirstName.value = profile.first_name || "";
  dashEls.profileLastName.value = profile.last_name || "";
  dashEls.profileEmail.value = profile.email || "";
  dashEls.profileCountry.value = profile.country || "";
  dashEls.profileLanguage.value = profile.lang || "en";
  dashEls.profileAudience.value = profile.audience || "student";
  dashEls.profileMode.value = profile.mode || "user";
  dashEls.profilePermissions.checked = String(profile.permissions) === "true";
}

function updateSession(nextSession) {
  Object.assign(session, nextSession);
  localStorage.setItem(sessionKey, JSON.stringify(session));
}

function attachPlanEditor(plan) {
  const saveButton = document.getElementById("savePlanEdits");
  if (!saveButton) {
    return;
  }
  saveButton.addEventListener("click", async () => {
    const steps = document.getElementById("planStepsInput").value
      .split("\n")
      .map((step) => step.trim())
      .filter(Boolean);
    try {
      setPanelMessage(dashEls.sessionMessage, t("loading"));
      const body = await apiRequest("/api/plan", {
        method: "PUT",
        headers: authHeaders(),
        body: JSON.stringify({
          title: plan.title,
          recommended_session_minutes: Number(document.getElementById("planMinutesInput").value),
          focus_theme: document.getElementById("planThemeInput").value.trim(),
          steps,
          attention_game: plan.attention_game,
        }),
      });
      dashEls.plan.innerHTML = planCard(body.plan);
      attachPlanEditor(body.plan);
      setPanelMessage(dashEls.sessionMessage, t("savePlanSuccess"));
    } catch (error) {
      setPanelMessage(dashEls.sessionMessage, error.message, true);
      if (!localStorage.getItem(sessionKey)) {
        window.location.href = "/";
      }
    }
  });
}

async function loadDashboard() {
  applyDashboardI18n(session.lang || "en");
  document.body.dataset.mode = session.mode || "user";
  setPanelMessage(dashEls.sessionMessage, t("loading"));
  const query = new URLSearchParams({
    lang: session.lang || "en",
    mode: session.mode || "user",
  });

  try {
    const [profileBody, dashboard, planBody] = await Promise.all([
      apiRequest("/api/profile"),
      apiRequest(`/api/dashboard?${query.toString()}`),
      apiRequest(`/api/plan?${query.toString()}`),
    ]);

    const profile = profileBody.profile;
    applyProfileForm(profile);
    dashEls.topbarName.textContent = session.first_name || profile.first_name || "Bboo";
    dashEls.headline.textContent = dashboard.headline;
    dashEls.focusScore.textContent = dashboard.focus_score;
    dashEls.stateBadge.textContent = dashboard.current_state;
    dashEls.metrics.innerHTML = dashboard.metrics.map(metricCard).join("");
    dashEls.charts.innerHTML = dashboard.charts.map(chartCard).join("");
    dashEls.habits.innerHTML = dashboard.habits.map(habitCard).join("");
    dashEls.insights.innerHTML = dashboard.insights.map(insightCard).join("");
    dashEls.plan.innerHTML = planCard(planBody);
    attachPlanEditor(planBody);

    if (dashboard.parent_guidance) {
      dashEls.guardianSection.classList.remove("hidden");
      dashEls.parentGuidance.className = "stack";
      dashEls.parentGuidance.innerHTML = guidanceCard(dashboard.parent_guidance);
    } else {
      dashEls.guardianSection.classList.add("hidden");
    }
    setPanelMessage(dashEls.sessionMessage, "");
  } catch (error) {
    setPanelMessage(dashEls.sessionMessage, error.message, true);
    if (!localStorage.getItem(sessionKey)) {
      return;
    }
  }
}

dashEls.saveProfile.addEventListener("click", async () => {
  try {
    setPanelMessage(dashEls.profileMessage, t("loading"));
    const body = await apiRequest("/api/profile", {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify({
        first_name: dashEls.profileFirstName.value.trim(),
        last_name: dashEls.profileLastName.value.trim(),
        country: dashEls.profileCountry.value.trim(),
        lang: dashEls.profileLanguage.value,
        audience: dashEls.profileAudience.value,
        mode: dashEls.profileMode.value,
        permissions: String(dashEls.profilePermissions.checked),
      }),
    });
    updateSession(body.session);
    applyDashboardI18n(session.lang || "en");
    document.body.dataset.mode = session.mode || "user";
    dashEls.topbarName.textContent = session.first_name || "Bboo";
    setPanelMessage(dashEls.profileMessage, t("saveProfileSuccess"));
    await loadDashboard();
  } catch (error) {
    setPanelMessage(dashEls.profileMessage, error.message, true);
    if (!localStorage.getItem(sessionKey)) {
      return;
    }
  }
});

dashEls.backToAuth.addEventListener("click", async () => {
  try {
    await apiRequest("/api/logout", { method: "POST" });
  } catch {
    // Ignore logout failures and clear local state anyway.
  }
  localStorage.removeItem(sessionKey);
  window.location.href = "/";
});

loadDashboard();
