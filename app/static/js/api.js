const API = {
  token: localStorage.getItem("access_token"),
  currentUser: null,

  async request(path, options = {}, allowRefresh = true) {
    const headers = options.body instanceof FormData
      ? { ...(options.headers || {}) }
      : { "Content-Type": "application/json", ...(options.headers || {}) };
    if (this.token) headers.Authorization = `Bearer ${this.token}`;
    const response = await fetch(path, { ...options, headers });
    if (response.status === 401 && allowRefresh && path !== "/api/auth/refresh") {
      const refreshed = await this.refreshTokens();
      if (refreshed) return this.request(path, options, false);
      this.logout();
      if (!window.location.pathname.includes("auth.html")) {
        window.location.href = "/pages/auth.html";
      }
      throw new Error(typeof t === "function" ? t("session_expired") : "Session expired");
    }
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }));
      const detail = error.detail;
      const message = Array.isArray(detail)
        ? detail.map((item) => item.msg || item.message || JSON.stringify(item)).join(", ")
        : detail || "Request failed";
      throw new Error(message);
    }
    if (response.status === 204) return null;
    return response.json();
  },

  async refreshTokens() {
    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) return false;
    try {
      const response = await fetch("/api/auth/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!response.ok) return false;
      const tokens = await response.json();
      this.setTokens(tokens);
      return true;
    } catch {
      return false;
    }
  },

  setTokens(tokens) {
    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);
    this.token = tokens.access_token;
  },

  logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    this.token = null;
    this.currentUser = null;
  },

  async loadCurrentUser() {
    if (!this.token) return null;
    try {
      this.currentUser = await this.request("/api/users/me");
      return this.currentUser;
    } catch {
      this.currentUser = null;
      return null;
    }
  },

  async ensureRole(roles, redirectTo = "/pages/auth.html") {
    if (!this.token) {
      window.location.href = redirectTo;
      return null;
    }
    const user = await this.loadCurrentUser();
    const allowed = Array.isArray(roles) ? roles : [roles];
    if (!user || !allowed.includes(user.role)) {
      showToast(typeof t === "function" ? t("access_denied") : "Access denied", "error");
      setTimeout(() => { window.location.href = redirectTo; }, 500);
      return null;
    }
    return user;
  },
};

// ── Currency formatter (TJS — Somoni)
function money(value) {
  return Number(value).toLocaleString("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " сом.";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function safeUrl(value, fallback = "/img/placeholder.svg") {
  const url = String(value || "").trim();
  if (!url) return fallback;
  if (url.startsWith("/") || url.startsWith("http://") || url.startsWith("https://")) return url;
  return fallback;
}


// ── Multilingual helper — reads translations JSON from item
function ml(item, field) {
  if (!item) return "";
  const lang = (typeof currentLang !== "undefined") ? currentLang : (localStorage.getItem("lang") || "tj");
  if (lang === "tj") return item[field] || "";
  if (item.translations) {
    try {
      const tr = typeof item.translations === "string" ? JSON.parse(item.translations) : item.translations;
      const key = field + "_" + lang;
      if (tr[key]) return tr[key];
    } catch {}
  }
  return item[field] || "";
}

function buildTranslations(fields, prefix) {
  const tr = {};
  let hasAny = false;
  for (const field of fields) {
    for (const lang of ["ru", "en"]) {
      const el = document.getElementById(prefix + "-" + field + "-" + lang);
      if (el && el.value.trim()) {
        tr[field + "_" + lang] = el.value.trim();
        hasAny = true;
      }
    }
  }
  return hasAny ? JSON.stringify(tr) : null;
}

function parseTr(translationsStr, field, lang) {
  if (!translationsStr) return "";
  try {
    const tr = typeof translationsStr === "string" ? JSON.parse(translationsStr) : translationsStr;
    return tr[field + "_" + lang] || "";
  } catch { return ""; }
}

window.ml = ml;
window.buildTranslations = buildTranslations;
window.parseTr = parseTr;

window.escapeHtml = escapeHtml;
window.safeUrl = safeUrl;

// ── Cart helpers
function getCart() {
  return JSON.parse(localStorage.getItem("cart") || "[]");
}
function setCart(cart) {
  localStorage.setItem("cart", JSON.stringify(cart));
  renderCartCount();
}
function addToCart(product, quantity = 1) {
  const cart = getCart();
  const existing = cart.find((item) => item.product_id === (product.product_id || product.id));
  if (existing) {
    existing.quantity += quantity;
  } else {
    cart.push({
      product_id: product.product_id || product.id,
      name: ml(product, "name") || product.name,
      price: product.price,
      image_url: product.image_url || "",
      quantity,
    });
  }
  setCart(cart);
  showToast(t("added_to_cart"));
}
function renderCartCount() {
  const count = getCart().reduce((sum, item) => sum + item.quantity, 0);
  document.querySelectorAll("#cart-count").forEach((node) => {
    node.textContent = String(count);
    node.style.display = count > 0 ? "" : "none";
  });
}

// ── Auth link sync
async function syncAuthLink() {
  const link = document.getElementById("auth-link");
  const ordersLink = document.getElementById("my-orders-link");
  if (!link) return;
  if (API.token) {
    const user = await API.loadCurrentUser();
    if (user) {
      link.textContent = user.full_name || t("logout");
      link.href = "#";
      link.onclick = (e) => { e.preventDefault(); API.logout(); window.location.href = "/"; };
      if (ordersLink) ordersLink.style.display = "";
      if (user.role === "admin" || user.role === "manager") {
        document.querySelectorAll(".admin-only").forEach((el) => (el.style.display = ""));
      }
    } else {
      API.logout();
    }
  } else {
    document.querySelectorAll(".admin-only").forEach((el) => (el.style.display = "none"));
    if (ordersLink) ordersLink.style.display = "none";
  }
}

// ── Toast notification system
function showToast(message, type = "success") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.className = "toast-container";
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = "toast " + type;
  const icon = document.createElement("span");
  icon.textContent = type === "success" ? "✓" : type === "error" ? "✗" : "ⓘ";
  toast.appendChild(icon);
  toast.appendChild(document.createTextNode(" " + String(message || "")));
  container.appendChild(toast);
  setTimeout(() => { toast.remove(); }, 3000);
}

function notifyAction(title, message, type = "success") {
  showToast(`${title}: ${message}`, type);
}

async function openContactModal() {
  let email = "info@sokhtmaterial.tj";
  try {
    const settings = await API.request("/api/cms/settings/public?group=contacts");
    const values = Object.fromEntries(settings.map((s) => [s.key, s.value]));
    email = values.site_email || email;
  } catch {}

  let root = document.getElementById("contact-modal-root");
  if (!root) {
    root = document.createElement("div");
    root.id = "contact-modal-root";
    document.body.appendChild(root);
  }
  root.innerHTML = `
    <div class="modal-overlay" onclick="if(event.target===this)closeContactModal()">
      <div class="modal">
        <h2>${escapeHtml(t("contact_title"))}</h2>
        <p class="muted">${escapeHtml(t("contact_hint"))}</p>
        <input id="contact-email" type="email" placeholder="${escapeHtml(t("email"))}" />
        <input id="contact-subject" placeholder="${escapeHtml(t("contact_subject"))}" />
        <textarea id="contact-message" rows="6" placeholder="${escapeHtml(t("contact_message"))}"></textarea>
        <div class="modal-actions">
          <button class="btn btn-outline" onclick="closeContactModal()">${escapeHtml(t("cancel"))}</button>
          <button class="btn btn-primary" onclick="sendContactMessage()">${escapeHtml(t("send"))}</button>
        </div>
      </div>
    </div>
  `;
}

function closeContactModal() {
  const root = document.getElementById("contact-modal-root");
  if (root) root.innerHTML = "";
}

async function sendContactMessage() {
  const from = document.getElementById("contact-email")?.value.trim() || "";
  const subject = document.getElementById("contact-subject")?.value.trim() || t("contact_subject_default");
  const message = document.getElementById("contact-message")?.value.trim() || "";
  if (!from || !message) {
    showToast(t("contact_fill_required"), "error");
    return;
  }
  try {
    await API.request("/api/cms/contact", {
      method: "POST",
      body: JSON.stringify({ email: from, subject, message }),
    });
    closeContactModal();
    showToast(t("contact_sent"));
  } catch (e) {
    showToast(e.message, "error");
  }
}

window.notifyAction = notifyAction;
window.openContactModal = openContactModal;
window.closeContactModal = closeContactModal;
window.sendContactMessage = sendContactMessage;

function renderCurrentYear() {
  document.querySelectorAll("[data-current-year]").forEach((node) => {
    node.textContent = String(new Date().getFullYear());
  });
}

function setSeoMeta({ title, description, ogImage, canonicalUrl, robotsIndex } = {}) {
  if (title) document.title = title;
  const setMeta = (name, content, attr = "name") => {
    if (!content) return;
    let node = document.querySelector(`meta[${attr}="${name}"]`);
    if (!node) {
      node = document.createElement("meta");
      node.setAttribute(attr, name);
      document.head.appendChild(node);
    }
    node.setAttribute("content", content);
  };
  setMeta("description", description);
  setMeta("og:title", title, "property");
  setMeta("og:description", description, "property");
  setMeta("og:image", ogImage, "property");
  setMeta("robots", robotsIndex === false ? "noindex,nofollow" : "index,follow");
  if (canonicalUrl) {
    let link = document.querySelector('link[rel="canonical"]');
    if (!link) {
      link = document.createElement("link");
      link.setAttribute("rel", "canonical");
      document.head.appendChild(link);
    }
    link.setAttribute("href", canonicalUrl);
  }
}

function trackPageView(extra = {}) {
  API.request("/api/cms/analytics/track", {
    method: "POST",
    body: JSON.stringify({ path: location.pathname + location.search, ...extra }),
  }).catch(() => {});
}

renderCartCount();
syncAuthLink();
renderCurrentYear();
trackPageView();
