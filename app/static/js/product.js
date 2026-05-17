const container = document.getElementById("product-detail");
const id = new URLSearchParams(window.location.search).get("id");

async function loadProduct() {
  if (!id) { container.innerHTML = '<p class="muted">Product ID not specified</p>'; return; }
  try {
    const p = await API.request(`/api/products/${id}`);
    document.title = `${p.name} — СохтМатериал`;
    container.innerHTML = `
      <img src="${escapeHtml(safeUrl(p.image_url))}" alt="${escapeHtml(p.name)}" />
      <div class="product-detail-info">
        <span class="badge badge--blue">${escapeHtml(p.category.name)}</span>
        <h1>${escapeHtml(p.name)}</h1>
        <div class="product-price">${money(p.price)}</div>
        ${p.volume ? `<span class="product-unit">${escapeHtml(p.volume)} ${escapeHtml(p.unit || '')}</span>` : ''}
        <p class="product-desc">${escapeHtml(p.description)}</p>
        <span class="product-meta">${t("stock_left")}: ${p.stock_quantity}</span>
        <div class="quantity-control">
          <button onclick="changeQty(-1)">−</button>
          <span id="qty">1</span>
          <button onclick="changeQty(1)">+</button>
        </div>
        <button class="btn btn-gradient btn-lg" onclick="addProductToCart()">${t("add_to_cart")}</button>
      </div>
    `;
    container.classList.add("fade-in");
    window._product = p;
  } catch (e) {
    container.innerHTML = `<p class="muted">${escapeHtml(e.message)}</p>`;
  }
}

let qty = 1;
function changeQty(delta) {
  qty = Math.max(1, qty + delta);
  const el = document.getElementById("qty");
  if (el) el.textContent = qty;
}

function addProductToCart() {
  if (window._product) {
    addToCart(window._product, qty);
  }
}

loadProduct();
