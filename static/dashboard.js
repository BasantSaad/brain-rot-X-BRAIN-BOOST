const sessionKey = "bboo-session";
const session = JSON.parse(localStorage.getItem(sessionKey) || "null");
let latestDashboardPayload = null;
let assistantDockElements = null;

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
  logoutAllDevices: document.getElementById("logoutAllDevices"),
  profileMessage: document.getElementById("profileMessage"),
  settingsMessage: document.getElementById("settingsMessage"),
  sessionMessage: document.getElementById("sessionMessage"),
  checkinMessage: document.getElementById("checkinMessage"),
  timerMessage: document.getElementById("timerMessage"),
  guardianMessage: document.getElementById("guardianMessage"),
  appUsageMessage: document.getElementById("appUsageMessage"),
  weeklySummary: document.getElementById("weeklySummary"),
  suggestions: document.getElementById("suggestions"),
  checkinHistory: document.getElementById("checkinHistory"),
  timerHistory: document.getElementById("timerHistory"),
  planHistory: document.getElementById("planHistory"),
  appUsageEntries: document.getElementById("appUsageEntries"),
  appUsageApps: document.getElementById("appUsageApps"),
  appUsageDetail: document.getElementById("appUsageDetail"),
  profileFirstName: document.getElementById("profileFirstName"),
  profileLastName: document.getElementById("profileLastName"),
  profileEmail: document.getElementById("profileEmail"),
  profileCountry: document.getElementById("profileCountry"),
  profileLanguage: document.getElementById("profileLanguage"),
  profileAudience: document.getElementById("profileAudience"),
  profileMode: document.getElementById("profileMode"),
  profilePermissions: document.getElementById("profilePermissions"),
  saveProfile: document.getElementById("saveProfile"),
  appName: document.getElementById("appName"),
  studyStart: document.getElementById("studyStart"),
  bedtimeTarget: document.getElementById("bedtimeTarget"),
  sleepTargetHours: document.getElementById("sleepTargetHours"),
  defaultSessionMinutes: document.getElementById("defaultSessionMinutes"),
  saveSettings: document.getElementById("saveSettings"),
  moodValue: document.getElementById("moodValue"),
  energyValue: document.getElementById("energyValue"),
  checkinNotes: document.getElementById("checkinNotes"),
  saveCheckin: document.getElementById("saveCheckin"),
  timerLabel: document.getElementById("timerLabel"),
  timerMinutes: document.getElementById("timerMinutes"),
  startTimer: document.getElementById("startTimer"),
  completeTimer: document.getElementById("completeTimer"),
  childEmail: document.getElementById("childEmail"),
  linkChild: document.getElementById("linkChild"),
  usageAppName: document.getElementById("usageAppName"),
  usageDate: document.getElementById("usageDate"),
  usageHours: document.getElementById("usageHours"),
  saveAppUsage: document.getElementById("saveAppUsage"),
  assistantPrompt: document.getElementById("assistantPrompt"),
  assistantSend: document.getElementById("assistantSend"),
  assistantHistory: document.getElementById("assistantHistory"),
  assistantMessage: document.getElementById("assistantMessage"),
};

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
    throw new Error("We could not reach the server. Please try again.");
  }

  let body = {};
  try {
    body = await response.json();
  } catch {
    body = {};
  }

  if (!response.ok) {
    const message = body.error || "We could not complete that request.";
    if (response.status === 401) {
      localStorage.removeItem(sessionKey);
      window.location.href = "/";
    }
    throw new Error(message);
  }
  return body;
}

function setPanelMessage(element, message, isError = false) {
  if (!element) {
    return;
  }
  element.textContent = message || "";
  element.classList.toggle("is-error", isError);
}

function updateSession(nextSession) {
  Object.assign(session, nextSession);
  localStorage.setItem(sessionKey, JSON.stringify(session));
  document.body.dataset.mode = session.mode || "user";
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
          <span>Apps today</span>
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

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

function buildReactiveUsageChart(usage) {
  const todaysEntries = (usage.recent_entries || []).filter((item) => item.usage_date === todayIsoDate());
  if (!todaysEntries.length) {
    return null;
  }
  const totals = new Map();
  todaysEntries.forEach((item) => {
    totals.set(item.app_name, (totals.get(item.app_name) || 0) + Number(item.usage_hours || 0));
  });
  const points = [...totals.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([label, value]) => ({ label, value: Number(value.toFixed(1)) }));
  if (!points.length) {
    return null;
  }
  return {
    title: "Today's app usage",
    subtitle: "A reactive donut view built from your saved app usage entries for today.",
    chart_type: "donut",
    points,
  };
}

function renderDashboardCharts(dashboard, usage = null) {
  if (!dashEls.charts) {
    return;
  }
  const charts = [...(dashboard?.charts || [])];
  const reactiveUsageChart = usage ? buildReactiveUsageChart(usage) : null;
  if (reactiveUsageChart) {
    const donutIndex = charts.findIndex((chart) => chart.chart_type === "donut");
    if (donutIndex >= 0) {
      charts[donutIndex] = reactiveUsageChart;
    } else {
      charts.push(reactiveUsageChart);
    }
  }
  dashEls.charts.innerHTML = charts.map(chartCard).join("");
}

function planCard(plan) {
  return `
    <div class="plan-card editable-plan">
      <strong>${plan.title}</strong>
      <label class="edit-field">
        <span>Theme</span>
        <input id="planThemeInput" value="${plan.focus_theme}">
      </label>
      <label class="edit-field">
        <span>Session minutes</span>
        <input id="planMinutesInput" type="number" min="10" max="120" value="${plan.recommended_session_minutes}">
      </label>
      <label class="edit-field">
        <span>Steps</span>
        <textarea id="planStepsInput" rows="7">${plan.steps.join("\n")}</textarea>
      </label>
      <p><strong>${plan.attention_game}</strong></p>
      <button id="savePlanEdits" class="ghost-btn save-plan-btn" type="button">Save my edits</button>
    </div>
  `;
}

function weeklySummaryCards(summary) {
  const cards = [
    { label: "Weekly headline", value: summary.headline },
    { label: "Completed sessions", value: `${summary.completed_sessions_this_week} this week / ${summary.completed_sessions_last_week} last week` },
    { label: "Average focus score", value: `${summary.average_focus_score_this_week} this week / ${summary.average_focus_score_last_week} last week` },
    { label: "Check-in streak", value: `${summary.checkin_streak} day(s)` },
    { label: "Weekly goal", value: `${summary.weekly_goal_completion}% complete` },
    { label: "Milestone", value: summary.milestone },
  ];
  return cards.map((card) => `<div class="summary-card"><small>${card.label}</small><strong>${card.value}</strong></div>`).join("");
}

function suggestionCards(suggestions) {
  const cards = [
    { title: "Best study time", body: suggestions.best_study_time },
    { title: "Sleep protection time", body: suggestions.sleep_protection_time },
    { title: "Risk window", body: suggestions.risk_window },
    { title: "Summary", body: suggestions.summary },
    { title: "Energy note", body: suggestions.energy_note },
  ];
  return cards.map((card) => `<div class="insight-card"><strong>${card.title}</strong><p>${card.body}</p></div>`).join("");
}

function checkinCards(items) {
  if (!items.length) {
    return `<div class="empty-state mini-empty">No check-ins yet. Save one to start your trend history.</div>`;
  }
  return items.map((item) => `
    <div class="history-card">
      <strong>${new Date(item.created_at).toLocaleString()}</strong>
      <p>Mood ${item.mood}/5, energy ${item.energy}/5</p>
      <p>${item.notes || "No notes added."}</p>
    </div>
  `).join("");
}

function timerCards(items) {
  if (!items.length) {
    return `<div class="empty-state mini-empty">No timer sessions yet. Start one to build your weekly analytics.</div>`;
  }
  return items.map((item) => `
    <div class="history-card ${item.status === "active" ? "active-history" : ""}">
      <strong>${item.label}</strong>
      <p>${item.planned_minutes} min • ${item.status}</p>
      <p>Started ${new Date(item.started_at).toLocaleString()}</p>
      <p>${item.completed_at ? `Finished ${new Date(item.completed_at).toLocaleString()}` : "Still running"}</p>
      <span class="tiny-id" data-timer-id="${item.id}">Timer #${item.id}</span>
    </div>
  `).join("");
}

function planHistoryCards(items) {
  if (!items.length) {
    return `<div class="empty-state mini-empty">No saved plan history yet.</div>`;
  }
  return items.map((item) => `
    <div class="history-card">
      <strong>${new Date(item.saved_at).toLocaleString()}</strong>
      <p>${item.focus_theme} • ${item.recommended_session_minutes} min</p>
      <p>${item.steps[0] || "No steps saved."}</p>
    </div>
  `).join("");
}

function childCards(items) {
  if (!items.length) {
    return `<div class="empty-state mini-empty">No linked child accounts yet.</div>`;
  }
  return items.map((item) => `
    <div class="history-card">
      <strong>${item.name}</strong>
      <p>${item.email}</p>
      <p>Focus score ${item.focus_score} • ${item.current_state}</p>
      <p>${item.summary}</p>
      <p>Weekly goal ${item.weekly_goal_completion}% complete</p>
    </div>
  `).join("");
}

function appUsageEntryCards(items) {
  if (!items.length) {
    return `<div class="empty-state mini-empty">No app usage added yet. Save an app and a day to begin your 7-day view.</div>`;
  }
  return items.map((item) => `
    <div class="history-card">
      <strong>${item.app_name}</strong>
      <p>${item.usage_hours} hour(s)</p>
      <p>${item.usage_date}</p>
    </div>
  `).join("");
}

function appUsageChips(apps, selectedApp) {
  if (!apps.length) {
    return `<div class="empty-state mini-empty">No app summaries yet.</div>`;
  }
  return apps.map((app) => `
    <button class="app-chip ${app.app_name === selectedApp ? "is-selected" : ""}" data-app-name="${app.app_name}" type="button">
      <strong>${app.app_name}</strong>
      <span>${app.total_hours}h / 7 days</span>
    </button>
  `).join("");
}

function appUsageDetailCard(detail) {
  if (!detail?.app_name) {
    return `Add or select an app to view its 7-day history.`;
  }
  const max = Math.max(...detail.days.map((day) => day.hours), 1);
  return `
    <div class="usage-detail-card">
      <div class="usage-detail-head">
        <strong>${detail.app_name}</strong>
        <span>${detail.total_hours}h in the last 7 days</span>
      </div>
      <div class="usage-bars">
        ${detail.days.map((day) => `
          <div class="usage-bar-col">
            <span class="usage-bar-value">${day.hours}h</span>
            <div class="usage-bar-track">
              <div class="usage-bar-fill" style="height:${(day.hours / max) * 100}%"></div>
            </div>
            <small>${day.label}</small>
          </div>
        `).join("")}
      </div>
    </div>
  `;
}

function assistantHistoryCards(items) {
  if (!items.length) {
    return `<div class="empty-state mini-empty">No assistant messages yet. Ask Bboo to update a setting or explain your progress.</div>`;
  }
  return items.map((item) => `
    <article class="assistant-bubble ${item.role === "assistant" ? "assistant-bubble-agent" : "assistant-bubble-user"}">
      <div class="assistant-bubble-head">
        <strong>${item.role === "assistant" ? "Bboo assistant" : "You"}</strong>
        <small>${new Date(item.created_at).toLocaleString()}</small>
      </div>
      <p>${item.message}</p>
      ${item.tool_name ? `<span class="assistant-tool-tag">${item.tool_name}</span>` : ""}
    </article>
  `).join("");
}

function ensureAssistantDock() {
  if (assistantDockElements || !document.body) {
    return assistantDockElements;
  }
  const shell = document.createElement("div");
  shell.className = "assistant-dock";
  shell.innerHTML = `
    <button class="assistant-dock-toggle" type="button">Assistant</button>
    <div class="assistant-dock-panel hidden">
      <div class="assistant-dock-head">
        <strong>Bboo assistant</strong>
        <button class="assistant-dock-close ghost-btn" type="button">Close</button>
      </div>
      <p class="assistant-dock-copy">Ask me to change settings, start a timer, or explain your progress.</p>
      <div class="assistant-dock-thread empty-state">No assistant messages yet.</div>
      <textarea class="assistant-dock-input" rows="3" placeholder="Change my session time to 45 minutes"></textarea>
      <button class="assistant-dock-send ghost-btn save-panel-btn" type="button">Send</button>
      <div class="assistant-dock-status panel-message"></div>
    </div>
  `;
  document.body.appendChild(shell);
  assistantDockElements = {
    shell,
    toggle: shell.querySelector(".assistant-dock-toggle"),
    panel: shell.querySelector(".assistant-dock-panel"),
    close: shell.querySelector(".assistant-dock-close"),
    thread: shell.querySelector(".assistant-dock-thread"),
    input: shell.querySelector(".assistant-dock-input"),
    send: shell.querySelector(".assistant-dock-send"),
    status: shell.querySelector(".assistant-dock-status"),
  };
  assistantDockElements.toggle.addEventListener("click", () => assistantDockElements.panel.classList.toggle("hidden"));
  assistantDockElements.close.addEventListener("click", () => assistantDockElements.panel.classList.add("hidden"));
  assistantDockElements.send.addEventListener("click", submitAssistantDockMessage);
  return assistantDockElements;
}

function renderAssistantEverywhere(items) {
  if (dashEls.assistantHistory) {
    dashEls.assistantHistory.innerHTML = assistantHistoryCards(items);
  }
  const dock = ensureAssistantDock();
  if (dock) {
    dock.thread.className = "assistant-dock-thread";
    dock.thread.innerHTML = assistantHistoryCards(items);
  }
}

async function submitAssistantMessage(message, statusElement, inputElement) {
  if (!message) {
    setPanelMessage(statusElement, "Type a message for the assistant first.", true);
    return;
  }
  setPanelMessage(statusElement, "Assistant is working...");
  const body = await apiRequest("/api/agent/chat", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({
      message,
      lang: session.lang || "en",
      mode: session.mode || "user",
    }),
  });
  if (inputElement) {
    inputElement.value = "";
  }
  renderAssistantEverywhere(body.history || []);
  latestDashboardPayload = body.dashboard || latestDashboardPayload;
  if (body.settings) {
    applySettingsForm(body.settings);
  }
  if (body.dashboard) {
    if (dashEls.headline) dashEls.headline.textContent = body.dashboard.headline;
    if (dashEls.focusScore) dashEls.focusScore.textContent = body.dashboard.focus_score;
    if (dashEls.stateBadge) dashEls.stateBadge.textContent = body.dashboard.current_state;
    if (dashEls.metrics) dashEls.metrics.innerHTML = body.dashboard.metrics.map(metricCard).join("");
    renderDashboardCharts(body.dashboard);
  }
  setPanelMessage(statusElement, body.assistant?.reply || "Done.");
  await Promise.all([
    loadWeeklySummary(),
    loadSuggestions(),
    loadTimers(),
    loadPlanHistory(),
    loadSettings(),
    loadAppUsage(),
  ]);
}

async function submitAssistantDockMessage() {
  const dock = ensureAssistantDock();
  try {
    await submitAssistantMessage(dock.input.value.trim(), dock.status, dock.input);
  } catch (error) {
    setPanelMessage(dock.status, error.message, true);
  }
}

function applyProfileForm(profile) {
  if (!dashEls.profileFirstName) {
    return;
  }
  dashEls.profileFirstName.value = profile.first_name || "";
  dashEls.profileLastName.value = profile.last_name || "";
  dashEls.profileEmail.value = profile.email || "";
  dashEls.profileCountry.value = profile.country || "";
  dashEls.profileLanguage.value = profile.lang || "en";
  dashEls.profileAudience.value = profile.audience || "student";
  dashEls.profileMode.value = profile.mode || "user";
  dashEls.profilePermissions.checked = String(profile.permissions) === "true";
}

function applySettingsForm(settings) {
  if (!dashEls.appName) {
    return;
  }
  dashEls.appName.value = settings.app_name || "Bboo";
  dashEls.studyStart.value = settings.study_start || "16:00";
  dashEls.bedtimeTarget.value = settings.bedtime_target || "22:30";
  dashEls.sleepTargetHours.value = settings.sleep_target_hours || 8;
  dashEls.defaultSessionMinutes.value = settings.default_session_minutes || 30;
  dashEls.topbarName.textContent = settings.app_name || session.first_name || "Bboo";
}

function attachPlanEditor(plan) {
  if (!dashEls.plan) {
    return;
  }
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
      setPanelMessage(dashEls.sessionMessage, "Saving your plan...");
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
      setPanelMessage(dashEls.sessionMessage, body.message || "Your plan was saved.");
      await loadPlanHistory();
      await loadWeeklySummary();
    } catch (error) {
      setPanelMessage(dashEls.sessionMessage, error.message, true);
    }
  });
}

async function loadPlanHistory() {
  if (!dashEls.planHistory) {
    return;
  }
  const body = await apiRequest("/api/plan-history");
  dashEls.planHistory.innerHTML = planHistoryCards(body.items || []);
}

async function loadWeeklySummary() {
  if (!dashEls.weeklySummary) {
    return;
  }
  const body = await apiRequest("/api/weekly-summary");
  dashEls.weeklySummary.innerHTML = weeklySummaryCards(body.summary || {});
}

async function loadSuggestions() {
  if (!dashEls.suggestions) {
    return;
  }
  const body = await apiRequest("/api/suggestions");
  dashEls.suggestions.innerHTML = suggestionCards(body.suggestions || {});
}

async function loadCheckins() {
  if (!dashEls.checkinHistory) {
    return;
  }
  const body = await apiRequest("/api/checkins");
  dashEls.checkinHistory.innerHTML = checkinCards(body.items || []);
}

async function loadTimers() {
  if (!dashEls.timerHistory) {
    return;
  }
  const body = await apiRequest("/api/timers");
  dashEls.timerHistory.innerHTML = timerCards(body.items || []);
}

async function loadChildren() {
  if (!dashEls.guardianSection || !dashEls.parentGuidance) {
    return;
  }
  if ((session.mode || "user") !== "parent") {
    dashEls.guardianSection.classList.add("hidden");
    return;
  }
  dashEls.guardianSection.classList.remove("hidden");
  const body = await apiRequest("/api/children");
  dashEls.parentGuidance.className = "stack";
  dashEls.parentGuidance.innerHTML = childCards(body.items || []);
}

async function loadAppUsageDetail(appName) {
  if (!dashEls.appUsageDetail) {
    return;
  }
  if (!appName) {
    dashEls.appUsageDetail.className = "usage-detail-shell empty-state";
    dashEls.appUsageDetail.innerHTML = "Add or select an app to view its 7-day history.";
    return;
  }
  const body = await apiRequest(`/api/app-usage-detail?app=${encodeURIComponent(appName)}`);
  dashEls.appUsageDetail.className = "usage-detail-shell";
  dashEls.appUsageDetail.innerHTML = appUsageDetailCard(body.detail);
}

async function loadAppUsage(preferredAppName = null) {
  if (!dashEls.appUsageEntries || !dashEls.appUsageApps) {
    return;
  }
  const body = await apiRequest("/api/app-usage");
  const usage = body.usage || { apps: [], recent_entries: [], selected_app: null };
  dashEls.appUsageEntries.innerHTML = appUsageEntryCards(usage.recent_entries || []);
  if (latestDashboardPayload) {
    renderDashboardCharts(latestDashboardPayload, usage);
  }
  const selectedApp = preferredAppName || usage.selected_app;
  dashEls.appUsageApps.innerHTML = appUsageChips(usage.apps || [], selectedApp);
  dashEls.appUsageApps.querySelectorAll("[data-app-name]").forEach((button) => {
    button.addEventListener("click", () => {
      loadAppUsage(button.dataset.appName);
    });
  });
  await loadAppUsageDetail(selectedApp);
}

async function loadSettings() {
  if (!dashEls.appName) {
    return;
  }
  const body = await apiRequest("/api/settings");
  applySettingsForm(body.settings || {});
}

async function loadAgentHistory() {
  ensureAssistantDock();
  const body = await apiRequest("/api/agent/history");
  renderAssistantEverywhere(body.items || []);
}

async function loadDashboard() {
  document.body.dataset.mode = session.mode || "user";
  setPanelMessage(dashEls.sessionMessage, "Loading your dashboard...");
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
    latestDashboardPayload = dashboard;
    applyProfileForm(profile);
    if (dashEls.topbarName) dashEls.topbarName.textContent = dashboard.app_name || session.first_name || profile.first_name || "Bboo";
    if (dashEls.headline) dashEls.headline.textContent = dashboard.headline;
    if (dashEls.focusScore) dashEls.focusScore.textContent = dashboard.focus_score;
    if (dashEls.stateBadge) dashEls.stateBadge.textContent = dashboard.current_state;
    if (dashEls.metrics) dashEls.metrics.innerHTML = dashboard.metrics.map(metricCard).join("");
    if (dashEls.charts) renderDashboardCharts(dashboard);
    if (dashEls.habits) dashEls.habits.innerHTML = dashboard.habits.map(habitCard).join("");
    if (dashEls.insights) dashEls.insights.innerHTML = dashboard.insights.map(insightCard).join("");
    if (dashEls.plan) dashEls.plan.innerHTML = planCard(planBody);
    attachPlanEditor(planBody);

    if (dashboard.parent_guidance && dashEls.parentGuidance) {
      dashEls.parentGuidance.className = "stack";
      dashEls.parentGuidance.innerHTML = guidanceCard(dashboard.parent_guidance);
    }
    setPanelMessage(dashEls.sessionMessage, "");
  } catch (error) {
    setPanelMessage(dashEls.sessionMessage, error.message, true);
  }
}

if (dashEls.saveProfile) dashEls.saveProfile.addEventListener("click", async () => {
  try {
    setPanelMessage(dashEls.profileMessage, "Saving profile...");
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
    setPanelMessage(dashEls.profileMessage, "Your profile was updated successfully.");
    await loadDashboard();
    await loadChildren();
  } catch (error) {
    setPanelMessage(dashEls.profileMessage, error.message, true);
  }
});

if (dashEls.saveSettings) dashEls.saveSettings.addEventListener("click", async () => {
  try {
    setPanelMessage(dashEls.settingsMessage, "Saving settings...");
    const body = await apiRequest("/api/settings", {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify({
        app_name: dashEls.appName.value.trim(),
        study_start: dashEls.studyStart.value,
        bedtime_target: dashEls.bedtimeTarget.value,
        sleep_target_hours: Number(dashEls.sleepTargetHours.value),
        default_session_minutes: Number(dashEls.defaultSessionMinutes.value),
      }),
    });
    applySettingsForm(body.settings);
    setPanelMessage(dashEls.settingsMessage, body.message || "Settings saved.");
    await loadSuggestions();
  } catch (error) {
    setPanelMessage(dashEls.settingsMessage, error.message, true);
  }
});

if (dashEls.saveCheckin) dashEls.saveCheckin.addEventListener("click", async () => {
  try {
    setPanelMessage(dashEls.checkinMessage, "Saving check-in...");
    const body = await apiRequest("/api/checkins", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        mood: Number(dashEls.moodValue.value),
        energy: Number(dashEls.energyValue.value),
        notes: dashEls.checkinNotes.value.trim(),
      }),
    });
    dashEls.checkinHistory.innerHTML = checkinCards(body.items || []);
    dashEls.checkinNotes.value = "";
    setPanelMessage(dashEls.checkinMessage, body.message || "Daily check-in saved.");
    await loadWeeklySummary();
    await loadSuggestions();
  } catch (error) {
    setPanelMessage(dashEls.checkinMessage, error.message, true);
  }
});

if (dashEls.startTimer) dashEls.startTimer.addEventListener("click", async () => {
  try {
    setPanelMessage(dashEls.timerMessage, "Starting timer...");
    const body = await apiRequest("/api/focus-timer/start", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        label: dashEls.timerLabel.value.trim(),
        minutes: Number(dashEls.timerMinutes.value),
      }),
    });
    dashEls.timerHistory.innerHTML = timerCards(body.items || []);
    setPanelMessage(dashEls.timerMessage, body.message || "Timer started.");
  } catch (error) {
    setPanelMessage(dashEls.timerMessage, error.message, true);
  }
});

if (dashEls.completeTimer) dashEls.completeTimer.addEventListener("click", async () => {
  const timerNode = dashEls.timerHistory.querySelector(".active-history [data-timer-id]") || dashEls.timerHistory.querySelector("[data-timer-id]");
  if (!timerNode) {
    setPanelMessage(dashEls.timerMessage, "Start a timer first so there is one to complete.", true);
    return;
  }
  try {
    setPanelMessage(dashEls.timerMessage, "Completing timer...");
    const body = await apiRequest("/api/focus-timer/complete", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        timer_id: Number(timerNode.dataset.timerId),
        completed: true,
      }),
    });
    dashEls.timerHistory.innerHTML = timerCards(body.items || []);
    setPanelMessage(dashEls.timerMessage, body.message || "Timer updated.");
    await loadWeeklySummary();
    await loadSuggestions();
  } catch (error) {
    setPanelMessage(dashEls.timerMessage, error.message, true);
  }
});

if (dashEls.linkChild) dashEls.linkChild.addEventListener("click", async () => {
  try {
    setPanelMessage(dashEls.guardianMessage, "Linking child account...");
    const body = await apiRequest("/api/guardian-link", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        child_email: dashEls.childEmail.value.trim(),
      }),
    });
    dashEls.parentGuidance.className = "stack";
    dashEls.parentGuidance.innerHTML = childCards(body.items || []);
    dashEls.childEmail.value = "";
    setPanelMessage(dashEls.guardianMessage, body.message || "Child account linked.");
  } catch (error) {
    setPanelMessage(dashEls.guardianMessage, error.message, true);
  }
});

if (dashEls.saveAppUsage) dashEls.saveAppUsage.addEventListener("click", async () => {
  try {
    setPanelMessage(dashEls.appUsageMessage, "Saving app usage...");
    const body = await apiRequest("/api/app-usage", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        app_name: dashEls.usageAppName.value.trim(),
        usage_date: dashEls.usageDate.value,
        usage_hours: Number(dashEls.usageHours.value),
      }),
    });
    setPanelMessage(dashEls.appUsageMessage, body.message || "App usage was saved.");
    await loadDashboard();
    await loadAppUsage(dashEls.usageAppName.value.trim());
    await loadWeeklySummary();
    await loadSuggestions();
  } catch (error) {
    setPanelMessage(dashEls.appUsageMessage, error.message, true);
  }
});

if (dashEls.assistantSend) dashEls.assistantSend.addEventListener("click", async () => {
  try {
    await submitAssistantMessage(dashEls.assistantPrompt.value.trim(), dashEls.assistantMessage, dashEls.assistantPrompt);
  } catch (error) {
    setPanelMessage(dashEls.assistantMessage, error.message, true);
  }
});

if (dashEls.logoutAllDevices) dashEls.logoutAllDevices.addEventListener("click", async () => {
  try {
    const body = await apiRequest("/api/logout-all-devices", {
      method: "POST",
      headers: authHeaders(),
    });
    setPanelMessage(dashEls.sessionMessage, body.message || "Other sessions were signed out.");
  } catch (error) {
    setPanelMessage(dashEls.sessionMessage, error.message, true);
  }
});

if (dashEls.backToAuth) dashEls.backToAuth.addEventListener("click", async () => {
  try {
    await apiRequest("/api/logout", { method: "POST" });
  } catch {
    // Ignore logout failures and clear local state anyway.
  }
  localStorage.removeItem(sessionKey);
  window.location.href = "/";
});

async function bootstrap() {
  if (dashEls.usageDate) {
    dashEls.usageDate.value = new Date().toISOString().slice(0, 10);
  }
  await loadDashboard();
  await Promise.all([
    loadSettings(),
    loadPlanHistory(),
    loadWeeklySummary(),
    loadSuggestions(),
    loadCheckins(),
    loadTimers(),
    loadAppUsage(),
    loadChildren(),
    loadAgentHistory(),
  ]);
}

bootstrap().catch((error) => {
  setPanelMessage(dashEls.sessionMessage, error.message || "We could not finish loading the dashboard.", true);
});
