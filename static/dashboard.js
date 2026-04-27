const sessionKey = "bboo-session";
const session = JSON.parse(localStorage.getItem(sessionKey) || "null");

if (!session?.token) {
  window.location.href = "/";
}

const els = {
  topbarName: document.getElementById("topbarName"),
  topbarSubtitle: document.getElementById("topbarSubtitle"),
  headline: document.getElementById("headline"),
  focusScore: document.getElementById("focusScore"),
  stateBadge: document.getElementById("stateBadge"),
  metrics: document.getElementById("metrics"),
  charts: document.getElementById("charts"),
  habits: document.getElementById("habits"),
  insights: document.getElementById("insights"),
  plan: document.getElementById("plan"),
  planHistory: document.getElementById("planHistory"),
  parentGuidance: document.getElementById("parentGuidance"),
  guardianSection: document.getElementById("guardianSection"),
  settingsMessage: document.getElementById("settingsMessage"),
  profileMessage: document.getElementById("profileMessage"),
  timerMessage: document.getElementById("timerMessage"),
  checkinMessage: document.getElementById("checkinMessage"),
  childrenMessage: document.getElementById("childrenMessage"),
  weeklySummary: document.getElementById("weeklySummary"),
  suggestions: document.getElementById("suggestions"),
  timers: document.getElementById("timers"),
  checkins: document.getElementById("checkins"),
  children: document.getElementById("children"),
};

function setMessage(element, message, isError = false) {
  if (!element) return;
  element.textContent = message;
  element.classList.toggle("is-error", isError);
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
    throw new Error("Could not reach the server.");
  }
  let body = {};
  try {
    body = await response.json();
  } catch {
    body = {};
  }
  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem(sessionKey);
      window.location.href = "/";
    }
    throw new Error(body.error || "Request failed.");
  }
  return body;
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
      <label class="edit-field"><span>Theme</span><input id="planThemeInput" value="${plan.focus_theme}"></label>
      <label class="edit-field"><span>Session minutes</span><input id="planMinutesInput" type="number" min="10" max="120" value="${plan.recommended_session_minutes}"></label>
      <label class="edit-field"><span>Steps</span><textarea id="planStepsInput" rows="7">${plan.steps.join("\n")}</textarea></label>
      <p><strong>${plan.attention_game}</strong></p>
      <button id="savePlanEdits" class="ghost-btn save-plan-btn" type="button">Save my edits</button>
    </div>
  `;
}

function chartCard(chart) {
  const items = chart.points.map((point) => `<div class="legend-row"><span>${point.label}</span><strong>${point.value}</strong></div>`).join("");
  return `<article class="glass chart-card"><h3>${chart.title}</h3><p>${chart.subtitle}</p><div class="stack">${items}</div></article>`;
}

function summaryCard(summary) {
  return `
    <div class="guidance-card">
      <strong>${summary.headline}</strong>
      <p>Improvement: ${summary.improvement_percent}%</p>
      <p>Streak: ${summary.streak_days} days</p>
      <p>Completed sessions: ${summary.completed_sessions}</p>
      <p>Average focus time: ${summary.average_focus_minutes} minutes</p>
      <p><strong>${summary.recommendation}</strong></p>
    </div>
  `;
}

function suggestionCards(suggestions) {
  return `
    <div class="guidance-card"><strong>Best study time</strong><p>${suggestions.best_study_time}</p></div>
    <div class="guidance-card"><strong>Best sleep protection time</strong><p>${suggestions.best_sleep_protection_time}</p></div>
    <div class="guidance-card"><strong>Risk window</strong><p>${suggestions.risk_window}</p></div>
  `;
}

function listCards(items, mapper, empty) {
  if (!items.length) {
    return `<div class="empty-state">${empty}</div>`;
  }
  return items.map(mapper).join("");
}

function timerCard(item) {
  return `<div class="insight-card"><strong>${item.label}</strong><p>Planned: ${item.planned_minutes}m | Actual: ${item.actual_minutes}m</p><p>${item.completed ? "Completed" : "In progress"}</p></div>`;
}

function checkinCard(item) {
  return `<div class="insight-card"><strong>${item.mood} / ${item.energy}</strong><p>Focus feeling: ${item.focus_feeling}/10</p><p>${item.notes || "No notes."}</p></div>`;
}

function historyCard(item) {
  return `<div class="insight-card"><strong>${item.focus_theme}</strong><p>${item.recommended_session_minutes} minutes</p><p>${item.steps.join(" | ")}</p></div>`;
}

function childCard(item) {
  return `<div class="guidance-card"><strong>${item.name}</strong><p>${item.email}</p><p>${item.weekly_summary.headline}</p><p>${item.weekly_summary.recommendation}</p></div>`;
}

function fillProfile(profile) {
  document.getElementById("profileFirstName").value = profile.first_name || "";
  document.getElementById("profileLastName").value = profile.last_name || "";
  document.getElementById("profileEmail").value = profile.email || "";
  document.getElementById("profileCountry").value = profile.country || "";
  document.getElementById("profileLanguage").value = profile.lang || "en";
  document.getElementById("profileAudience").value = profile.audience || "student";
  document.getElementById("profileMode").value = profile.mode || "user";
  document.getElementById("profileAge").value = profile.age || "";
  document.getElementById("profileScheduleType").value = profile.schedule_type || "";
  document.getElementById("profileSleepTarget").value = profile.sleep_target_hours || 8;
  document.getElementById("profileMoodBaseline").value = profile.mood_baseline || "";
  document.getElementById("profileEnergyBaseline").value = profile.energy_baseline || "";
  document.getElementById("profileGoals").value = (profile.goals || []).join("\n");
  document.getElementById("profileTriggers").value = (profile.distraction_triggers || []).join("\n");
  document.getElementById("profilePermissions").checked = String(profile.permissions) === "true";
}

function fillSettings(settings) {
  document.getElementById("appNameInput").value = settings.app_name || "Bboo";
  document.getElementById("studyStartInput").value = settings.study_start_time || "16:00";
  document.getElementById("studyEndInput").value = settings.study_end_time || "20:00";
  document.getElementById("sleepTargetInput").value = settings.sleep_target_hours || 8;
  document.getElementById("focusMinutesInput").value = settings.focus_session_minutes || 30;
  document.getElementById("shortBreakInput").value = settings.short_break_minutes || 5;
  document.getElementById("longBreakInput").value = settings.long_break_minutes || 15;
}

async function loadAll() {
  const [profileRes, settingsRes, dashboard, plan, weeklyRes, suggestionsRes, historyRes, timersRes, checkinsRes, childrenRes] = await Promise.all([
    apiRequest("/api/profile"),
    apiRequest("/api/settings"),
    apiRequest(`/api/dashboard?lang=${session.lang || "en"}&mode=${session.mode || "user"}`),
    apiRequest(`/api/plan?lang=${session.lang || "en"}&mode=${session.mode || "user"}`),
    apiRequest("/api/weekly-summary"),
    apiRequest("/api/suggestions"),
    apiRequest("/api/plan-history"),
    apiRequest("/api/timers"),
    apiRequest("/api/checkins"),
    apiRequest("/api/children"),
  ]);

  fillProfile(profileRes.profile);
  fillSettings(settingsRes.settings);
  session.app_name = settingsRes.settings.app_name;
  localStorage.setItem(sessionKey, JSON.stringify(session));

  els.topbarName.textContent = settingsRes.settings.app_name;
  els.topbarSubtitle.textContent = `${session.first_name || profileRes.profile.first_name}'s recovery dashboard`;
  document.title = `${settingsRes.settings.app_name} | Dashboard`;
  document.body.dataset.mode = profileRes.profile.mode || "user";

  els.headline.textContent = dashboard.headline;
  els.focusScore.textContent = dashboard.focus_score;
  els.stateBadge.textContent = dashboard.current_state;
  els.metrics.innerHTML = dashboard.metrics.map(metricCard).join("");
  els.charts.innerHTML = dashboard.charts.map(chartCard).join("");
  els.habits.innerHTML = dashboard.habits.map(habitCard).join("");
  els.insights.innerHTML = dashboard.insights.map(insightCard).join("");
  els.plan.innerHTML = planCard(plan);
  els.weeklySummary.innerHTML = summaryCard(weeklyRes.summary);
  els.suggestions.innerHTML = suggestionCards(suggestionsRes);
  els.planHistory.innerHTML = listCards(historyRes.items, historyCard, "No saved plan history yet.");
  els.timers.innerHTML = listCards(timersRes.items, timerCard, "No timer sessions yet.");
  els.checkins.innerHTML = listCards(checkinsRes.items, checkinCard, "No daily check-ins yet.");
  els.children.innerHTML = listCards(childrenRes.items, childCard, "No linked children yet.");

  if (dashboard.parent_guidance) {
    els.guardianSection.classList.remove("hidden");
    els.parentGuidance.className = "stack";
    els.parentGuidance.innerHTML = `<div class="guidance-card"><p>${dashboard.parent_guidance.summary}</p><ul>${dashboard.parent_guidance.recommended_actions.map((step) => `<li>${step}</li>`).join("")}</ul></div>`;
  } else {
    els.guardianSection.classList.add("hidden");
  }

  attachPlanSave(plan);
}

function attachPlanSave(plan) {
  const button = document.getElementById("savePlanEdits");
  if (!button) return;
  button.addEventListener("click", async () => {
    try {
      const body = await apiRequest("/api/plan", {
        method: "PUT",
        headers: authHeaders(),
        body: JSON.stringify({
          title: plan.title,
          recommended_session_minutes: Number(document.getElementById("planMinutesInput").value),
          focus_theme: document.getElementById("planThemeInput").value.trim(),
          steps: document.getElementById("planStepsInput").value,
          attention_game: plan.attention_game,
        }),
      });
      setMessage(els.settingsMessage, body.message);
      await loadAll();
    } catch (error) {
      setMessage(els.settingsMessage, error.message, true);
    }
  });
}

document.getElementById("saveSettings").addEventListener("click", async () => {
  try {
    const body = await apiRequest("/api/settings", {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify({
        app_name: document.getElementById("appNameInput").value.trim(),
        study_start_time: document.getElementById("studyStartInput").value.trim(),
        study_end_time: document.getElementById("studyEndInput").value.trim(),
        sleep_target_hours: Number(document.getElementById("sleepTargetInput").value),
        focus_session_minutes: Number(document.getElementById("focusMinutesInput").value),
        short_break_minutes: Number(document.getElementById("shortBreakInput").value),
        long_break_minutes: Number(document.getElementById("longBreakInput").value),
      }),
    });
    setMessage(els.settingsMessage, `${body.settings.app_name} settings saved.`);
    await loadAll();
  } catch (error) {
    setMessage(els.settingsMessage, error.message, true);
  }
});

document.getElementById("saveProfile").addEventListener("click", async () => {
  try {
    const body = await apiRequest("/api/profile", {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify({
        first_name: document.getElementById("profileFirstName").value.trim(),
        last_name: document.getElementById("profileLastName").value.trim(),
        country: document.getElementById("profileCountry").value.trim(),
        lang: document.getElementById("profileLanguage").value,
        audience: document.getElementById("profileAudience").value,
        mode: document.getElementById("profileMode").value,
        permissions: String(document.getElementById("profilePermissions").checked),
        age: document.getElementById("profileAge").value,
        schedule_type: document.getElementById("profileScheduleType").value.trim(),
        goals: document.getElementById("profileGoals").value,
        distraction_triggers: document.getElementById("profileTriggers").value,
        sleep_target_hours: Number(document.getElementById("profileSleepTarget").value),
        mood_baseline: document.getElementById("profileMoodBaseline").value.trim(),
        energy_baseline: document.getElementById("profileEnergyBaseline").value.trim(),
      }),
    });
    Object.assign(session, body.session);
    localStorage.setItem(sessionKey, JSON.stringify(session));
    setMessage(els.profileMessage, "Profile updated.");
    await loadAll();
  } catch (error) {
    setMessage(els.profileMessage, error.message, true);
  }
});

document.getElementById("startTimer").addEventListener("click", async () => {
  try {
    const body = await apiRequest("/api/focus-timer/start", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        label: document.getElementById("timerLabel").value.trim(),
        planned_minutes: Number(document.getElementById("timerPlannedMinutes").value),
      }),
    });
    document.getElementById("timerId").value = body.timer_id;
    setMessage(els.timerMessage, body.message);
    await loadAll();
  } catch (error) {
    setMessage(els.timerMessage, error.message, true);
  }
});

document.getElementById("completeTimer").addEventListener("click", async () => {
  try {
    const body = await apiRequest("/api/focus-timer/complete", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        timer_id: Number(document.getElementById("timerId").value),
        actual_minutes: Number(document.getElementById("timerActualMinutes").value),
        completed: true,
      }),
    });
    setMessage(els.timerMessage, body.message);
    await loadAll();
  } catch (error) {
    setMessage(els.timerMessage, error.message, true);
  }
});

document.getElementById("saveCheckin").addEventListener("click", async () => {
  try {
    const body = await apiRequest("/api/checkins", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        mood: document.getElementById("checkinMood").value.trim(),
        energy: document.getElementById("checkinEnergy").value.trim(),
        focus_feeling: Number(document.getElementById("checkinFocusFeeling").value),
        notes: document.getElementById("checkinNotes").value.trim(),
      }),
    });
    setMessage(els.checkinMessage, body.message);
    await loadAll();
  } catch (error) {
    setMessage(els.checkinMessage, error.message, true);
  }
});

document.getElementById("linkChild").addEventListener("click", async () => {
  try {
    const body = await apiRequest("/api/guardian-link", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ child_email: document.getElementById("childEmail").value.trim() }),
    });
    setMessage(els.childrenMessage, body.message);
    await loadAll();
  } catch (error) {
    setMessage(els.childrenMessage, error.message, true);
  }
});

document.getElementById("logoutAllDevices").addEventListener("click", async () => {
  try {
    const body = await apiRequest("/api/logout-all-devices", {
      method: "POST",
      headers: authHeaders(),
    });
    setMessage(els.settingsMessage, body.message);
  } catch (error) {
    setMessage(els.settingsMessage, error.message, true);
  }
});

document.getElementById("backToAuth").addEventListener("click", async () => {
  try {
    await apiRequest("/api/logout", { method: "POST" });
  } catch {
    // Ignore logout failures.
  }
  localStorage.removeItem(sessionKey);
  window.location.href = "/";
});

loadAll().catch((error) => setMessage(els.settingsMessage, error.message, true));
