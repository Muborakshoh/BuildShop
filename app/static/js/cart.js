function renderCart() {
  const cart = getCart();
  const listNode = document.getElementById("cart-list");
  const summaryNode = document.getElementById("cart-summary");
  const totalNode = document.getElementById("cart-total");

  if (!cart.length) {
    listNode.innerHTML = `<div class="empty-state">
      <h3>${t("cart_empty")}</h3>
      <a href="/pages/products.html" class="btn btn-primary" style="margin-top:16px">${t("nav_products")}</a>
    </div>`;
    summaryNode.style.display = "none";
    return;
  }

  listNode.innerHTML = cart.map((item, i) => `
    <div class="cart-item slide-up">
      <img src="${item.image_url || '/img/placeholder.svg'}" alt="${item.name}" />
      <div class="cart-item-info">
        <h3>${item.name}</h3>
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
  totalNode.textContent = money(total);
  summaryNode.style.display = "flex";
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

async function checkout() {
  const cart = getCart();
  if (!cart.length) return;
  if (!API.token) {
    showToast(t("login"), "error");
    window.location.href = "/pages/auth.html";
    return;
  }
  try {
    await API.request("/api/orders", {
      method: "POST",
      body: JSON.stringify({ items: cart.map(item => ({ product_id: item.product_id, quantity: item.quantity })) }),
    });
    setCart([]);
    renderCart();
    showToast(t("order_success"));
  } catch (e) {
    showToast(e.message, "error");
  }
}

renderCart();
