function renderCart() {
  const cart = getCart();
  const listNode = document.getElementById("cart-list");
  const summaryNode = document.getElementById("cart-summary");
  const checkoutNode = document.getElementById("checkout-form");
  const totalNode = document.getElementById("cart-total");

  if (!cart.length) {
    listNode.innerHTML = `<div class="empty-state">
      <h3>${t("cart_empty")}</h3>
      <a href="/pages/products.html" class="btn btn-primary" style="margin-top:16px">${t("nav_products")}</a>
    </div>`;
    summaryNode.style.display = "none";
    if (checkoutNode) checkoutNode.style.display = "none";
    return;
  }

  listNode.innerHTML = cart.map((item, i) => `
    <div class="cart-item slide-up">
      <img src="${escapeHtml(safeUrl(item.image_url))}" alt="${escapeHtml(item.name)}" />
      <div class="cart-item-info">
        <h3>${escapeHtml(item.name)}</h3>
        <p>${money(item.price)} x ${item.quantity}</p>
      </div>
      <span class="price">${money(item.price * item.quantity)}</span>
      <div style="display:flex;gap:8px;align-items:center">
        <button class="btn btn-outline btn-sm" onclick="updateQty(${i},-1)">−</button>
        <span style="font-weight:700;min-width:24px;text-align:center">${item.quantity}</span>
        <button class="btn btn-outline btn-sm" onclick="updateQty(${i},1)">+</button>
        <button class="btn btn-danger btn-sm" onclick="removeItem(${i})">✕</button>
      </div>
    </div>
  `).join("");

  const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
  window._cartTotal = total;
  totalNode.textContent = money(window._promoDiscount ? total - window._promoDiscount : total);
  summaryNode.style.display = "flex";
  if (checkoutNode) checkoutNode.style.display = "block";

  // Render promo section
  let promoEl = document.getElementById("promo-section");
  if (!promoEl) {
    promoEl = document.createElement("div");
    promoEl.id = "promo-section";
    promoEl.className = "promo-section";
    summaryNode.parentNode.insertBefore(promoEl, summaryNode);
  }
  if (window._promoApplied) {
    promoEl.innerHTML = '<div class="promo-applied"><span>✓ ' + escapeHtml(window._promoApplied) + ' (' + escapeHtml(window._promoDesc) + ')</span>' +
      '<button class="btn btn-outline btn-sm" onclick="removePromo()">' + escapeHtml(t("promo_remove")) + '</button></div>';
  } else {
    promoEl.innerHTML = '<div class="promo-input-row">' +
      '<input id="promo-code" type="text" placeholder="' + escapeHtml(t("promo_placeholder")) + '" maxlength="50" />' +
      '<button class="btn btn-outline btn-sm" onclick="applyPromo()">' + escapeHtml(t("promo_apply")) + '</button></div>';
  }
}

function updateQty(index, delta) {
  const cart = getCart();
  cart[index].quantity = Math.max(1, cart[index].quantity + delta);
  setCart(cart);
  renderCart();
}

function removeItem(index) {
  const cart = getCart();
  cart.splice(index, 1);
  setCart(cart);
  renderCart();
  showToast(t("product_deleted"), "info");
}

function clearCart() {
  setCart([]);
  renderCart();
  showToast(t("cart_cleared"), "info");
}

function toggleDeliveryFields() {
  const method = document.querySelector('input[name="delivery_method"]:checked')?.value || "pickup";
  const addressField = document.getElementById("checkout-address");
  if (addressField) {
    addressField.disabled = method === "pickup";
    if (method === "pickup") addressField.value = t("delivery_pickup_default");
  }
}

async function checkout() {
  const cart = getCart();
  if (!cart.length) return;
  if (!API.token) {
    showToast(t("login"), "error");
    window.location.href = "/pages/auth.html";
    return;
  }
  const deliveryMethod = document.querySelector('input[name="delivery_method"]:checked')?.value || "pickup";
  const phone = document.getElementById("checkout-phone")?.value.trim() || null;
  const address = document.getElementById("checkout-address")?.value.trim() || t("delivery_pickup_default");
  const comment = document.getElementById("checkout-comment")?.value.trim() || null;
  if (!phone) {
    showToast(t("checkout_phone_required"), "error");
    return;
  }
  try {
    await API.request("/api/orders", {
      method: "POST",
      body: JSON.stringify({
        delivery_method: deliveryMethod,
        delivery_address: address,
        phone,
        comment,
        items: cart.map((item) => ({ product_id: item.product_id, quantity: item.quantity })),
      }),
    });
    setCart([]);
    renderCart();
    showToast(t("order_success"));
    setTimeout(() => { window.location.href = "/pages/orders.html"; }, 800);
  } catch (e) {
    showToast(e.message, "error");
  }
}

// ── Promo codes ──
window._promoApplied = null;
window._promoDiscount = 0;
window._promoDesc = "";

async function applyPromo() {
  const code = document.getElementById("promo-code")?.value.trim();
  if (!code) return;
  if (!API.token) {
    showToast(t("login_to_use_promo"), "error");
    return;
  }
  const total = window._cartTotal || 0;
  if (!total) return;
  try {
    const result = await API.request("/api/promos/apply", {
      method: "POST",
      body: JSON.stringify({ code, order_total: total }),
    });
    window._promoApplied = result.code;
    window._promoDiscount = parseFloat(result.discount);
    window._promoDesc = result.description;
    showToast(t("promo_applied") + " " + result.description);
    renderCart();
  } catch (e) {
    showToast(e.message, "error");
  }
}

function removePromo() {
  window._promoApplied = null;
  window._promoDiscount = 0;
  window._promoDesc = "";
  renderCart();
}

window.applyPromo = applyPromo;
window.removePromo = removePromo;

toggleDeliveryFields();
renderCart();
