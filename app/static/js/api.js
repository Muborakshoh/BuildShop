const API = {
  token: localStorage.getItem("access_token"),
  currentUser: null,

  async request(path, options = {}) {
    const headers = options.body instanceof FormData
      ? { ...(options.headers || {}) }
      : { "Content-Type": "application/json", ...(options.headers || {}) };
    if (this.token) headers.Authorization = `Bearer ${this.token}`;
    const response = await fetch(path, { ...options, headers });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(error.detail || "Request failed");
    }
    if (response.status === 204) return null;
    return response.json();
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
      name: product.name,
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
  if (!link) return;
  if (API.token) {
    const user = await API.loadCurrentUser();
    if (user) {
      link.textContent = user.full_name || t("logout");
      link.href = "#";
      link.onclick = (e) => { e.preventDefault(); API.logout(); window.location.href = "/"; };
      if (user.role === "admin") {
        document.querySelectorAll(".admin-only").forEach((el) => (el.style.display = ""));
      }
    } else {
      API.logout();
    }
  } else {
    document.querySelectorAll(".admin-only").forEach((el) => (el.style.display = "none"));
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
          <button class="btn btn-primary" onclick="sendContactMail('${escapeHtml(email).replace(/'/g, "\\'")}')">${escapeHtml(t("send"))}</button>
        </div>
      </div>
    </div>
  `;
}

function closeContactModal() {
  const root = document.getElementById("contact-modal-root");
  if (root) root.innerHTML = "";
}

function sendContactMail(toEmail) {
  const from = document.getElementById("contact-email")?.value.trim() || "";
  const subject = document.getElementById("contact-subject")?.value.trim() || t("contact_subject_default");
  const message = document.getElementById("contact-message")?.value.trim() || "";
  const body = `${message}\n\n${t("contact_from")}: ${from}`;
  window.location.href = `mailto:${encodeURIComponent(toEmail)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  closeContactModal();
}

window.notifyAction = notifyAction;
window.openContactModal = openContactModal;
window.closeContactModal = closeContactModal;
window.sendContactMail = sendContactMail;

renderCartCount();
syncAuthLink();
