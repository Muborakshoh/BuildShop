/* ═══════════════════════════════════════════════════════════════
   CMS Admin Panel — NoCode/LowCode Builder
   ═══════════════════════════════════════════════════════════════ */

const cmsContent = document.getElementById("cms-content");
const modalRoot = document.getElementById("modal-root");
let currentSection = "pages";
let quillInstances = {};

function tr(key) {
  return typeof t === "function" ? t(key) : key;
}

// ── Section switching ─────────────────────────────────────────

function switchSection(section, btn) {
  currentSection = section;
  document.querySelectorAll(".cms-nav-item").forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");
  loadSection(section);
}

function loadSection(section) {
  switch (section) {
    case "pages": loadPages(); break;
    case "news": loadNews(); break;
    case "menus": loadMenus(); break;
    case "settings": loadSettings(); break;
  }
}

// ── PAGES ─────────────────────────────────────────────────────

async function loadPages() {
  try {
    const pages = await API.request("/api/cms/pages");
    if (!pages.length) {
      cmsContent.innerHTML = `
        <div class="cms-header"><h2>${tr("cms_pages")}</h2>
          <button class="btn btn-primary" onclick="showPageEditor()">+ ${tr("cms_new_page")}</button>
        </div>
        <div class="cms-empty">
          <p style="font-size:40px">📄</p>
          <p>${tr("cms_no_pages")}</p>
          <p>${tr("cms_no_pages_hint")}</p>
          <button class="btn btn-primary" onclick="showPageEditor()">${tr("cms_new_page")}</button>
        </div>`;
      return;
    }
    cmsContent.innerHTML = `
      <div class="cms-header"><h2>${tr("cms_pages")} (${pages.length})</h2>
        <button class="btn btn-primary" onclick="showPageEditor()">+ ${tr("cms_new_page")}</button>
      </div>
      <div class="cms-cards">${pages.map(p => `
        <div class="cms-card" onclick="editPage(${p.id})">
          <h3>${esc(p.title)}</h3>
          <p>/${esc(p.slug)}</p>
          <div class="card-meta">
            <span class="status-${p.status}">${statusLabel(p.status)}</span>
            ${p.show_in_nav ? `<span class="badge badge--blue">${tr("cms_menus")}</span>` : ''}
            <span class="badge">${p.blocks_count || 0} ${tr("cms_blocks")}</span>
          </div>
          <div class="cms-card-actions">
            ${p.status === "published" ? `<button class="btn btn-outline btn-sm" onclick="event.stopPropagation(); window.open('/pages/page.html?slug=${encodeURIComponent(p.slug)}','_blank')">${tr("cms_preview")}</button>` : ""}
          </div>
        </div>`).join("")}
      </div>`;
  } catch (e) { cmsContent.innerHTML = `<p class="muted">${e.message}</p>`; }
}

function statusLabel(s) {
  return { draft: tr("cms_status_draft"), published: tr("cms_status_published"), archived: tr("cms_status_archived") }[s] || s;
}

function esc(str) {
  if (!str) return "";
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// ── Page Editor (full page with blocks) ───────────────────────

async function showPageEditor(pageId) {
  let page = null;
  if (pageId) {
    page = await API.request(`/api/cms/pages/${pageId}`);
  }
  const isEdit = !!page;
  const title = page ? page.title : "";
  const slug = page ? page.slug : "";
  const desc = page ? (page.description || "") : "";
  const status = page ? page.status : "draft";
  const showNav = page ? page.show_in_nav : false;
  const metaTitle = page ? (page.meta_title || "") : "";
  const metaDesc = page ? (page.meta_description || "") : "";
  const blocks = page ? (page.blocks || []) : [];

  cmsContent.innerHTML = `
    <div class="cms-header">
      <h2>${isEdit ? tr("edit") + ": " + esc(title) : tr("cms_new_page")}</h2>
      <button class="btn btn-outline" onclick="loadPages()">← ${tr("cms_back")}</button>
    </div>
    <div class="cms-form">
      <div class="tab-bar">
        <button class="tab-btn active" onclick="showTab('content',this)">${tr("cms_page_content")}</button>
        <button class="tab-btn" onclick="showTab('seo',this)">${tr("cms_seo")}</button>
        <button class="tab-btn" onclick="showTab('settings-tab',this)">${tr("cms_page_settings")}</button>
      </div>

      <div id="tab-content">
        <div class="form-group">
          <label>${tr("cms_page_title")}</label>
          <input id="pg-title" value="${esc(title)}" placeholder="Масалан: Дар бораи мо" />
        </div>
        <div class="form-group">
          <label>${tr("cms_page_slug")}</label>
          <input id="pg-slug" value="${esc(slug)}" placeholder="dar-borai-mo (автоматӣ пур мешавад)" />
        </div>
        <div class="form-group">
          <label>${tr("cms_page_desc")}</label>
          <textarea id="pg-desc" rows="2" placeholder="Тавсифи кӯтоҳ">${esc(desc)}</textarea>
        </div>

        <h3 style="margin:24px 0 12px">${tr("cms_blocks")}</h3>
        <div class="block-list" id="blocks-list"></div>
        <div class="add-block-bar">
          <button class="add-block-btn" onclick="addBlock('richtext')">📝 ${tr("cms_block_richtext")}</button>
          <button class="add-block-btn" onclick="addBlock('image')">🖼 ${tr("cms_block_image")}</button>
          <button class="add-block-btn" onclick="addBlock('hero')">🎯 ${tr("cms_block_hero")}</button>
          <button class="add-block-btn" onclick="addBlock('gallery')">📸 ${tr("cms_block_gallery")}</button>
          <button class="add-block-btn" onclick="addBlock('video')">🎬 ${tr("cms_block_video")}</button>
          <button class="add-block-btn" onclick="addBlock('html')">🧩 HTML</button>
          <button class="add-block-btn" onclick="addBlock('products')">🛒 ${tr("cms_block_products")}</button>
          <button class="add-block-btn" onclick="addBlock('categories')">📂 ${tr("cms_block_categories")}</button>
          <button class="add-block-btn" onclick="addBlock('contacts')">📞 ${tr("cms_block_contacts")}</button>
          <button class="add-block-btn" onclick="addBlock('separator')">── ${tr("cms_block_separator")}</button>
        </div>
      </div>

      <div id="tab-seo" style="display:none">
        <div class="form-group">
          <label>Meta Title</label>
          <input id="pg-meta-title" value="${esc(metaTitle)}" placeholder="Сарлавҳа барои Google" />
        </div>
        <div class="form-group">
          <label>${tr("cms_meta_desc")}</label>
          <textarea id="pg-meta-desc" rows="3" placeholder="Тавсиф барои Google">${esc(metaDesc)}</textarea>
        </div>
      </div>

      <div id="tab-settings-tab" style="display:none">
        <div class="form-group">
          <label>${tr("cms_status")}</label>
          <select id="pg-status">
            <option value="draft" ${status==="draft"?"selected":""}>${tr("cms_status_draft")}</option>
            <option value="published" ${status==="published"?"selected":""}>${tr("cms_status_published")}</option>
            <option value="archived" ${status==="archived"?"selected":""}>${tr("cms_status_archived")}</option>
          </select>
        </div>
        <div class="form-group">
          <label><input type="checkbox" id="pg-nav" ${showNav?"checked":""} /> ${tr("cms_show_in_nav")}</label>
        </div>
      </div>

      <div class="form-actions">
        <button class="btn btn-primary" onclick="savePage(${pageId || 'null'})">${isEdit ? tr("save") : tr("cms_create")}</button>
        ${isEdit ? '<button class="btn btn-outline" onclick="window.open(\'/pages/page.html?slug='+encodeURIComponent(slug)+'\',\'_blank\')">'+tr("cms_preview")+'</button>' : ''}
        ${isEdit ? '<button class="btn btn-danger" onclick="deletePage('+pageId+')">'+tr("delete_btn")+'</button>' : ''}
        <button class="btn btn-outline" onclick="loadPages()">${tr("cancel")}</button>
      </div>
    </div>`;

  // Build existing blocks
  window._pageBlocks = blocks.map((b, i) => ({
    id: b.id || null,
    block_type: b.block_type,
    content: b.content || "",
    image_url: b.image_url || "",
    settings_json: b.settings_json || "",
    sort_order: i,
  }));
  renderBlocks();
}

function editPage(id) { showPageEditor(id); }

function showTab(tab, btn) {
  document.querySelectorAll('[id^="tab-"]').forEach(el => el.style.display = "none");
  document.getElementById("tab-" + tab).style.display = "block";
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
}

// ── Block management ──────────────────────────────────────────

window._pageBlocks = [];

function addBlock(type) {
  window._pageBlocks.push({
    id: null,
    block_type: type,
    content: "",
    image_url: "",
    settings_json: "",
    sort_order: window._pageBlocks.length,
  });
  renderBlocks();
}

function removeBlock(idx) {
  window._pageBlocks.splice(idx, 1);
  window._pageBlocks.forEach((b, i) => b.sort_order = i);
  renderBlocks();
}

function moveBlock(idx, dir) {
  const newIdx = idx + dir;
  if (newIdx < 0 || newIdx >= window._pageBlocks.length) return;
  const tmp = window._pageBlocks[idx];
  window._pageBlocks[idx] = window._pageBlocks[newIdx];
  window._pageBlocks[newIdx] = tmp;
  window._pageBlocks.forEach((b, i) => b.sort_order = i);
  renderBlocks();
}

function blockTypeLabel(t) {
  const m = {
    richtext:"📝 " + tr("cms_block_richtext"), image:"🖼 " + tr("cms_block_image"), hero:"🎯 " + tr("cms_block_hero"),
    gallery:"📸 " + tr("cms_block_gallery"), video:"🎬 " + tr("cms_block_video"), html:"🧩 " + tr("cms_block_html"),
    products:"🛒 " + tr("cms_block_products"), categories:"📂 " + tr("cms_block_categories"),
    separator:"── " + tr("cms_block_separator"), contacts:"📞 " + tr("cms_block_contacts"), map:"🗺 Харита",
  };
  return m[t] || t;
}

function renderBlocks() {
  // Save current quill contents before re-render
  saveQuillContents();

  const container = document.getElementById("blocks-list");
  if (!container) return;

  if (!window._pageBlocks.length) {
    container.innerHTML = '<p class="muted" style="text-align:center;padding:30px">Блокҳо нест. Тугмаро зер кунед барои илова кардан.</p>';
    return;
  }

  container.innerHTML = window._pageBlocks.map((b, i) => {
    let editor = "";
    switch (b.block_type) {
      case "richtext":
        editor = `<div id="quill-${i}" class="quill-editor"></div>`;
        break;
      case "image":
        editor = `
          <div class="form-group">
            <label>URL расм</label>
            <input value="${esc(b.image_url)}" onchange="window._pageBlocks[${i}].image_url=this.value" placeholder="https://... ё /uploads/..." />
            <div class="image-upload" onclick="document.getElementById('blk-file-${i}').click()" style="margin-top:8px">
              Расм бор кунед
              <input type="file" id="blk-file-${i}" accept="image/*" style="display:none" onchange="uploadBlockImage(this,${i})" />
            </div>
            ${b.image_url ? '<img src="'+esc(b.image_url)+'" style="max-width:200px;margin-top:8px;border-radius:8px" />' : ''}
          </div>
          <div class="form-group">
            <label>Тавсиф (alt)</label>
            <input value="${esc(b.content)}" onchange="window._pageBlocks[${i}].content=this.value" placeholder="Тавсифи расм" />
          </div>`;
        break;
      case "hero":
        editor = `
          <div class="form-group">
            <label>Сарлавҳа</label>
            <input value="${esc(getJson(b.settings_json,'title',''))}" onchange="setBlockJson(${i},'title',this.value)" />
          </div>
          <div class="form-group">
            <label>Зерсарлавҳа</label>
            <textarea rows="2" onchange="setBlockJson(${i},'subtitle',this.value)">${esc(getJson(b.settings_json,'subtitle',''))}</textarea>
          </div>
          <div class="form-group">
            <label>Тугмаи матн</label>
            <input value="${esc(getJson(b.settings_json,'btn_text',''))}" onchange="setBlockJson(${i},'btn_text',this.value)" placeholder="Бештар хонед" />
          </div>
          <div class="form-group">
            <label>Тугмаи URL</label>
            <input value="${esc(getJson(b.settings_json,'btn_url',''))}" onchange="setBlockJson(${i},'btn_url',this.value)" placeholder="/pages/products.html" />
          </div>
          <div class="form-group">
            <label>Расми пасзамина</label>
            <input value="${esc(b.image_url)}" onchange="window._pageBlocks[${i}].image_url=this.value" placeholder="/img/hero-bg.svg" />
          </div>`;
        break;
      case "video":
        editor = `
          <div class="form-group">
            <label>URL видео (YouTube/Vimeo)</label>
            <input value="${esc(b.content)}" onchange="window._pageBlocks[${i}].content=this.value" placeholder="https://youtube.com/embed/..." />
          </div>`;
        break;
      case "html":
        editor = `
          <div class="form-group">
            <label>HTML код</label>
            <textarea rows="8" style="font-family:monospace;font-size:13px" onchange="window._pageBlocks[${i}].content=this.value">${esc(b.content)}</textarea>
          </div>`;
        break;
      case "products":
        editor = `
          <div class="form-group">
            <label>Шумора (лимит)</label>
            <input type="number" value="${getJson(b.settings_json,'limit','8')}" onchange="setBlockJson(${i},'limit',this.value)" />
          </div>
          <div class="form-group">
            <label>Категория ID (холӣ = ҳама)</label>
            <input value="${getJson(b.settings_json,'category_id','')}" onchange="setBlockJson(${i},'category_id',this.value)" />
          </div>`;
        break;
      case "categories":
        editor = `<p class="muted" style="padding:10px">Ин блок автоматӣ ҳамаи категорияҳоро нишон медиҳад.</p>`;
        break;
      case "contacts":
        editor = `
          <div class="form-group">
            <label>Телефон</label>
            <input value="${getJson(b.settings_json,'phone','')}" onchange="setBlockJson(${i},'phone',this.value)" placeholder="+992 (00) 000-00-00" />
          </div>
          <div class="form-group">
            <label>Email</label>
            <input value="${getJson(b.settings_json,'email','')}" onchange="setBlockJson(${i},'email',this.value)" placeholder="info@example.tj" />
          </div>
          <div class="form-group">
            <label>Суроға</label>
            <input value="${getJson(b.settings_json,'address','')}" onchange="setBlockJson(${i},'address',this.value)" placeholder="ш. Душанбе" />
          </div>`;
        break;
      case "gallery":
        editor = `
          <div class="form-group">
            <label>Расмҳо (ҳар сатр як URL)</label>
            <textarea rows="4" onchange="window._pageBlocks[${i}].content=this.value" placeholder="/uploads/1.jpg&#10;/uploads/2.jpg">${esc(b.content)}</textarea>
          </div>`;
        break;
      case "separator":
        editor = `<hr style="margin:10px 0;border-color:var(--border)" />`;
        break;
      default:
        editor = `<p class="muted">Блоки номаълум: ${b.block_type}</p>`;
    }

    return `
      <div class="block-item" data-idx="${i}">
        <div class="block-header">
          <span>${blockTypeLabel(b.block_type)}</span>
          <div class="block-actions">
            <button class="btn btn-outline btn-sm" onclick="moveBlock(${i},-1)" ${i===0?'disabled':''}>↑</button>
            <button class="btn btn-outline btn-sm" onclick="moveBlock(${i},1)" ${i===window._pageBlocks.length-1?'disabled':''}>↓</button>
            <button class="btn btn-danger btn-sm" onclick="removeBlock(${i})">✕</button>
          </div>
        </div>
        ${editor}
      </div>`;
  }).join("");

  // Init Quill for richtext blocks
  quillInstances = {};
  window._pageBlocks.forEach((b, i) => {
    if (b.block_type === "richtext") {
      const el = document.getElementById("quill-" + i);
      if (el) {
        const q = new Quill(el, {
          theme: "snow",
          modules: {
            toolbar: [
              [{ header: [1,2,3,false] }],
              ["bold","italic","underline","strike"],
              [{ color: [] }, { background: [] }],
              [{ list: "ordered" }, { list: "bullet" }],
              [{ align: [] }],
              ["blockquote","code-block"],
              ["link","image"],
              ["clean"],
            ],
          },
          placeholder: "Матнро ин ҷо нависед...",
        });
        if (b.content) {
          q.root.innerHTML = b.content;
        }
        quillInstances[i] = q;
      }
    }
  });
}

function saveQuillContents() {
  for (const [idx, q] of Object.entries(quillInstances)) {
    if (window._pageBlocks[idx]) {
      window._pageBlocks[idx].content = q.root.innerHTML;
    }
  }
}

function getJson(jsonStr, key, def) {
  try { const o = JSON.parse(jsonStr || "{}"); return o[key] !== undefined ? o[key] : def; }
  catch { return def; }
}

function setBlockJson(idx, key, val) {
  let obj = {};
  try { obj = JSON.parse(window._pageBlocks[idx].settings_json || "{}"); } catch {}
  obj[key] = val;
  window._pageBlocks[idx].settings_json = JSON.stringify(obj);
}

async function uploadBlockImage(input, idx) {
  if (!input.files.length) return;
  const form = new FormData();
  form.append("file", input.files[0]);
  try {
    const res = await fetch("/api/upload-image", {
      method: "POST",
      headers: { Authorization: "Bearer " + API.token },
      body: form,
    });
    const data = await res.json();
    if (data.url) {
      window._pageBlocks[idx].image_url = data.url;
      renderBlocks();
    }
  } catch (e) { showToast(e.message, "error"); }
}

// ── Save / Delete Page ────────────────────────────────────────

async function savePage(pageId) {
  saveQuillContents();
  const title = document.getElementById("pg-title").value.trim();
  if (!title) { showToast("Номи саҳифаро нависед", "error"); return; }

  const payload = {
    title: title,
    slug: document.getElementById("pg-slug").value.trim() || "",
    description: document.getElementById("pg-desc").value.trim() || null,
    status: document.getElementById("pg-status").value,
    show_in_nav: document.getElementById("pg-nav").checked,
    meta_title: document.getElementById("pg-meta-title")?.value.trim() || null,
    meta_description: document.getElementById("pg-meta-desc")?.value.trim() || null,
  };

  try {
    let savedPage;
    if (pageId) {
      savedPage = await API.request(`/api/cms/pages/${pageId}`, {
        method: "PATCH", body: JSON.stringify(payload),
      });
      // Update blocks: delete old, add new
      const existingBlocks = savedPage.blocks || [];
      for (const eb of existingBlocks) {
        await API.request(`/api/cms/blocks/${eb.id}`, { method: "DELETE" });
      }
    } else {
      payload.blocks = window._pageBlocks.map((b, i) => ({
        block_type: b.block_type,
        content: b.content || null,
        image_url: b.image_url || null,
        settings_json: b.settings_json || null,
        sort_order: i,
      }));
      savedPage = await API.request("/api/cms/pages", {
        method: "POST", body: JSON.stringify(payload),
      });
    }

    // If editing, re-add blocks
    if (pageId) {
      for (let i = 0; i < window._pageBlocks.length; i++) {
        const b = window._pageBlocks[i];
        await API.request(`/api/cms/pages/${pageId}/blocks`, {
          method: "POST",
          body: JSON.stringify({
            block_type: b.block_type,
            content: b.content || null,
            image_url: b.image_url || null,
            settings_json: b.settings_json || null,
            sort_order: i,
          }),
        });
      }
    }

    showToast("Саҳифа нигоҳ дошта шуд!");
    loadPages();
  } catch (e) { showToast(e.message, "error"); }
}

async function deletePage(id) {
  if (!confirm("Саҳифаро нест кунем?")) return;
  try {
    await API.request(`/api/cms/pages/${id}`, { method: "DELETE" });
    showToast("Саҳифа нест шуд");
    loadPages();
  } catch (e) { showToast(e.message, "error"); }
}


// ═══════════════════════════════════════════════════════════════
// NEWS
// ═══════════════════════════════════════════════════════════════

async function loadNews() {
  try {
    const news = await API.request("/api/cms/news");
    cmsContent.innerHTML = `
      <div class="cms-header"><h2>${tr("cms_news")} (${news.length})</h2>
        <button class="btn btn-primary" onclick="showNewsEditor()">+ ${tr("cms_new_news")}</button>
      </div>
      ${!news.length ? `
        <div class="cms-empty">
          <p style="font-size:40px">📰</p>
          <p>${tr("cms_no_news")}</p>
          <button class="btn btn-primary" onclick="showNewsEditor()">${tr("cms_new_news")}</button>
        </div>` : `
        <div class="cms-cards">${news.map(n => `
          <div class="cms-card" onclick="editNews(${n.id})">
            ${n.image_url ? '<img src="'+esc(n.image_url)+'" style="width:100%;height:140px;object-fit:cover;border-radius:8px;margin-bottom:10px" />' : ''}
            <h3>${esc(n.title)}</h3>
            <p>${esc(n.summary || "")}</p>
            <div class="card-meta">
              <span class="status-${n.status}">${statusLabel(n.status)}</span>
              ${n.pinned ? '<span class="badge badge--blue">📌 '+tr("cms_pinned")+'</span>' : ''}
              <span class="badge">${new Date(n.created_at).toLocaleDateString("ru")}</span>
            </div>
            <div class="cms-card-actions">
              ${n.status === "published" ? `<button class="btn btn-outline btn-sm" onclick="event.stopPropagation(); window.open('/pages/news.html?slug=${encodeURIComponent(n.slug)}','_blank')">${tr("cms_preview")}</button>` : ""}
            </div>
          </div>`).join("")}
        </div>`}`;
  } catch (e) { cmsContent.innerHTML = `<p class="muted">${e.message}</p>`; }
}

async function showNewsEditor(newsId) {
  let news = null;
  if (newsId) news = await API.request(`/api/cms/news/${newsId}`);
  const isEdit = !!news;

  cmsContent.innerHTML = `
    <div class="cms-header">
      <h2>${isEdit ? tr("edit") + ": " + esc(news.title) : tr("cms_new_news")}</h2>
      <button class="btn btn-outline" onclick="loadNews()">← ${tr("cms_back")}</button>
    </div>
    <div class="cms-form">
      <div class="form-group">
        <label>${tr("cms_hero_title")}</label>
        <input id="nw-title" value="${esc(news?.title||'')}" placeholder="Сарлавҳаи хабар" />
      </div>
      <div class="form-group">
        <label>Slug</label>
        <input id="nw-slug" value="${esc(news?.slug||'')}" placeholder="автоматӣ" />
      </div>
      <div class="form-group">
        <label>${tr("cms_summary")}</label>
        <textarea id="nw-summary" rows="2" placeholder="Хулосаи кӯтоҳ">${esc(news?.summary||'')}</textarea>
      </div>
      <div class="form-group">
        <label>${tr("cms_page_content")}</label>
        <div id="news-editor"></div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>${tr("cms_status")}</label>
          <select id="nw-status">
            <option value="draft" ${news?.status==="draft"?"selected":""}>${tr("cms_status_draft")}</option>
            <option value="published" ${news?.status==="published"?"selected":""}>${tr("cms_status_published")}</option>
            <option value="archived" ${news?.status==="archived"?"selected":""}>${tr("cms_status_archived")}</option>
          </select>
        </div>
        <div class="form-group">
          <label><input type="checkbox" id="nw-pinned" ${news?.pinned?"checked":""} /> ${tr("cms_pinned")}</label>
        </div>
      </div>
      <div class="form-group">
        <label>${tr("cms_block_image")}</label>
        <div class="image-upload" onclick="document.getElementById('nw-file').click()">
          ${news?.image_url ? '<img src="'+esc(news.image_url)+'" style="max-height:120px" />' : 'Расм бор кунед'}
          <input type="file" id="nw-file" accept="image/*" style="display:none" onchange="uploadNewsImage(this)" />
        </div>
        <input id="nw-image" value="${esc(news?.image_url||'')}" placeholder="URL расм" style="margin-top:8px" onchange="this.value" />
      </div>
      <div class="form-actions">
        <button class="btn btn-primary" onclick="saveNews(${newsId||'null'})">${isEdit?tr("save"):tr("cms_create")}</button>
        ${isEdit ? '<button class="btn btn-outline" onclick="window.open(\'/pages/news.html?slug='+encodeURIComponent(news.slug)+'\',\'_blank\')">'+tr("cms_preview")+'</button>' : ''}
        ${isEdit ? '<button class="btn btn-danger" onclick="deleteNews('+newsId+')">'+tr("delete_btn")+'</button>' : ''}
        <button class="btn btn-outline" onclick="loadNews()">${tr("cancel")}</button>
      </div>
    </div>`;

  // Init Quill for news editor
  window._newsQuill = new Quill("#news-editor", {
    theme: "snow",
    modules: {
      toolbar: [
        [{ header: [1,2,3,false] }],
        ["bold","italic","underline","strike"],
        [{ color: [] }, { background: [] }],
        [{ list: "ordered" }, { list: "bullet" }],
        [{ align: [] }],
        ["blockquote","code-block"],
        ["link","image"],
        ["clean"],
      ],
    },
    placeholder: "Матни хабарро ин ҷо нависед...",
  });
  if (news?.content) {
    window._newsQuill.root.innerHTML = news.content;
  }
}

function editNews(id) { showNewsEditor(id); }

let newsImageUrl = "";
async function uploadNewsImage(input) {
  if (!input.files.length) return;
  const form = new FormData();
  form.append("file", input.files[0]);
  try {
    const res = await fetch("/api/upload-image", {
      method: "POST",
      headers: { Authorization: "Bearer " + API.token },
      body: form,
    });
    const data = await res.json();
    if (data.url) {
      newsImageUrl = data.url;
      document.getElementById("nw-image").value = data.url;
      showToast("Расм бор шуд!");
    }
  } catch (e) { showToast(e.message, "error"); }
}

async function saveNews(newsId) {
  const title = document.getElementById("nw-title").value.trim();
  if (!title) { showToast("Сарлавҳаро нависед", "error"); return; }

  const content = window._newsQuill.root.innerHTML;
  if (!content || content === "<p><br></p>") { showToast("Мундариҷаро нависед", "error"); return; }

  const payload = {
    title,
    slug: document.getElementById("nw-slug").value.trim() || "",
    summary: document.getElementById("nw-summary").value.trim() || null,
    content,
    image_url: document.getElementById("nw-image").value.trim() || newsImageUrl || null,
    status: document.getElementById("nw-status").value,
    pinned: document.getElementById("nw-pinned").checked,
  };

  try {
    if (newsId) {
      await API.request(`/api/cms/news/${newsId}`, { method: "PATCH", body: JSON.stringify(payload) });
    } else {
      await API.request("/api/cms/news", { method: "POST", body: JSON.stringify(payload) });
    }
    showToast("Хабар нигоҳ дошта шуд!");
    newsImageUrl = "";
    loadNews();
  } catch (e) { showToast(e.message, "error"); }
}

async function deleteNews(id) {
  if (!confirm("Хабарро нест кунем?")) return;
  try {
    await API.request(`/api/cms/news/${id}`, { method: "DELETE" });
    showToast("Хабар нест шуд");
    loadNews();
  } catch (e) { showToast(e.message, "error"); }
}


// ═══════════════════════════════════════════════════════════════
// MENUS
// ═══════════════════════════════════════════════════════════════

async function loadMenus() {
  try {
    const items = await API.request("/api/cms/menus");
    cmsContent.innerHTML = `
      <div class="cms-header"><h2>${tr("cms_menus")}</h2>
        <button class="btn btn-primary" onclick="showMenuForm()">+ ${tr("cms_new_menu")}</button>
      </div>
      ${!items.length ? `
        <div class="cms-empty">
          <p style="font-size:40px">🔗</p>
          <p>${tr("cms_no_menus")}</p>
          <button class="btn btn-primary" onclick="showMenuForm()">${tr("cms_new_menu")}</button>
        </div>` : `
        <table class="data-table" style="width:100%">
          <thead><tr>
            <th>${tr("cms_label")}</th><th>URL</th><th>${tr("cms_location")}</th><th>${tr("cms_sort_order")}</th><th>${tr("cms_active")}</th><th></th>
          </tr></thead>
          <tbody>${items.map(m => `
            <tr>
              <td><strong>${esc(m.label)}</strong>${m.icon ? ' '+m.icon : ''}</td>
              <td><code>${esc(m.url)}</code></td>
              <td><span class="badge">${m.location}</span></td>
              <td>${m.sort_order}</td>
              <td>${m.is_active ? '✅' : '❌'}</td>
              <td class="actions-cell">
                <button class="btn btn-outline btn-sm" onclick="showMenuForm(${m.id})">${tr("edit")}</button>
                <button class="btn btn-danger btn-sm" onclick="deleteMenu(${m.id})">✕</button>
              </td>
            </tr>`).join("")}
          </tbody>
        </table>`}`;
  } catch (e) { cmsContent.innerHTML = `<p class="muted">${e.message}</p>`; }
}

async function showMenuForm(itemId) {
  let item = null;
  if (itemId) {
    const all = await API.request("/api/cms/menus");
    item = all.find(m => m.id === itemId);
  }
  showModal(`
    <h2>${item ? tr("edit") : tr("cms_new_menu")}</h2>
    <div class="form-group">
      <label>${tr("cms_label")}</label>
      <input id="mn-label" value="${esc(item?.label||'')}" placeholder="Асосӣ" />
    </div>
    <div class="form-group">
      <label>URL</label>
      <input id="mn-url" value="${esc(item?.url||'')}" placeholder="/" />
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>${tr("cms_location")}</label>
        <select id="mn-loc">
          <option value="header" ${item?.location==='header'?'selected':''}>Header</option>
          <option value="footer" ${item?.location==='footer'?'selected':''}>Footer</option>
          <option value="sidebar" ${item?.location==='sidebar'?'selected':''}>Sidebar</option>
        </select>
      </div>
      <div class="form-group">
        <label>${tr("cms_sort_order")}</label>
        <input id="mn-order" type="number" value="${item?.sort_order||0}" />
      </div>
    </div>
    <div class="form-group">
      <label><input type="checkbox" id="mn-active" ${item?.is_active!==false?'checked':''} /> ${tr("cms_active")}</label>
    </div>
    <div class="form-group">
      <label><input type="checkbox" id="mn-newtab" ${item?.open_new_tab?'checked':''} /> ${tr("cms_open_new_tab")}</label>
    </div>
    <div class="modal-actions">
      <button class="btn btn-outline" onclick="closeModal()">${tr("cancel")}</button>
      <button class="btn btn-primary" onclick="saveMenu(${itemId||'null'})">${tr("save")}</button>
    </div>
  `);
}

async function saveMenu(itemId) {
  const label = document.getElementById("mn-label").value.trim();
  const url = document.getElementById("mn-url").value.trim();
  if (!label || !url) { showToast(tr("cms_name_url_required"), "error"); return; }

  const payload = {
    label, url,
    location: document.getElementById("mn-loc").value,
    sort_order: parseInt(document.getElementById("mn-order").value) || 0,
    is_active: document.getElementById("mn-active").checked,
    open_new_tab: document.getElementById("mn-newtab").checked,
  };

  try {
    if (itemId) {
      await API.request(`/api/cms/menus/${itemId}`, { method: "PATCH", body: JSON.stringify(payload) });
    } else {
      await API.request("/api/cms/menus", { method: "POST", body: JSON.stringify(payload) });
    }
    closeModal();
    showToast(tr("cms_menu_saved"));
    loadMenus();
  } catch (e) { showToast(e.message, "error"); }
}

async function deleteMenu(id) {
  if (!confirm(tr("cms_confirm_delete_menu"))) return;
  try {
    await API.request(`/api/cms/menus/${id}`, { method: "DELETE" });
    showToast(tr("cms_deleted"));
    loadMenus();
  } catch (e) { showToast(e.message, "error"); }
}


// ═══════════════════════════════════════════════════════════════
// SETTINGS
// ═══════════════════════════════════════════════════════════════

async function loadSettings() {
  try {
    const settings = await API.request("/api/cms/settings");
    cmsContent.innerHTML = `
      <div class="cms-header"><h2>${tr("cms_settings")}</h2>
        <button class="btn btn-primary" onclick="showSettingForm()">+ ${tr("cms_new_setting")}</button>
      </div>
      <div class="identity-note"><strong>${tr("cms_unique")}</strong><br>${tr("cms_unique_hint")}</div>
      ${!settings.length ? `
        <div class="cms-empty">
          <p style="font-size:40px">⚙️</p>
          <p>${tr("cms_no_settings")}</p>
          <p>${tr("cms_no_settings_hint")}</p>
          <button class="btn btn-primary" onclick="addDefaultSettings()">${tr("cms_add_defaults")}</button>
        </div>` : `
        <table class="data-table" style="width:100%">
          <thead><tr>
            <th>${tr("cms_key")}</th><th>${tr("cms_label")}</th><th>${tr("cms_value")}</th><th>${tr("cms_group")}</th><th></th>
          </tr></thead>
          <tbody>${settings.map(s => `
            <tr>
              <td><code>${esc(s.key)}</code></td>
              <td>${esc(s.label || '-')}</td>
              <td style="max-width:250px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(s.value || '-')}</td>
              <td><span class="badge">${esc(s.group_name)}</span></td>
              <td class="actions-cell">
                <button class="btn btn-outline btn-sm" onclick='showSettingForm(${JSON.stringify(s).replace(/'/g,"\\'")})'>${tr("edit")}</button>
                <button class="btn btn-danger btn-sm" onclick="deleteSetting('${esc(s.key)}')">✕</button>
              </td>
            </tr>`).join("")}
          </tbody>
        </table>`}`;
  } catch (e) { cmsContent.innerHTML = `<p class="muted">${e.message}</p>`; }
}

function showSettingForm(existing) {
  const s = existing || {};
  showModal(`
    <h2>${s.key ? tr("edit") : tr("cms_new_setting")}</h2>
    <div class="form-group">
      <label>${tr("cms_key")}</label>
      <input id="st-key" value="${esc(s.key||'')}" placeholder="site_name" ${s.key?'readonly':''} />
    </div>
    <div class="form-group">
      <label>${tr("cms_label")}</label>
      <input id="st-label" value="${esc(s.label||'')}" placeholder="Номи сайт" />
    </div>
    <div class="form-group">
      <label>${tr("cms_value")}</label>
      <textarea id="st-value" rows="3">${esc(s.value||'')}</textarea>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>${tr("cms_type")}</label>
        <select id="st-type">
          <option value="text" ${s.value_type==='text'?'selected':''}>Матн</option>
          <option value="html" ${s.value_type==='html'?'selected':''}>HTML</option>
          <option value="boolean" ${s.value_type==='boolean'?'selected':''}>Boolean</option>
          <option value="number" ${s.value_type==='number'?'selected':''}>Рақам</option>
          <option value="json" ${s.value_type==='json'?'selected':''}>JSON</option>
        </select>
      </div>
      <div class="form-group">
        <label>${tr("cms_group")}</label>
        <input id="st-group" value="${esc(s.group_name||'general')}" />
      </div>
    </div>
    <div class="modal-actions">
      <button class="btn btn-outline" onclick="closeModal()">${tr("cancel")}</button>
      <button class="btn btn-primary" onclick="saveSetting()">${tr("save")}</button>
    </div>
  `);
}

async function saveSetting() {
  const key = document.getElementById("st-key").value.trim();
  if (!key) { showToast(tr("cms_enter_key"), "error"); return; }

  try {
    await API.request("/api/cms/settings", {
      method: "POST",
      body: JSON.stringify({
        key,
        value: document.getElementById("st-value").value,
        value_type: document.getElementById("st-type").value,
        label: document.getElementById("st-label").value.trim() || null,
        group_name: document.getElementById("st-group").value.trim() || "general",
      }),
    });
    closeModal();
    showToast(tr("cms_setting_saved"));
    loadSettings();
  } catch (e) { showToast(e.message, "error"); }
}

async function deleteSetting(key) {
  if (!confirm(tr("cms_confirm_delete_setting"))) return;
  try {
    await API.request(`/api/cms/settings/${key}`, { method: "DELETE" });
    showToast(tr("cms_deleted"));
    loadSettings();
  } catch (e) { showToast(e.message, "error"); }
}

async function addDefaultSettings() {
  const defaults = [
    { key: "site_name", value: "СохтМатериал", label: "Номи сайт", group_name: "general" },
    { key: "site_description", value: "Маводҳои сохтмонии боифтихор", label: "Тавсифи сайт", group_name: "general" },
    { key: "site_phone", value: "+992 (00) 000-00-00", label: "Телефон", group_name: "contacts" },
    { key: "site_email", value: "info@sokhtmaterial.tj", label: "Email", group_name: "contacts" },
    { key: "site_address", value: "ш. Душанбе, к. Сомонӣ 1", label: "Суроға", group_name: "contacts" },
    { key: "work_hours_weekday", value: "Душ – Шан: 08:00 – 18:00", label: "Вақти корӣ (ҳафта)", group_name: "contacts" },
    { key: "work_hours_weekend", value: "Якшанбе: 09:00 – 15:00", label: "Вақти корӣ (якшанбе)", group_name: "contacts" },
    { key: "store_badge", value: "Local Pro Store", label: "Store identity badge", group_name: "identity" },
    { key: "store_promise_title", value: "Магазин барои сохтмони воқеӣ", label: "Store promise title", group_name: "identity" },
    { key: "store_promise_text", value: "Каталог, касса, CMS ва идоракунии анбор дар як системаи маҳаллӣ барои мағозаи сохтмонӣ.", label: "Store promise text", group_name: "identity" },
    { key: "store_point_1_title", value: "Анбор + касса", label: "Identity point 1 title", group_name: "identity" },
    { key: "store_point_1_text", value: "Фурӯш ва фармоишҳо бо бақияи маҳсулот пайваст мешаванд.", label: "Identity point 1 text", group_name: "identity" },
    { key: "store_point_2_title", value: "CMS-и дохилӣ", label: "Identity point 2 title", group_name: "identity" },
    { key: "store_point_2_text", value: "Саҳифа, хабар, меню ва SEO бе платформаи беруна идора мешаванд.", label: "Identity point 2 text", group_name: "identity" },
    { key: "store_point_3_title", value: "3 забон", label: "Identity point 3 title", group_name: "identity" },
    { key: "store_point_3_text", value: "Интерфейс барои тоҷикӣ, русӣ ва англисӣ омода шудааст.", label: "Identity point 3 text", group_name: "identity" },
  ];
  try {
    await API.request("/api/cms/settings/bulk", {
      method: "POST", body: JSON.stringify({ settings: defaults }),
    });
    showToast(tr("cms_default_settings_saved"));
    loadSettings();
  } catch (e) { showToast(e.message, "error"); }
}


// ── Modal helpers ─────────────────────────────────────────────

function showModal(html) {
  modalRoot.innerHTML = `<div class="modal-overlay" onclick="if(event.target===this)closeModal()"><div class="modal">${html}</div></div>`;
}
function closeModal() { modalRoot.innerHTML = ""; }


// ── Burger menu ───────────────────────────────────────────────

function toggleMenu() {
  document.getElementById("main-nav").classList.toggle("open");
  document.getElementById("burger").classList.toggle("open");
  document.getElementById("mobile-overlay").classList.toggle("open");
}


// ── Init ──────────────────────────────────────────────────────

loadPages();
