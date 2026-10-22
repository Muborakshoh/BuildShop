const productsBody = document.getElementById("products-body");
const messageNode = document.getElementById("message");
const modalRoot = document.getElementById("modal-root");
let allCategories = [];
let uploadedImageUrl = "";

/* ── Language tabs HTML ──────────────────────────────────────── */
function langTabs(prefix, fields, existing) {
  // fields = [{key:"name",label_key:"product_name",type:"input"}, {key:"desc",label_key:"product_description",type:"textarea"}]
  // existing = product or category object (for editing) or null
  const langs = [
    {code:"tj", label:t("lang_tj"), flag:"🇹🇯"},
    {code:"ru", label:t("lang_ru"), flag:"🇷🇺"},
    {code:"en", label:t("lang_en"), flag:"🇬🇧"},
  ];

  let tabs = '<div class="lang-tabs" style="display:flex;gap:4px;margin-bottom:12px;border-bottom:2px solid var(--border)">';
  langs.forEach((l, i) => {
    tabs += `<button type="button" class="tab-btn ${i===0?'active':''}" onclick="switchLangTab('${prefix}','${l.code}',this)" style="padding:8px 14px;border:none;background:none;cursor:pointer;font-size:13px;color:var(--muted);border-bottom:2px solid transparent;margin-bottom:-2px;transition:all .2s">${l.flag} ${l.label}</button>`;
  });
  tabs += '</div>';

  langs.forEach((l, i) => {
    const display = i === 0 ? 'block' : 'none';
    tabs += `<div id="${prefix}-lang-${l.code}" style="display:${display}">`;
    fields.forEach(f => {
      let val = "";
      if (existing) {
        if (l.code === "tj") {
          val = existing[f.key] || "";
        } else {
          val = parseTr(existing.translations, f.key, l.code);
        }
      }
      const inputId = l.code === "tj" ? `${prefix}-${f.key}` : `${prefix}-${f.key}-${l.code}`;
      const placeholder = t(f.label_key) + " (" + l.label + ")";
      if (f.type === "textarea") {
        tabs += `<textarea id="${inputId}" rows="${f.rows||3}" placeholder="${escapeHtml(placeholder)}">${escapeHtml(val)}</textarea>`;
      } else {
        tabs += `<input id="${inputId}" value="${escapeHtml(val)}" placeholder="${escapeHtml(placeholder)}" />`;
      }
    });
    tabs += '</div>';
  });
  return tabs;
}

function switchLangTab(prefix, lang, btn) {
  // Hide all
  ["tj","ru","en"].forEach(l => {
    const el = document.getElementById(prefix + "-lang-" + l);
    if (el) el.style.display = "none";
  });
  // Show selected
  const el = document.getElementById(prefix + "-lang-" + lang);
  if (el) el.style.display = "block";
  // Active tab
  if (btn && btn.parentElement) {
    btn.parentElement.querySelectorAll(".tab-btn").forEach(b => {
      b.classList.remove("active");
      b.style.color = "var(--muted)";
      b.style.borderBottomColor = "transparent";
    });
    btn.classList.add("active");
    btn.style.color = "var(--primary)";
    btn.style.borderBottomColor = "var(--primary)";
  }
}
window.switchLangTab = switchLangTab;

/* ── Load data ───────────────────────────────────────────────── */
async function loadCategories() {
  allCategories = await API.request("/api/categories");
}

async function loadProducts() {
  try {
    const products = await API.request("/api/products?limit=200");
    if (!products.length) {
      productsBody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:40px;color:var(--muted)">' + t("products_not_found") + '</td></tr>';
      return;
    }
    productsBody.innerHTML = products.map((p) => `
      <tr>
        <td><img src="${escapeHtml(safeUrl(p.image_url))}" style="width:50px;height:38px;object-fit:cover;border-radius:6px;background:var(--bg);" /></td>
        <td><strong>${escapeHtml(ml(p,"name"))}</strong></td>
        <td><span class="badge badge--blue">${escapeHtml(ml(p.category,"name"))}</span></td>
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
  return allCategories.map((c) => `<option value="${c.id}" ${c.id===selectedId?"selected":""}>${escapeHtml(ml(c,"name"))}</option>`).join("");
}

function calcFieldsBlock(existing) {
  const cov = existing?.coverage_per_unit_m2 ?? "";
  const pack = existing?.units_per_pack ?? "";
  const waste = existing?.calc_waste_percent ?? "";
  return `
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px">
      <input id="m-coverage" type="number" step="0.0001" min="0" value="${cov}" placeholder="${t("product_coverage")}" />
      <input id="m-units-pack" type="number" step="1" min="0" value="${pack}" placeholder="${t("product_units_per_pack")}" />
      <input id="m-calc-waste" type="number" step="0.1" min="0" value="${waste}" placeholder="${t("product_calc_waste")}" />
    </div>`;
}

function calcPayloadExtras() {
  const cov = document.getElementById("m-coverage")?.value;
  const pack = document.getElementById("m-units-pack")?.value;
  const waste = document.getElementById("m-calc-waste")?.value;
  return {
    coverage_per_unit_m2: cov ? parseFloat(cov) : null,
    units_per_pack: pack ? parseInt(pack, 10) : null,
    calc_waste_percent: waste ? parseFloat(waste) : null,
  };
}

function unitOptions(selected) {
  const units = ["шт","кг","м","л","м²","м³","упак","рулон"];
  return units.map(u => `<option value="${u}" ${u===selected?"selected":""}>${u}</option>`).join("");
}

/* ── Add Product ─────────────────────────────────────────────── */
document.getElementById("add-product-btn").addEventListener("click", () => {
  if (!allCategories.length) {
    showToast(t("cms_enter_name"), "error");
    return;
  }
  uploadedImageUrl = "";
  const fields = [
    {key:"name", label_key:"product_name", type:"input"},
    {key:"description", label_key:"product_description", type:"textarea", rows:3},
  ];
  showModal(`
    <h2>${t("add_product")}</h2>
    ${langTabs("m", fields, null)}
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
      <input id="m-price" type="number" step="0.01" min="0.01" placeholder="${t("product_price")}" />
      <select id="m-unit">${unitOptions("шт")}</select>
    </div>
    <input id="m-volume" placeholder="${t("unit")} (50кг)" />
    ${calcFieldsBlock(null)}
    <select id="m-category">${categoryOptions()}</select>
    <input id="m-stock" type="number" min="0" value="0" placeholder="${t("product_stock")}" />
    <details style="margin:12px 0">
      <summary>SEO</summary>
      <input id="m-meta-title" placeholder="Meta title" />
      <textarea id="m-meta-description" rows="2" placeholder="Meta description"></textarea>
      <input id="m-og-image" placeholder="Open Graph image URL" />
      <input id="m-canonical" placeholder="Canonical URL" />
      <label style="display:block;margin-top:8px"><input type="checkbox" id="m-robots" checked /> Index in sitemap</label>
    </details>
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

/* ── Add Category ────────────────────────────────────────────── */
document.getElementById("add-category-btn").addEventListener("click", () => {
  const fields = [
    {key:"name", label_key:"category_name", type:"input"},
    {key:"description", label_key:"category_description", type:"textarea", rows:2},
  ];
  showModal(`
    <h2>${t("add_category")}</h2>
    ${langTabs("mc", fields, null)}
    <div class="image-upload" onclick="document.getElementById('mc-file').click()">
      ${t("upload_image")}
      <input type="file" id="mc-file" accept="image/*" style="display:none" onchange="uploadCatImage(this)" />
      <div id="mc-preview"></div>
    </div>
    <div class="modal-actions">
      <button class="btn btn-outline" onclick="closeModal()">${t("cancel")}</button>
      <button class="btn btn-primary" onclick="createCategory()">${t("save")}</button>
    </div>
  `);
});

/* ── Image upload ────────────────────────────────────────────── */
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
      document.getElementById("mc-preview").innerHTML = `<img src="${escapeHtml(safeUrl(data.url))}" />`;
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

/* ── Create Product ──────────────────────────────────────────── */
async function createProduct() {
  const name = document.getElementById("m-name").value.trim();
  const price = parseFloat(document.getElementById("m-price").value);
  const catId = parseInt(document.getElementById("m-category").value);

  if (!name) { showToast(t("cms_enter_name"), "error"); return; }
  if (!price || price <= 0) { showToast(t("product_price"), "error"); return; }
  if (!catId) { showToast(t("product_category"), "error"); return; }

  const translations = buildTranslations(["name","description"], "m");

  try {
    await API.request("/api/products", {
      method: "POST",
      body: JSON.stringify({
        name: name,
        description: document.getElementById("m-description").value.trim() || name,
        price: price,
        category_id: catId,
        initial_stock: parseInt(document.getElementById("m-stock").value) || 0,
        image_url: uploadedImageUrl || null,
        meta_title: document.getElementById("m-meta-title")?.value.trim() || null,
        meta_description: document.getElementById("m-meta-description")?.value.trim() || null,
        og_image: document.getElementById("m-og-image")?.value.trim() || null,
        canonical_url: document.getElementById("m-canonical")?.value.trim() || null,
        robots_index: document.getElementById("m-robots")?.checked !== false,
        unit: document.getElementById("m-unit").value || "шт",
        volume: document.getElementById("m-volume").value.trim() || null,
        ...calcPayloadExtras(),
        translations: translations,
      }),
    });
    closeModal();
    showToast(t("product_saved"));
    loadProducts();
  } catch (e) { showToast(e.message, "error"); }
}

/* ── Create Category ─────────────────────────────────────────── */
async function createCategory() {
  const name = document.getElementById("mc-name").value.trim();
  if (!name) { showToast(t("cms_enter_name"), "error"); return; }

  const translations = buildTranslations(["name","description"], "mc");

  try {
    await API.request("/api/categories", {
      method: "POST",
      body: JSON.stringify({
        name: name,
        description: document.getElementById("mc-description").value.trim() || null,
        image_url: catImageUrl || null,
        translations: translations,
      }),
    });
    closeModal();
    catImageUrl = "";
    showToast(t("category_saved"));
    await loadCategories();
    loadProducts();
  } catch (e) { showToast(e.message, "error"); }
}

/* ── Edit Product ────────────────────────────────────────────── */
async function editProduct(id) {
  try {
    const p = await API.request(`/api/products/${id}`);
    uploadedImageUrl = p.image_url || "";
    const fields = [
      {key:"name", label_key:"product_name", type:"input"},
      {key:"description", label_key:"product_description", type:"textarea", rows:3},
    ];
    showModal(`
      <h2>${t("edit")} — ${escapeHtml(p.name)}</h2>
      ${langTabs("m", fields, p)}
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
        <input id="m-price" type="number" step="0.01" value="${p.price}" placeholder="${t("product_price")}" />
        <select id="m-unit">${unitOptions(p.unit)}</select>
      </div>
      <input id="m-volume" value="${escapeHtml(p.volume || '')}" placeholder="${t("unit")}" />
      ${calcFieldsBlock(p)}
      <select id="m-category">${categoryOptions(p.category_id)}</select>
      <details style="margin:12px 0">
        <summary>SEO</summary>
        <input id="m-meta-title" value="${escapeHtml(p.meta_title || '')}" placeholder="Meta title" />
        <textarea id="m-meta-description" rows="2" placeholder="Meta description">${escapeHtml(p.meta_description || '')}</textarea>
        <input id="m-og-image" value="${escapeHtml(p.og_image || '')}" placeholder="Open Graph image URL" />
        <input id="m-canonical" value="${escapeHtml(p.canonical_url || '')}" placeholder="Canonical URL" />
        <label style="display:block;margin-top:8px"><input type="checkbox" id="m-robots" ${p.robots_index !== false ? "checked" : ""} /> Index in sitemap</label>
      </details>
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

/* ── Update Product ──────────────────────────────────────────── */
async function updateProduct(id) {
  const translations = buildTranslations(["name","description"], "m");
  try {
    await API.request(`/api/products/${id}`, {
      method: "PATCH",
      body: JSON.stringify({
        name: document.getElementById("m-name").value.trim(),
        description: document.getElementById("m-description").value.trim(),
        price: parseFloat(document.getElementById("m-price").value),
        category_id: parseInt(document.getElementById("m-category").value),
        image_url: uploadedImageUrl || null,
        meta_title: document.getElementById("m-meta-title")?.value.trim() || null,
        meta_description: document.getElementById("m-meta-description")?.value.trim() || null,
        og_image: document.getElementById("m-og-image")?.value.trim() || null,
        canonical_url: document.getElementById("m-canonical")?.value.trim() || null,
        robots_index: document.getElementById("m-robots")?.checked !== false,
        unit: document.getElementById("m-unit").value,
        volume: document.getElementById("m-volume").value.trim() || null,
        ...calcPayloadExtras(),
        translations: translations,
      }),
    });
    closeModal();
    showToast(t("product_saved"));
    loadProducts();
  } catch (e) { showToast(e.message, "error"); }
}

/* ── Delete Product ──────────────────────────────────────────── */
async function deleteProduct(id) {
  if (!confirm(t("confirm_delete"))) return;
  try {
    await API.request(`/api/products/${id}`, { method: "DELETE" });
    showToast(t("product_deleted"));
    loadProducts();
  } catch (e) { showToast(e.message, "error"); }
}

loadCategories().then(() => {
  API.ensureRole(["admin", "manager"]).then((user) => {
    if (user) loadProducts();
  });
});
