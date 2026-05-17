let isLogin = true;

function passwordField(id, placeholder) {
  return `
    <div class="password-field">
      <input id="${id}" type="password" placeholder="${placeholder}" />
      <button type="button" class="password-toggle" onclick="togglePassword('${id}', this)" data-state="hidden">${t("show_password")}</button>
    </div>
  `;
}

function togglePassword(inputId, button) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const isHidden = input.type === "password";
  input.type = isHidden ? "text" : "password";
  button.dataset.state = isHidden ? "visible" : "hidden";
  button.textContent = isHidden ? t("hide_password") : t("show_password");
}

function switchMode(e) {
  e.preventDefault();
  isLogin = !isLogin;
  const title = document.getElementById("auth-title");
  const subtitle = document.getElementById("auth-subtitle");
  const fields = document.getElementById("auth-fields");
  const btn = document.getElementById("auth-btn");
  const link = document.getElementById("switch-link");
  const msg = document.getElementById("auth-message");
  msg.textContent = "";

  if (isLogin) {
    title.textContent = t("login");
    subtitle.textContent = t("login_subtitle");
    fields.innerHTML = `
      <input id="a-email" type="email" placeholder="Email" />
      ${passwordField("a-password", t("password"))}
    `;
    btn.textContent = t("login");
    link.textContent = t("register");
    document.querySelector(".switch-mode span").textContent = t("no_account");
  } else {
    title.textContent = t("register");
    subtitle.textContent = t("register_subtitle");
    fields.innerHTML = `
      <input id="a-name" placeholder="${t("user_name")}" />
      <input id="a-email" type="email" placeholder="Email" />
      <div style="display:flex;gap:8px">
        <input id="a-code" placeholder="${t("verification_code")}" />
        <button type="button" class="btn btn-outline btn-sm" onclick="requestRegisterCode()">${t("request_code")}</button>
      </div>
      ${passwordField("a-password", t("password"))}
      ${passwordField("a-password2", t("password_repeat"))}
    `;
    btn.textContent = t("register");
    link.textContent = t("login");
    document.querySelector(".switch-mode span").textContent = t("have_account");
  }
}

async function requestRegisterCode() {
  const msg = document.getElementById("auth-message");
  msg.textContent = "";
  const email = document.getElementById("a-email")?.value.trim();
  if (!email) { msg.textContent = t("email_required"); return; }
  try {
    await API.request("/api/auth/register/request-code", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
    msg.textContent = t("code_sent");
    msg.style.color = "var(--green)";
    showToast(t("code_sent"));
  } catch (error) {
    msg.textContent = error.message;
    msg.style.color = "var(--red)";
  }
}

async function doAuth() {
  const msg = document.getElementById("auth-message");
  msg.textContent = "";
  const email = document.getElementById("a-email").value;
  const password = document.getElementById("a-password").value;

  if (!email || !password) { msg.textContent = "Ҳамаи майдонҳоро пур кунед"; return; }

  try {
    if (isLogin) {
      const tokens = await API.request("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      API.setTokens(tokens);
      window.location.href = "/";
    } else {
      const name = document.getElementById("a-name").value;
      const password2 = document.getElementById("a-password2").value;
      const verificationCode = document.getElementById("a-code").value.trim();
      if (password !== password2) { msg.textContent = "Паролҳо мувофиқ нестанд"; return; }
      if (!verificationCode) { msg.textContent = t("verification_code_required"); return; }
      const response = await API.request("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ full_name: name, email, password, verification_code: verificationCode }),
      });
      API.setTokens(response.tokens || response);
      window.location.href = "/";
    }
  } catch (error) {
    msg.textContent = error.message;
    msg.style.color = "var(--red)";
  }
}

// Allow Enter key
document.getElementById("auth-fields").addEventListener("keydown", (e) => {
  if (e.key === "Enter") doAuth();
});

// If already logged in, redirect
if (API.token) { window.location.href = "/"; }
