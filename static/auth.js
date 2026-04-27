const authTranslations = {
  en: {
    eyebrow: "Electric focus recovery",
    title: "Bboo now combines real sessions, focus plans, check-ins, and recovery tracking in one place.",
    subtitle: "Create an account or log in to manage your profile, timer, weekly trends, parent links, and personalized suggestions powered by your real stored activity.",
    createAccount: "Create account",
    login: "Log in",
    resetPassword: "Reset password",
    profileTitle: "Create account profile",
    profileSubtitle: "Start with your account details and get a personalized focus system immediately.",
    loginTitle: "Log in to Bboo",
    loginSubtitle: "Open your dashboard with your stored settings, summaries, timer activity, and check-ins.",
    resetTitle: "Reset your password",
    resetSubtitle: "Request a reset code first, then enter it below with your new password.",
    firstName: "First name",
    lastName: "Last name",
    email: "Email",
    password: "Password",
    newPassword: "New password",
    country: "Country",
    language: "Language",
    audience: "Audience",
    view: "Dashboard",
    permissions: "Device permission",
    continue: "Continue to dashboard",
    enterDashboard: "Enter dashboard",
    rememberMe: "Remember me",
    requestCode: "Request reset code",
    resetCode: "Reset code",
    confirmReset: "Confirm password reset",
    processing: "Processing your request...",
    genericError: "We could not complete that request. Please try again.",
    createSuccess: "Account created. Loading your dashboard...",
    loginSuccess: "Login successful. Loading your dashboard...",
  },
  ar: {
    eyebrow: "استعادة تركيز كهربائية",
    title: "يجمع Bboo الآن بين الجلسات الحقيقية والخطط والمتابعة اليومية وتتبع التعافي في مكان واحد.",
    subtitle: "أنشئ حسابا أو سجّل الدخول لإدارة ملفك ومؤقتك واتجاهاتك الأسبوعية وروابط ولي الأمر والاقتراحات المبنية على نشاطك الحقيقي.",
    createAccount: "إنشاء حساب",
    login: "تسجيل الدخول",
    resetPassword: "إعادة التعيين",
    profileTitle: "إنشاء ملف الحساب",
    profileSubtitle: "ابدأ ببيانات حسابك واحصل مباشرة على نظام تركيز شخصي.",
    loginTitle: "الدخول إلى Bboo",
    loginSubtitle: "افتح لوحتك بإعداداتك المحفوظة وملخصاتك ونشاط المؤقت والمتابعة اليومية.",
    resetTitle: "إعادة تعيين كلمة المرور",
    resetSubtitle: "اطلب رمز إعادة التعيين أولا ثم أدخله مع كلمة المرور الجديدة.",
    firstName: "الاسم الأول",
    lastName: "اسم العائلة",
    email: "البريد الإلكتروني",
    password: "كلمة المرور",
    newPassword: "كلمة المرور الجديدة",
    country: "الدولة",
    language: "اللغة",
    audience: "الفئة",
    view: "نوع اللوحة",
    permissions: "صلاحية الجهاز",
    continue: "المتابعة إلى اللوحة",
    enterDashboard: "الدخول إلى اللوحة",
    rememberMe: "تذكرني",
    requestCode: "اطلب رمز التعيين",
    resetCode: "رمز التعيين",
    confirmReset: "تأكيد إعادة التعيين",
    processing: "يجري تنفيذ طلبك...",
    genericError: "لم نتمكن من إكمال الطلب. حاول مرة أخرى.",
    createSuccess: "تم إنشاء الحساب. جاري فتح اللوحة...",
    loginSuccess: "تم تسجيل الدخول. جاري فتح اللوحة...",
  },
};

const storageKey = "bboo-session";
const authEls = {
  createTab: document.getElementById("createTab"),
  loginTab: document.getElementById("loginTab"),
  resetTab: document.getElementById("resetTab"),
  createForm: document.getElementById("createForm"),
  loginForm: document.getElementById("loginForm"),
  resetForm: document.getElementById("resetForm"),
  createLanguage: document.getElementById("createLanguage"),
  loginLanguage: document.getElementById("loginLanguage"),
  authMessage: document.getElementById("authMessage"),
};

function currentLanguage() {
  if (!authEls.loginForm.classList.contains("hidden")) {
    return document.getElementById("loginLanguage").value;
  }
  return document.getElementById("createLanguage").value;
}

function applyAuthI18n(language) {
  document.documentElement.lang = language;
  document.body.dir = language === "ar" ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = authTranslations[language][node.dataset.i18n];
  });
}

function setTab(tab) {
  authEls.createTab.classList.toggle("is-active", tab === "create");
  authEls.loginTab.classList.toggle("is-active", tab === "login");
  authEls.resetTab.classList.toggle("is-active", tab === "reset");
  authEls.createForm.classList.toggle("hidden", tab !== "create");
  authEls.loginForm.classList.toggle("hidden", tab !== "login");
  authEls.resetForm.classList.toggle("hidden", tab !== "reset");
  applyAuthI18n(currentLanguage());
}

function saveSession(data) {
  localStorage.setItem(storageKey, JSON.stringify(data));
  window.location.href = "/dashboard.html";
}

function setMessage(message, isError = false) {
  authEls.authMessage.textContent = message;
  authEls.authMessage.classList.toggle("is-error", isError);
}

async function sendJson(url, payload) {
  const language = payload.lang || currentLanguage() || "en";
  setMessage(authTranslations[language].processing);
  let response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new Error(authTranslations[language].genericError);
  }
  let body = {};
  try {
    body = await response.json();
  } catch {
    body = {};
  }
  if (!response.ok) {
    throw new Error(body.error || authTranslations[language].genericError);
  }
  return body;
}

authEls.createTab.addEventListener("click", () => setTab("create"));
authEls.loginTab.addEventListener("click", () => setTab("login"));
authEls.resetTab.addEventListener("click", () => setTab("reset"));
authEls.createLanguage.addEventListener("change", () => applyAuthI18n(authEls.createLanguage.value));
authEls.loginLanguage.addEventListener("change", () => applyAuthI18n(authEls.loginLanguage.value));

document.getElementById("createForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const language = document.getElementById("createLanguage").value;
  try {
    const body = await sendJson("/api/register", {
      first_name: document.getElementById("createFirstName").value.trim(),
      last_name: document.getElementById("createLastName").value.trim(),
      email: document.getElementById("createEmail").value.trim(),
      password: document.getElementById("createPassword").value,
      country: document.getElementById("createCountry").value.trim(),
      lang: language,
      audience: document.getElementById("createAudience").value,
      mode: document.getElementById("createMode").value,
      permissions: String(document.getElementById("createPermissions").checked),
      remember_me: document.getElementById("createRememberMe").checked,
    });
    setMessage(authTranslations[language].createSuccess);
    saveSession(body.session);
  } catch (error) {
    setMessage(error.message, true);
  }
});

document.getElementById("loginForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const language = document.getElementById("loginLanguage").value;
  try {
    const body = await sendJson("/api/login", {
      email: document.getElementById("loginEmail").value.trim(),
      password: document.getElementById("loginPassword").value,
      lang: language,
      remember_me: document.getElementById("loginRememberMe").checked,
    });
    setMessage(authTranslations[language].loginSuccess);
    saveSession(body.session);
  } catch (error) {
    setMessage(error.message, true);
  }
});

document.getElementById("requestResetCode").addEventListener("click", async () => {
  try {
    const body = await sendJson("/api/password-reset/request", {
      email: document.getElementById("resetEmail").value.trim(),
      lang: currentLanguage(),
    });
    setMessage(`${body.message} Demo code: ${body.reset_code}`);
  } catch (error) {
    setMessage(error.message, true);
  }
});

document.getElementById("resetForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const body = await sendJson("/api/password-reset/confirm", {
      email: document.getElementById("resetEmail").value.trim(),
      reset_code: document.getElementById("resetCode").value.trim(),
      new_password: document.getElementById("resetNewPassword").value,
      lang: currentLanguage(),
    });
    setMessage(body.message);
    setTab("login");
  } catch (error) {
    setMessage(error.message, true);
  }
});

setTab("create");
setMessage("");
