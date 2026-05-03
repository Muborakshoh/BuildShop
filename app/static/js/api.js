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
  toast.innerHTML = `<span>${type === "success" ? "&#10003;" : type === "error" ? "&#10007;" : "&#9432;"}</span> ${message}`;
  container.appendChild(toast);
  setTimeout(() => { toast.remove(); }, 3000);
}

renderCartCount();
syncAuthLink();
