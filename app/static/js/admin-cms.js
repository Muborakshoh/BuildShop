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

async function ensureCmsAdmin() {
  if (!API.token) {
    window.location.href = "/pages/auth.html";
    return false;
  }
  const user = await API.loadCurrentUser();
  if (!user || user.role !== "admin") {
    showToast(tr("cms_admin_required") || "Admin role required", "error");
    setTimeout(() => { window.location.href = "/pages/auth.html"; }, 500);
    return false;
  }
  return true;
}

/* ── Language tabs for CMS forms ─────────────────────────────── */
function cmsLangTabs(prefix, fields, existing) {
  const langs = [
    {code:"tj", label:t("lang_tj"), flag:"🇹🇯"},
    {code:"ru", label:t("lang_ru"), flag:"🇷🇺"},
    {code:"en", label:t("lang_en"), flag:"🇬🇧"},
  ];
  let html = '<div class="lang-tabs" style="display:flex;gap:4px;margin-bottom:12px;border-bottom:2px solid var(--border)">';
  langs.forEach((l, i) => {
    html += `<button type="button" class="tab-btn ${i===0?'active':''}" onclick="switchLangTab('${prefix}','${l.code}',this)" style="padding:8px 14px;border:none;background:none;cursor:pointer;font-size:13px;color:${i===0?'var(--primary)':'var(--muted)'};border-bottom:2px solid ${i===0?'var(--primary)':'transparent'};margin-bottom:-2px;transition:all .2s;font-weight:${i===0?'600':'400'}">${l.flag} ${l.label}</button>`;
  });
  html += '</div>';
  langs.forEach((l, i) => {
    html += `<div id="${prefix}-lang-${l.code}" style="display:${i===0?'block':'none'}">`;
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
      const ph = (f.placeholder || f.key) + " (" + l.label + ")";
      if (f.type === "textarea") {
        html += `<div class="form-group"><label>${esc(ph)}</label><textarea id="${inputId}" rows="${f.rows||3}" placeholder="${esc(ph)}">${esc(val)}</textarea></div>`;
      } else {
        html += `<div class="form-group"><label>${esc(ph)}</label><input id="${inputId}" value="${esc(val)}" placeholder="${esc(ph)}" /></div>`;
      }
    });
    html += '</div>';
  });
  return html;
}

function cmsBuildTranslations(fields, prefix) {
  const tr = {};
  let hasAny = false;
  for (const f of fields) {
    for (const lang of ["ru", "en"]) {
      const el = document.getElementById(prefix + "-" + f + "-" + lang);
      if (el && el.value.trim()) {
        tr[f + "_" + lang] = el.value.trim();
        hasAny = true;
      }
    }
  }
  return hasAny ? JSON.stringify(tr) : null;
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
    case "media": loadMedia(); break;
    case "import": loadImport(); break;
    case "ai": loadAiTools(); break;
    case "audit": loadAudit(); break;
    case "reports": loadReports(); break;
    case "calculators": loadCalculators(); break;
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
          <h3>${esc(ml(p, "title"))}</h3>
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
  const ogImage = page ? (page.og_image || "") : "";
  const canonicalUrl = page ? (page.canonical_url || "") : "";
  const robotsIndex = page ? page.robots_index !== false : true;
  const blocks = page ? (page.blocks || []) : [];
  const pageTranslationFields = [
    {key:"title", placeholder:tr("cms_page_title"), type:"input"},
    {key:"description", placeholder:tr("cms_page_desc"), type:"textarea", rows:2},
  ];

  cmsContent.innerHTML = `
    <div class="cms-header">
      <h2>${isEdit ? tr("edit") + ": " + esc(ml(page, "title")) : tr("cms_new_page")}</h2>
      <button class="btn btn-outline" onclick="loadPages()">← ${tr("cms_back")}</button>
    </div>
    <div class="cms-form">
      <div class="tab-bar">
        <button class="tab-btn active" onclick="showTab('content',this)">${tr("cms_page_content")}</button>
        <button class="tab-btn" onclick="showTab('seo',this)">${tr("cms_seo")}</button>
        <button class="tab-btn" onclick="showTab('settings-tab',this)">${tr("cms_page_settings")}</button>
      </div>

      <div id="tab-content">
        ${cmsLangTabs("pg", pageTranslationFields, page)}
        <div class="form-group">
          <label>${tr("cms_page_slug")}</label>
          <input id="pg-slug" value="${esc(slug)}" placeholder="dar-borai-mo (автоматӣ пур мешавад)" />
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
        <div class="form-group">
          <label>Open Graph image</label>
          <input id="pg-og-image" value="${esc(ogImage)}" placeholder="/uploads/image.png" />
        </div>
        <div class="form-group">
          <label>Canonical URL</label>
          <input id="pg-canonical" value="${esc(canonicalUrl)}" placeholder="/pages/page.html?slug=${esc(slug)}" />
        </div>
        <div class="form-group">
          <label><input type="checkbox" id="pg-robots" ${robotsIndex ? "checked" : ""} /> Index in sitemap</label>
        </div>
        <div class="identity-note"><strong>SEO preview</strong><br>${esc(metaTitle || title)}<br><span class="muted">${esc(metaDesc || desc || "")}</span></div>
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
        ${isEdit ? '<button class="btn btn-outline" onclick="showPageVersions('+pageId+')">Versions</button>' : ''}
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

  const pgTranslations = cmsBuildTranslations(["title","description"], "pg");
  const payload = {
    title: title,
    slug: document.getElementById("pg-slug").value.trim() || "",
    description: document.getElementById("pg-description") ? document.getElementById("pg-description").value.trim() || null : null,
    translations: pgTranslations,
    status: document.getElementById("pg-status").value,
    show_in_nav: document.getElementById("pg-nav").checked,
    meta_title: document.getElementById("pg-meta-title")?.value.trim() || null,
    meta_description: document.getElementById("pg-meta-desc")?.value.trim() || null,
    og_image: document.getElementById("pg-og-image")?.value.trim() || null,
    canonical_url: document.getElementById("pg-canonical")?.value.trim() || null,
    robots_index: document.getElementById("pg-robots")?.checked !== false,
  };

  try {
    let savedPage;
    if (pageId) {
      savedPage = await API.request(`/api/cms/pages/${pageId}`, {
        method: "PATCH", body: JSON.stringify(payload),
      });
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

    if (pageId) {
      await API.request(`/api/cms/pages/${pageId}/blocks`, {
        method: "PUT",
        body: JSON.stringify(window._pageBlocks.map((b, i) => ({
          block_type: b.block_type,
          content: b.content || null,
          image_url: b.image_url || null,
          settings_json: b.settings_json || null,
          sort_order: i,
        }))),
      });
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
            <h3>${esc(ml(n, "title"))}</h3>
            <p>${esc(ml(n, "summary") || "")}</p>
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
  const newsTranslationFields = [
    {key:"title", placeholder:tr("cms_hero_title"), type:"input"},
    {key:"summary", placeholder:tr("cms_summary"), type:"textarea", rows:2},
  ];

  cmsContent.innerHTML = `
    <div class="cms-header">
      <h2>${isEdit ? tr("edit") + ": " + esc(ml(news, "title")) : tr("cms_new_news")}</h2>
      <button class="btn btn-outline" onclick="loadNews()">← ${tr("cms_back")}</button>
    </div>
    <div class="cms-form">
      ${cmsLangTabs("nw", newsTranslationFields, news)}
      <div class="form-group">
        <label>Slug</label>
        <input id="nw-slug" value="${esc(news?.slug||'')}" placeholder="автоматӣ" />
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

  const nwTranslations = cmsBuildTranslations(["title","summary"], "nw");
  const payload = {
    title,
    slug: document.getElementById("nw-slug").value.trim() || "",
    summary: document.getElementById("nw-summary") ? document.getElementById("nw-summary").value.trim() || null : null,
    translations: nwTranslations,
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
              <td style="max-width:250px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(s.value || "-")} ${s.translations ? "🌐" : ""}</td>
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
  const trData = s.translations ? (typeof s.translations === "string" ? JSON.parse(s.translations) : s.translations) : {};
  const langs = [
    {code:"tj", label: typeof t==="function" ? t("lang_tj") : "Тоҷикӣ", flag:"🇹🇯"},
    {code:"ru", label: typeof t==="function" ? t("lang_ru") : "Русский", flag:"🇷🇺"},
    {code:"en", label: typeof t==="function" ? t("lang_en") : "English", flag:"🇬🇧"},
  ];

  let valueTabs = '<div class="lang-tabs" style="display:flex;gap:4px;margin-bottom:12px;border-bottom:2px solid var(--border)">';
  langs.forEach((l, i) => {
    valueTabs += '<button type="button" class="tab-btn '+(i===0?'active':'')+'" onclick="switchSettingLang(\''+l.code+'\',this)" style="padding:8px 14px;border:none;background:none;cursor:pointer;font-size:13px;color:'+(i===0?'var(--primary)':'var(--muted)')+';border-bottom:2px solid '+(i===0?'var(--primary)':'transparent')+';margin-bottom:-2px;transition:all .2s;font-weight:'+(i===0?'600':'400')+'">'+l.flag+' '+l.label+'</button>';
  });
  valueTabs += '</div>';

  langs.forEach((l, i) => {
    const val = l.code === "tj" ? (s.value || "") : (trData["value_" + l.code] || "");
    valueTabs += '<div class="lang-pane" data-st-lang="'+l.code+'" style="display:'+(i===0?'block':'none')+'">';
    valueTabs += '<textarea id="st-value-'+l.code+'" rows="3" placeholder="'+l.flag+' '+l.label+'">'+esc(val)+'</textarea>';
    valueTabs += '</div>';
  });

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
      ${valueTabs}
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

function switchSettingLang(lang, btn) {
  const panes = document.querySelectorAll("[data-st-lang]");
  panes.forEach(p => p.style.display = p.dataset.stLang === lang ? "block" : "none");
  const tabs = btn.parentElement.querySelectorAll(".tab-btn");
  tabs.forEach(t => { t.classList.remove("active"); t.style.color = "var(--muted)"; t.style.borderBottomColor = "transparent"; t.style.fontWeight = "400"; });
  btn.classList.add("active"); btn.style.color = "var(--primary)"; btn.style.borderBottomColor = "var(--primary)"; btn.style.fontWeight = "600";
}

async function saveSetting() {
  const key = document.getElementById("st-key").value.trim();
  if (!key) { showToast(tr("cms_enter_key"), "error"); return; }

  const valueTj = (document.getElementById("st-value-tj")?.value || "").trim();
  const valueRu = (document.getElementById("st-value-ru")?.value || "").trim();
  const valueEn = (document.getElementById("st-value-en")?.value || "").trim();

  const translations = {};
  if (valueRu) translations.value_ru = valueRu;
  if (valueEn) translations.value_en = valueEn;

  try {
    await API.request("/api/cms/settings", {
      method: "POST",
      body: JSON.stringify({
        key,
        value: valueTj,
        value_type: document.getElementById("st-type").value,
        label: document.getElementById("st-label").value.trim() || null,
        group_name: document.getElementById("st-group").value.trim() || "general",
        translations: Object.keys(translations).length ? JSON.stringify(translations) : null,
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
    { key: "site_name", value: "СохтМатериал", label: "Номи сайт", group_name: "identity",
      translations: JSON.stringify({value_ru: "СтройМатериал", value_en: "BuildMaterial"}) },
    { key: "site_description", value: "Маводҳои сохтмонии боифтихор", label: "Тавсифи сайт", group_name: "identity",
      translations: JSON.stringify({value_ru: "Качественные строительные материалы", value_en: "Quality construction materials"}) },
    { key: "site_phone", value: "+992 (00) 000-00-00", label: "Телефон", group_name: "contacts" },
    { key: "site_email", value: "info@sokhtmaterial.tj", label: "Email", group_name: "contacts" },
    { key: "site_address", value: "ш. Душанбе, к. Сомонӣ 1", label: "Суроға", group_name: "contacts",
      translations: JSON.stringify({value_ru: "г. Душанбе, ул. Сомони 1", value_en: "Dushanbe, Somoni st. 1"}) },
    { key: "work_hours_weekday", value: "Душ – Шан: 08:00 – 18:00", label: "Вақти корӣ (ҳафта)", group_name: "contacts",
      translations: JSON.stringify({value_ru: "Пн – Сб: 08:00 – 18:00", value_en: "Mon – Sat: 08:00 – 18:00"}) },
    { key: "work_hours_weekend", value: "Якшанбе: 09:00 – 15:00", label: "Вақти корӣ (якшанбе)", group_name: "contacts",
      translations: JSON.stringify({value_ru: "Воскресенье: 09:00 – 15:00", value_en: "Sunday: 09:00 – 15:00"}) },
    { key: "footer_desc", value: "Маводҳои сохтмонии баландсифат аз беҳтарин истеҳсолкунандагон.", label: "Тавсифи footer", group_name: "identity",
      translations: JSON.stringify({value_ru: "Качественные стройматериалы от лучших производителей.", value_en: "High-quality construction materials from the best manufacturers."}) },
    { key: "store_badge", value: "Local Pro Store", label: "Store identity badge", group_name: "identity" },
    { key: "store_promise_title", value: "Магазин барои сохтмони воқеӣ", label: "Store promise title", group_name: "identity",
      translations: JSON.stringify({value_ru: "Магазин для настоящего строительства", value_en: "A store for real construction"}) },
    { key: "store_promise_text", value: "Каталог, касса, CMS ва идоракунии анбор дар як системаи маҳаллӣ барои мағозаи сохтмонӣ.", label: "Store promise text", group_name: "identity",
      translations: JSON.stringify({value_ru: "Каталог, касса, CMS и управление складом в одной локальной системе.", value_en: "Catalog, cashier, CMS and warehouse management in one local system."}) },
    { key: "store_point_1_title", value: "Анбор + касса", label: "Identity point 1 title", group_name: "identity",
      translations: JSON.stringify({value_ru: "Склад + касса", value_en: "Warehouse + cashier"}) },
    { key: "store_point_1_text", value: "Фурӯш ва фармоишҳо бо бақияи маҳсулот пайваст мешаванд.", label: "Identity point 1 text", group_name: "identity",
      translations: JSON.stringify({value_ru: "Продажи и заказы связаны с остатками товара.", value_en: "Sales and orders are linked to product stock."}) },
    { key: "store_point_2_title", value: "CMS-и дохилӣ", label: "Identity point 2 title", group_name: "identity",
      translations: JSON.stringify({value_ru: "Встроенная CMS", value_en: "Built-in CMS"}) },
    { key: "store_point_2_text", value: "Саҳифа, хабар, меню ва SEO бе платформаи беруна идора мешаванд.", label: "Identity point 2 text", group_name: "identity",
      translations: JSON.stringify({value_ru: "Страницы, новости, меню и SEO управляются без внешней платформы.", value_en: "Pages, news, menus and SEO managed without external platform."}) },
    { key: "store_point_3_title", value: "3 забон", label: "Identity point 3 title", group_name: "identity",
      translations: JSON.stringify({value_ru: "3 языка", value_en: "3 languages"}) },
    { key: "store_point_3_text", value: "Интерфейс барои тоҷикӣ, русӣ ва англисӣ омода шудааст.", label: "Identity point 3 text", group_name: "identity",
      translations: JSON.stringify({value_ru: "Интерфейс готов для таджикского, русского и английского.", value_en: "Interface ready for Tajik, Russian and English."}) },
  ];
  try {
    await API.request("/api/cms/settings/bulk", {
      method: "POST", body: JSON.stringify({ settings: defaults }),
    });
    showToast(tr("cms_default_settings_saved"));
    loadSettings();
  } catch (e) { showToast(e.message, "error"); }
}



// ═══════════════════════════════════════════════════════════════
// GROWTH FEATURES
// ═══════════════════════════════════════════════════════════════

async function showPageVersions(pageId) {
  try {
    const versions = await API.request(`/api/cms/pages/${pageId}/versions`);
    showModal(`
      <h2>Page versions</h2>
      ${!versions.length ? '<p class="muted">No saved versions yet.</p>' : `
        <table class="data-table" style="width:100%">
          <thead><tr><th>Date</th><th>Note</th><th></th></tr></thead>
          <tbody>${versions.map(v => `
            <tr>
              <td>${new Date(v.created_at).toLocaleString()}</td>
              <td>${esc(v.note || "")}</td>
              <td><button class="btn btn-outline btn-sm" onclick="restorePageVersion(${pageId},${v.id})">Restore</button></td>
            </tr>`).join("")}</tbody>
        </table>`}
      <div class="modal-actions"><button class="btn btn-outline" onclick="closeModal()">${tr("cancel")}</button></div>
    `);
  } catch (e) { showToast(e.message, "error"); }
}

async function restorePageVersion(pageId, versionId) {
  if (!confirm("Restore this version?")) return;
  try {
    await API.request(`/api/cms/pages/${pageId}/versions/${versionId}/restore`, { method: "POST" });
    closeModal();
    showToast("Version restored");
    showPageEditor(pageId);
  } catch (e) { showToast(e.message, "error"); }
}

async function loadMedia() {
  try {
    const query = document.getElementById("media-search")?.value.trim() || "";
    const items = await API.request("/api/cms/media" + (query ? "?search=" + encodeURIComponent(query) : ""));
    cmsContent.innerHTML = `
      <div class="cms-header"><h2>Media library (${items.length})</h2>
        <button class="btn btn-primary" onclick="showMediaUpload()">Upload</button>
      </div>
      <div class="cms-form" style="margin-bottom:16px">
        <input id="media-search" value="${esc(query)}" placeholder="Search by filename or alt text" onkeydown="if(event.key==='Enter')loadMedia()" />
      </div>
      <div class="cms-cards">${items.map(m => `
        <div class="cms-card">
          <img src="${esc(safeUrl(m.url))}" alt="${esc(m.alt_text || "")}" style="width:100%;height:150px;object-fit:cover;border-radius:8px;margin-bottom:10px" />
          <h3>${esc(m.filename)}</h3>
          <p>${Math.round(m.size_bytes / 1024)} KB · used ${m.used_count || 0} times</p>
          <p>${esc(m.alt_text || "No alt text")}</p>
          <div class="cms-card-actions">
            <button class="btn btn-outline btn-sm" onclick="copyText('${esc(m.url)}')">Copy URL</button>
            <button class="btn btn-outline btn-sm" onclick="editMediaAlt(${m.id}, '${esc(m.alt_text || "")}')">Alt</button>
            <button class="btn btn-danger btn-sm" onclick="deleteMedia(${m.id})">Delete</button>
          </div>
        </div>`).join("")}</div>`;
  } catch (e) { cmsContent.innerHTML = `<p class="muted">${e.message}</p>`; }
}

function showMediaUpload() {
  showModal(`
    <h2>Upload media</h2>
    <input id="media-alt" placeholder="Alt text" />
    <input id="media-file" type="file" accept="image/*" />
    <div class="modal-actions">
      <button class="btn btn-outline" onclick="closeModal()">${tr("cancel")}</button>
      <button class="btn btn-primary" onclick="uploadMedia()">Upload</button>
    </div>
  `);
}

async function uploadMedia() {
  const file = document.getElementById("media-file").files[0];
  if (!file) { showToast("Choose file", "error"); return; }
  const form = new FormData();
  form.append("file", file);
  form.append("alt_text", document.getElementById("media-alt").value.trim());
  try {
    const res = await fetch("/api/cms/media", { method: "POST", headers: { Authorization: "Bearer " + API.token }, body: form });
    if (!res.ok) throw new Error((await res.json()).detail || "Upload failed");
    closeModal();
    showToast("Media uploaded");
    loadMedia();
  } catch (e) { showToast(e.message, "error"); }
}

async function editMediaAlt(id, alt) {
  showModal(`
    <h2>Edit alt text</h2>
    <input id="media-alt-edit" value="${esc(alt)}" />
    <div class="modal-actions">
      <button class="btn btn-outline" onclick="closeModal()">${tr("cancel")}</button>
      <button class="btn btn-primary" onclick="saveMediaAlt(${id})">${tr("save")}</button>
    </div>
  `);
}

async function saveMediaAlt(id) {
  try {
    await API.request(`/api/cms/media/${id}`, { method: "PATCH", body: JSON.stringify({ alt_text: document.getElementById("media-alt-edit").value.trim() || null }) });
    closeModal();
    showToast("Media saved");
    loadMedia();
  } catch (e) { showToast(e.message, "error"); }
}

async function deleteMedia(id) {
  if (!confirm("Delete unused media?")) return;
  try {
    await API.request(`/api/cms/media/${id}`, { method: "DELETE" });
    showToast("Media deleted");
    loadMedia();
  } catch (e) { showToast(e.message, "error"); }
}

function copyText(text) {
  navigator.clipboard?.writeText(text);
  showToast("Copied");
}

function loadImport() {
  cmsContent.innerHTML = `
    <div class="cms-header"><h2>Import products</h2></div>
    <div class="cms-form">
      <div class="identity-note">CSV/XLSX columns: name, category, price, description, stock, unit, volume, image_url, slug.</div>
      <input id="import-file" type="file" accept=".csv,.xlsx" />
      <div class="form-actions"><button class="btn btn-primary" onclick="importProducts()">Import</button></div>
      <pre id="import-result" class="identity-note" style="white-space:pre-wrap;display:none"></pre>
    </div>`;
}

async function importProducts() {
  const file = document.getElementById("import-file").files[0];
  if (!file) { showToast("Choose CSV or XLSX", "error"); return; }
  const form = new FormData();
  form.append("file", file);
  try {
    const res = await fetch("/api/products/import", { method: "POST", headers: { Authorization: "Bearer " + API.token }, body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Import failed");
    const out = document.getElementById("import-result");
    out.style.display = "block";
    out.textContent = JSON.stringify(data, null, 2);
    showToast("Import finished");
  } catch (e) { showToast(e.message, "error"); }
}

function loadAiTools() {
  cmsContent.innerHTML = `
    <div class="cms-header"><h2>${escapeHtml(t("cms_draft_assistant"))}</h2></div>
    <div class="cms-form">
      <input id="ai-name" placeholder="Product name" />
      <input id="ai-category" placeholder="Category" />
      <div class="form-row">
        <input id="ai-unit" placeholder="Unit" />
        <input id="ai-volume" placeholder="Volume" />
      </div>
      <div class="form-actions"><button class="btn btn-primary" onclick="generateAiCopy()">Generate product copy</button></div>
      <textarea id="ai-output" rows="10" placeholder="Generated content"></textarea>
      <hr>
      <textarea id="ai-translate-source" rows="4" placeholder="Text to translate"></textarea>
      <div class="form-actions"><button class="btn btn-outline" onclick="translateAiText()">Translate draft</button></div>
    </div>`;
}

async function generateAiCopy() {
  try {
    const data = await API.request("/api/cms/ai/product-copy", {
      method: "POST",
      body: JSON.stringify({
        name: document.getElementById("ai-name").value.trim(),
        category: document.getElementById("ai-category").value.trim() || null,
        unit: document.getElementById("ai-unit").value.trim() || null,
        volume: document.getElementById("ai-volume").value.trim() || null,
      }),
    });
    document.getElementById("ai-output").value = JSON.stringify(data, null, 2);
  } catch (e) { showToast(e.message, "error"); }
}

async function translateAiText() {
  try {
    const data = await API.request("/api/cms/ai/translate", {
      method: "POST",
      body: JSON.stringify({ text: document.getElementById("ai-translate-source").value.trim(), field: "description" }),
    });
    document.getElementById("ai-output").value = JSON.stringify(data, null, 2);
  } catch (e) { showToast(e.message, "error"); }
}

async function loadAudit() {
  try {
    const logs = await API.request("/api/cms/audit?limit=200");
    cmsContent.innerHTML = `
      <div class="cms-header"><h2>Action log</h2></div>
      <table class="data-table" style="width:100%">
        <thead><tr><th>Date</th><th>Action</th><th>Entity</th><th>Details</th></tr></thead>
        <tbody>${logs.map(l => `<tr><td>${new Date(l.created_at).toLocaleString()}</td><td>${esc(l.action)}</td><td>${esc(l.entity_type)} #${l.entity_id || ""}</td><td>${esc(l.details_json || "")}</td></tr>`).join("")}</tbody>
      </table>`;
  } catch (e) { cmsContent.innerHTML = `<p class="muted">${e.message}</p>`; }
}

async function loadReports() {
  try {
    const r = await API.request("/api/cms/reports/dashboard");
    cmsContent.innerHTML = `
      <div class="cms-header"><h2>Analytics and reports</h2></div>
      <div class="cms-cards">
        <div class="cms-card"><h3>${r.page_views}</h3><p>Page views</p></div>
        <div class="cms-card"><h3>${r.products}</h3><p>Products</p></div>
        <div class="cms-card"><h3>${r.products_without_stock}</h3><p>Products without stock</p></div>
        <div class="cms-card"><h3>${r.products_without_photo}</h3><p>Products without photo</p></div>
      </div>
      <h3>Popular products</h3>
      <table class="data-table" style="width:100%"><tbody>${r.popular_products.map(p => `<tr><td>${esc(p.name)}</td><td>${p.sold}</td></tr>`).join("")}</tbody></table>
      <h3>Search queries</h3>
      <table class="data-table" style="width:100%"><tbody>${r.search_queries.map(q => `<tr><td>${esc(q.query)}</td><td>${q.count}</td></tr>`).join("")}</tbody></table>`;
  } catch (e) { cmsContent.innerHTML = `<p class="muted">${e.message}</p>`; }
}

function loadCalculators() {
  cmsContent.innerHTML = `
    <div class="cms-header"><h2>Construction calculators</h2></div>
    <div class="cms-form">
      <div class="form-row">
        <input id="calc-area" type="number" step="0.01" placeholder="Area, m2" />
        <input id="calc-coverage" type="number" step="0.01" placeholder="Coverage per unit, m2" />
      </div>
      <div class="form-row">
        <input id="calc-waste" type="number" step="1" value="10" placeholder="Waste %" />
        <input id="calc-pack" type="number" step="0.01" value="1" placeholder="Units per pack" />
      </div>
      <div class="form-actions"><button class="btn btn-primary" onclick="runMaterialCalculator()">Calculate</button></div>
      <div id="calc-result" class="identity-note" style="display:none"></div>
    </div>`;
}

async function runMaterialCalculator() {
  try {
    const data = await API.request("/api/cms/calculators/material", {
      method: "POST",
      body: JSON.stringify({
        area_m2: Number(document.getElementById("calc-area").value),
        coverage_per_unit_m2: Number(document.getElementById("calc-coverage").value),
        waste_percent: Number(document.getElementById("calc-waste").value || 0),
        units_per_pack: Number(document.getElementById("calc-pack").value || 1),
      }),
    });
    const root = document.getElementById("calc-result");
    root.style.display = "block";
    root.innerHTML = `<strong>${data.units_needed}</strong> units · <strong>${data.packs_needed}</strong> packs`;
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

ensureCmsAdmin().then((ok) => {
  if (ok) loadPages();
});
