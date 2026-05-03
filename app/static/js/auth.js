let isLogin = true;

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
      <input id="a-password" type="password" placeholder="Пароль" />
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
      <input id="a-password" type="password" placeholder="Пароль" />
      <input id="a-password2" type="password" placeholder="Пароли такрорӣ" />
    `;
    btn.textContent = t("register");
    link.textContent = t("login");
    document.querySelector(".switch-mode span").textContent = t("have_account");
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
      if (password !== password2) { msg.textContent = "Паролҳо мувофиқ нестанд"; return; }
      const response = await API.request("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ full_name: name, email, password }),
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
