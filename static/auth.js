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
  },
  ar: {
    eyebrow: "استعادة تركيز كهربائية",
    title: "يبدأ Bboo بحسابك أولا ثم يفتح عالم التركيز في الصفحة التالية.",
    subtitle: "أدخل بياناتك المهمة أولا ثم أنشئ الحساب أو سجّل الدخول. بعد ذلك ينقلك Bboo إلى صفحة لوحة منفصلة فيها الرسوم والعادات والإرشاد.",
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

authEls.createTab.addEventListener("click", () => setTab("create"));
authEls.loginTab.addEventListener("click", () => setTab("login"));
authEls.createLanguage.addEventListener("change", () => applyAuthI18n(authEls.createLanguage.value));
authEls.loginLanguage.addEventListener("change", () => applyAuthI18n(authEls.loginLanguage.value));

document.getElementById("createForm").addEventListener("submit", (event) => {
  event.preventDefault();
  saveSession({
    first_name: document.getElementById("createFirstName").value.trim(),
    last_name: document.getElementById("createLastName").value.trim(),
    email: document.getElementById("createEmail").value.trim(),
    country: document.getElementById("createCountry").value.trim(),
    lang: document.getElementById("createLanguage").value,
    audience: document.getElementById("createAudience").value,
    mode: document.getElementById("createMode").value,
    permissions: String(document.getElementById("createPermissions").checked),
  });
});

document.getElementById("loginForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const language = document.getElementById("loginLanguage").value;
  saveSession({
    first_name: "Lina",
    last_name: "Hassan",
    email: document.getElementById("loginEmail").value.trim(),
    country: "Egypt",
    lang: language,
    audience: "student",
    mode: "user",
    permissions: "true",
  });
});

setTab("create");
