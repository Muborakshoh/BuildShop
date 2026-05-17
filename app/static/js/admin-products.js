const productsBody = document.getElementById("products-body");
const messageNode = document.getElementById("message");
const modalRoot = document.getElementById("modal-root");
let allCategories = [];
let uploadedImageUrl = "";

async function loadCategories() {
  allCategories = await API.request("/api/categories");
}

async function loadProducts() {
  try {
    const products = await API.request("/api/products?limit=200");
    if (!products.length) {
      productsBody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:40px;color:var(--muted)">Нет товаров</td></tr>';
      return;
    }
    productsBody.innerHTML = products.map((p) => `
      <tr>
        <td><img src="${escapeHtml(safeUrl(p.image_url))}" style="width:50px;height:38px;object-fit:cover;border-radius:6px;background:var(--bg);" /></td>
        <td><strong>${escapeHtml(p.name)}</strong></td>
        <td><span class="badge badge--blue">${escapeHtml(p.category.name)}</span></td>
        <td class="price" style="font-size:16px;">${money(p.price)}</td>
        <td>${p.stock_quantity}</td>
        <td class="actions-cell">
          <button class="btn btn-outline btn-sm" onclick="editProduct(${p.id})">${t("edit")}</button>
          <button class="btn btn-danger btn-sm" onclick="deleteProduct(${p.id})">${t("delete_btn")}</button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    messageNode.textContent = e.message;
  }
}

function showModal(html) {
  modalRoot.innerHTML = `<div class="modal-overlay" onclick="if(event.target===this)closeModal()"><div class="modal">${html}</div></div>`;
}
function closeModal() { modalRoot.innerHTML = ""; uploadedImageUrl = ""; }

function categoryOptions(selectedId) {
  return allCategories.map((c) => `<option value="${c.id}" ${c.id===selectedId?"selected":""}>${escapeHtml(c.name)}</option>`).join("");
}

function unitOptions(selected) {
  const units = ["шт","кг","м","л","м²","м³","упак","рулон"];
  return units.map(u => `<option value="${u}" ${u===selected?"selected":""}>${u}</option>`).join("");
}

document.getElementById("add-product-btn").addEventListener("click", () => {
  if (!allCategories.length) {
    showToast("Аввал категория илова кунед!", "error");
    return;
  }
  uploadedImageUrl = "";
  showModal(`
    <h2>${t("add_product")}</h2>
    <input id="m-name" placeholder="${t("product_name")}" />
    <textarea id="m-desc" rows="3" placeholder="${t("product_description")}"></textarea>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
      <input id="m-price" type="number" step="0.01" min="0.01" placeholder="${t("product_price")}" />
      <select id="m-unit">${unitOptions("шт")}</select>
    </div>
    <input id="m-volume" placeholder="Объём/вес (напр. 50кг)" />
    <select id="m-category">${categoryOptions()}</select>
    <input id="m-stock" type="number" min="0" value="0" placeholder="${t("product_stock")}" />
    <div class="image-upload" id="m-image-upload" onclick="document.getElementById('m-file').click()">
      ${t("upload_image")}
      <input type="file" id="m-file" accept="image/*" style="display:none" onchange="uploadImage(this)" />
      <div id="m-preview"></div>
    </div>
    <div class="modal-actions">
      <button class="btn btn-outline" onclick="closeModal()">${t("cancel")}</button>
      <button class="btn btn-primary" onclick="createProduct()">${t("save")}</button>
    </div>
  `);
});

document.getElementById("add-category-btn").addEventListener("click", () => {
  showModal(`
    <h2>${t("add_category")}</h2>
    <input id="m-cat-name" placeholder="${t("category_name")}" />
    <textarea id="m-cat-desc" rows="2" placeholder="${t("category_description")}"></textarea>
    <div class="image-upload" onclick="document.getElementById('m-cat-file').click()">
      ${t("upload_image")}
      <input type="file" id="m-cat-file" accept="image/*" style="display:none" onchange="uploadCatImage(this)" />
      <div id="m-cat-preview"></div>
    </div>
    <div class="modal-actions">
      <button class="btn btn-outline" onclick="closeModal()">${t("cancel")}</button>
      <button class="btn btn-primary" onclick="createCategory()">${t("save")}</button>
    </div>
  `);
});

let catImageUrl = "";
async function uploadCatImage(input) {
  if (!input.files.length) return;
  const form = new FormData();
  form.append("file", input.files[0]);
  try {
    const res = await fetch("/api/upload-image", {
      method: "POST",
      headers: { Authorization: `Bearer ${API.token}` },
      body: form,
    });
    const data = await res.json();
    if (data.url) {
      catImageUrl = data.url;
      document.getElementById("m-cat-preview").innerHTML = `<img src="${escapeHtml(safeUrl(data.url))}" />`;
    }
  } catch (e) { showToast(e.message, "error"); }
}

async function uploadImage(input) {
  if (!input.files.length) return;
  const form = new FormData();
  form.append("file", input.files[0]);
  try {
    const res = await fetch("/api/upload-image", {
      method: "POST",
      headers: { Authorization: `Bearer ${API.token}` },
      body: form,
    });
    const data = await res.json();
    if (data.url) {
      uploadedImageUrl = data.url;
      document.getElementById("m-preview").innerHTML = `<img src="${escapeHtml(safeUrl(data.url))}" />`;
    }
  } catch (e) { showToast(e.message, "error"); }
}

async function createProduct() {
  const name = document.getElementById("m-name").value.trim();
  const price = parseFloat(document.getElementById("m-price").value);
  const catId = parseInt(document.getElementById("m-category").value);

  if (!name) { showToast("Номи молро нависед", "error"); return; }
  if (!price || price <= 0) { showToast("Нархро нависед", "error"); return; }
  if (!catId) { showToast("Категорияро интихоб кунед", "error"); return; }

  try {
    await API.request("/api/products", {
      method: "POST",
      body: JSON.stringify({
        name: name,
        description: document.getElementById("m-desc").value.trim() || name,
        price: price,
        category_id: catId,
        initial_stock: parseInt(document.getElementById("m-stock").value) || 0,
        image_url: uploadedImageUrl || null,
        unit: document.getElementById("m-unit").value || "шт",
        volume: document.getElementById("m-volume").value.trim() || null,
      }),
    });
    closeModal();
    showToast(t("product_saved"));
    notifyAction(t("add_product"), t("product_saved"));
    loadProducts();
  } catch (e) { showToast(e.message, "error"); }
}

async function createCategory() {
  const name = document.getElementById("m-cat-name").value.trim();
  if (!name) { showToast("Номи категорияро нависед", "error"); return; }

  try {
    await API.request("/api/categories", {
      method: "POST",
      body: JSON.stringify({
        name: name,
        description: document.getElementById("m-cat-desc").value.trim() || null,
        image_url: catImageUrl || null,
      }),
    });
    closeModal();
    catImageUrl = "";
    showToast(t("category_saved"));
    notifyAction(t("add_category"), t("category_saved"));
    await loadCategories();
    loadProducts();
  } catch (e) { showToast(e.message, "error"); }
}

async function editProduct(id) {
  try {
    const p = await API.request(`/api/products/${id}`);
    uploadedImageUrl = p.image_url || "";
    showModal(`
      <h2>${t("edit")} — ${escapeHtml(p.name)}</h2>
      <input id="m-name" value="${escapeHtml(p.name)}" placeholder="${t("product_name")}" />
      <textarea id="m-desc" rows="3" placeholder="${t("product_description")}">${escapeHtml(p.description)}</textarea>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
        <input id="m-price" type="number" step="0.01" value="${p.price}" placeholder="${t("product_price")}" />
        <select id="m-unit">${unitOptions(p.unit)}</select>
      </div>
      <input id="m-volume" value="${escapeHtml(p.volume || '')}" placeholder="Объём/вес" />
      <select id="m-category">${categoryOptions(p.category_id)}</select>
      <div class="image-upload" onclick="document.getElementById('m-file').click()">
        ${p.image_url ? `<img src="${escapeHtml(safeUrl(p.image_url))}" />` : t("upload_image")}
        <input type="file" id="m-file" accept="image/*" style="display:none" onchange="uploadImage(this)" />
        <div id="m-preview"></div>
      </div>
      <div class="modal-actions">
        <button class="btn btn-outline" onclick="closeModal()">${t("cancel")}</button>
        <button class="btn btn-primary" onclick="updateProduct(${id})">${t("save")}</button>
      </div>
    `);
  } catch (e) { showToast(e.message, "error"); }
}

async function updateProduct(id) {
  try {
    await API.request(`/api/products/${id}`, {
      method: "PATCH",
      body: JSON.stringify({
        name: document.getElementById("m-name").value.trim(),
        description: document.getElementById("m-desc").value.trim(),
        price: parseFloat(document.getElementById("m-price").value),
        category_id: parseInt(document.getElementById("m-category").value),
        image_url: uploadedImageUrl || null,
        unit: document.getElementById("m-unit").value,
        volume: document.getElementById("m-volume").value.trim() || null,
      }),
    });
    closeModal();
    showToast(t("product_saved"));
    notifyAction(t("edit"), t("product_saved"));
    loadProducts();
  } catch (e) { showToast(e.message, "error"); }
}

async function deleteProduct(id) {
  if (!confirm(t("confirm_delete"))) return;
  try {
    await API.request(`/api/products/${id}`, { method: "DELETE" });
    showToast(t("product_deleted"));
    notifyAction(t("delete_btn"), t("product_deleted"));
    loadProducts();
  } catch (e) { showToast(e.message, "error"); }
}

loadCategories().then(loadProducts);
