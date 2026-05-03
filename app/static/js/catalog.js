const productsNode = document.getElementById("products");
const categoryNode = document.getElementById("category");
const searchNode = document.getElementById("search");
const stockNode = document.getElementById("in-stock");

const urlParams = new URLSearchParams(window.location.search);
const preCategory = urlParams.get("category");

// Skeleton loading
function showSkeletons(count = 8) {
  productsNode.innerHTML = Array(count).fill(0).map(() =>
    '<div class="skeleton skeleton-card"></div>'
  ).join("");
}

async function loadCategories() {
  const categories = await API.request("/api/categories");
  categoryNode.innerHTML = '<option value="">' + t("all_categories") + '</option>';
  categories.forEach((c) => {
    const opt = document.createElement("option");
    opt.value = c.id;
    opt.textContent = c.name;
    if (preCategory && String(c.id) === preCategory) opt.selected = true;
    categoryNode.appendChild(opt);
  });
}

function renderProducts(products) {
  if (!products.length) {
    productsNode.innerHTML = `<div class="empty-state" style="grid-column:1/-1">
      <h3>${t("products_not_found")}</h3>
    </div>`;
    return;
  }
  productsNode.innerHTML = products.map((p) => `
    <div class="product-card slide-up">
      <a href="/pages/product.html?id=${p.id}">
        <img src="${p.image_url || '/img/placeholder.svg'}" alt="${p.name}" loading="lazy" />
      </a>
      <div class="product-card-body">
        <span class="product-meta">${p.category.name}</span>
        <h3>${p.name}</h3>
        <div class="product-price">${money(p.price)}</div>
        ${p.volume ? '<span class="product-unit">' + p.volume + ' ' + (p.unit || '') + '</span>' : ''}
        <span class="product-meta">${t("stock_left")}: ${p.stock_quantity}</span>
        <button class="btn btn-primary btn-sm" data-id="${p.id}">${t("add_to_cart")}</button>
      </div>
    </div>
  `).join("");

  productsNode.querySelectorAll("button[data-id]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const p = products.find((x) => x.id === Number(btn.dataset.id));
      addToCart(p);
    });
  });
}

async function loadProducts() {
  showSkeletons();
  const params = new URLSearchParams();
  if (searchNode.value) params.set("search", searchNode.value);
  if (categoryNode.value) params.set("category_id", categoryNode.value);
  if (stockNode.checked) params.set("in_stock", "true");
  try {
    const products = await API.request(`/api/products?${params.toString()}`);
    renderProducts(products);
  } catch (e) {
    productsNode.innerHTML = `<p class="muted text-center" style="grid-column:1/-1">${e.message}</p>`;
  }
}

// Debounce for live search
let searchTimeout;
searchNode.addEventListener("input", () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(loadProducts, 400);
});
categoryNode.addEventListener("change", loadProducts);
stockNode.addEventListener("change", loadProducts);
document.getElementById("search-btn").addEventListener("click", loadProducts);
searchNode.addEventListener("keydown", (e) => { if (e.key === "Enter") loadProducts(); });

loadCategories().then(loadProducts).catch((e) => {
  productsNode.innerHTML = `<p class="muted">${e.message}</p>`;
});
