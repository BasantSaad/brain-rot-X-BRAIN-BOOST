const authTranslations = {
  en: {
    eyebrow: "Electric focus recovery",
    title: "Bboo starts with your account, then opens your focus world on the next page.",
    subtitle: "First enter your important data and sign in or log in. After that, Bboo moves you to a dedicated dashboard page with graphs, habits, and guidance.",
    createAccount: "Create account",
    login: "Log in",
    profileTitle: "Create account profile",
    profileSubtitle: "Fill the important data first. Bboo uses it to prepare your next page.",
    loginTitle: "Log in to Bboo",
    loginSubtitle: "Enter your account details, then go to the separate dashboard page.",
    firstName: "First name",
    lastName: "Last name",
    email: "Email",
    password: "Password",
    country: "Country",
    language: "Language",
    audience: "Audience",
    view: "Dashboard",
    permissions: "Device permission",
    continue: "Continue to dashboard",
    enterDashboard: "Enter dashboard",
    processing: "Processing your request...",
    genericError: "We could not complete that request. Please try again.",
    createSuccess: "Account created. Loading your dashboard...",
    loginSuccess: "Login successful. Loading your dashboard...",
  },
  ar: {
    eyebrow: "استعادة تركيز كهربائية",
    title: "يبدأ Bboo بحسابك أولا ثم يفتح عالم التركيز في الصفحة التالية.",
    subtitle: "أدخل بياناتك المهمة أولا ثم أنشئ الحساب أو سجل الدخول. بعد ذلك ينقلك Bboo إلى صفحة لوحة منفصلة فيها الرسوم والعادات والإرشاد.",
    createAccount: "إنشاء حساب",
    login: "تسجيل الدخول",
    profileTitle: "إنشاء ملف الحساب",
    profileSubtitle: "املأ البيانات المهمة أولا. يستخدمها Bboo لتجهيز الصفحة التالية.",
    loginTitle: "الدخول إلى Bboo",
    loginSubtitle: "أدخل بيانات الحساب ثم انتقل إلى صفحة اللوحة المنفصلة.",
    firstName: "الاسم الأول",
    lastName: "اسم العائلة",
    email: "البريد الإلكتروني",
    password: "كلمة المرور",
    country: "الدولة",
    language: "اللغة",
    audience: "الفئة",
    view: "نوع اللوحة",
    permissions: "صلاحية الجهاز",
    continue: "المتابعة إلى اللوحة",
    enterDashboard: "الدخول إلى اللوحة",
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
  createForm: document.getElementById("createForm"),
  loginForm: document.getElementById("loginForm"),
  createLanguage: document.getElementById("createLanguage"),
  loginLanguage: document.getElementById("loginLanguage"),
  authMessage: document.getElementById("authMessage"),
};

function applyAuthI18n(language) {
  document.documentElement.lang = language;
  document.body.dir = language === "ar" ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = authTranslations[language][node.dataset.i18n];
  });
}

function setTab(tab) {
  const createActive = tab === "create";
  authEls.createTab.classList.toggle("is-active", createActive);
  authEls.loginTab.classList.toggle("is-active", !createActive);
  authEls.createForm.classList.toggle("hidden", !createActive);
  authEls.loginForm.classList.toggle("hidden", createActive);
  const language = createActive ? authEls.createLanguage.value : authEls.loginLanguage.value;
  applyAuthI18n(language);
}

function saveSession(data) {
  localStorage.setItem(storageKey, JSON.stringify(data));
  window.location.href = "/dashboard.html";
}

function setMessage(message, isError = false) {
  authEls.authMessage.textContent = message;
  authEls.authMessage.classList.toggle("is-error", isError);
}

async function submitAuth(url, payload) {
  const language = payload.lang || authEls.createLanguage.value || "en";
  setMessage(authTranslations[language].processing);
  let response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
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
  return body.session;
}

authEls.createTab.addEventListener("click", () => setTab("create"));
authEls.loginTab.addEventListener("click", () => setTab("login"));
authEls.createLanguage.addEventListener("change", () => applyAuthI18n(authEls.createLanguage.value));
authEls.loginLanguage.addEventListener("change", () => applyAuthI18n(authEls.loginLanguage.value));

document.getElementById("createForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const language = document.getElementById("createLanguage").value;
  try {
    const session = await submitAuth("/api/register", {
      first_name: document.getElementById("createFirstName").value.trim(),
      last_name: document.getElementById("createLastName").value.trim(),
      email: document.getElementById("createEmail").value.trim(),
      password: document.getElementById("createPassword").value,
      country: document.getElementById("createCountry").value.trim(),
      lang: language,
      audience: document.getElementById("createAudience").value,
      mode: document.getElementById("createMode").value,
      permissions: String(document.getElementById("createPermissions").checked),
    });
    setMessage(authTranslations[language].createSuccess);
    saveSession(session);
  } catch (error) {
    setMessage(error.message, true);
  }
});

document.getElementById("loginForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const language = document.getElementById("loginLanguage").value;
  try {
    const session = await submitAuth("/api/login", {
      email: document.getElementById("loginEmail").value.trim(),
      password: document.getElementById("loginPassword").value,
      lang: language,
    });
    setMessage(authTranslations[language].loginSuccess);
    saveSession(session);
  } catch (error) {
    setMessage(error.message, true);
  }
});

setTab("create");
setMessage("");
