const container = document.getElementById("product-detail");
const id = new URLSearchParams(window.location.search).get("id");

function calcFieldsHtml(p) {
  if (!p || !p.coverage_per_unit_m2) return "";
  const waste = p.calc_waste_percent ?? 10;
  return `
    <section class="material-calc card">
      <h3>${escapeHtml(t("calc_title"))}</h3>
      <div class="calc-grid">
        <label>${escapeHtml(t("calc_area"))}
          <input id="calc-area" type="number" min="0.1" step="0.1" value="10" />
        </label>
        <label>${escapeHtml(t("calc_waste"))}
          <input id="calc-waste" type="number" min="0" step="1" value="${waste}" />
        </label>
      </div>
      <button type="button" class="btn btn-outline btn-sm" onclick="runMaterialCalc()">${escapeHtml(t("calc_run"))}</button>
      <div id="calc-result" class="calc-result muted" style="display:none"></div>
    </section>
  `;
}

async function runMaterialCalc() {
  const p = window._product;
  if (!p) return;
  const area = parseFloat(document.getElementById("calc-area")?.value);
  const waste = parseFloat(document.getElementById("calc-waste")?.value);
  if (!area || area <= 0) return;
  try {
    const data = await API.request("/api/cms/calculators/material/public", {
      method: "POST",
      body: JSON.stringify({
        product_id: p.id,
        area_m2: area,
        waste_percent: Number.isFinite(waste) ? waste : null,
      }),
    });
    const result = document.getElementById("calc-result");
    result.style.display = "block";
    result.innerHTML = `<strong>${escapeHtml(t("calc_units"))}:</strong> ${data.units_needed}` +
      (data.packs_needed != null ? ` · <strong>${escapeHtml(t("calc_packs"))}:</strong> ${data.packs_needed}` : "");
  } catch (e) {
    showToast(e.message, "error");
  }
}
window.runMaterialCalc = runMaterialCalc;

async function loadProduct() {
  if (!id) { container.innerHTML = '<p class="muted">Product ID not specified</p>'; return; }
  try {
    const p = await API.request(`/api/products/${id}`);
    setSeoMeta({
      title: p.meta_title || `${ml(p, "name")} — СохтМатериал`,
      description: p.meta_description || ml(p, "description"),
      ogImage: p.og_image || p.image_url,
      canonicalUrl: p.canonical_url,
      robotsIndex: p.robots_index,
    });
    trackPageView({ product_id: p.id });
    container.innerHTML = `
      <img src="${escapeHtml(safeUrl(p.image_url))}" alt="${escapeHtml(ml(p, "name"))}" />
      <div class="product-detail-info">
        <span class="badge badge--blue">${escapeHtml(ml(p.category, "name"))}</span>
        <h1>${escapeHtml(ml(p, "name"))}</h1>
        <div class="product-price">${money(p.price)}</div>
        ${p.volume ? `<span class="product-unit">${escapeHtml(p.volume)} ${escapeHtml(p.unit || '')}</span>` : ''}
        <p class="product-desc">${escapeHtml(ml(p, "description"))}</p>
        <span class="product-meta">${t("stock_left")}: ${p.stock_quantity}</span>
        ${calcFieldsHtml(p)}
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
    loadReviews(p.id);
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

// ── Reviews ──────────────────────────────────────────────────
function starsHtml(rating, interactive = false) {
  let html = '<div class="stars">';
  for (let i = 1; i <= 5; i++) {
    const cls = i <= rating ? "star filled" : "star";
    if (interactive) {
      html += `<span class="${cls}" data-star="${i}" onclick="selectStar(${i})" onmouseover="hoverStar(${i})" onmouseout="resetStars()">★</span>`;
    } else {
      html += `<span class="${cls}">★</span>`;
    }
  }
  html += '</div>';
  return html;
}

let selectedRating = 0;

function selectStar(n) {
  selectedRating = n;
  document.querySelectorAll("#review-form .star").forEach((s) => {
    s.classList.toggle("filled", parseInt(s.dataset.star) <= n);
  });
}

function hoverStar(n) {
  document.querySelectorAll("#review-form .star").forEach((s) => {
    s.classList.toggle("filled", parseInt(s.dataset.star) <= n);
  });
}

function resetStars() {
  document.querySelectorAll("#review-form .star").forEach((s) => {
    s.classList.toggle("filled", parseInt(s.dataset.star) <= selectedRating);
  });
}

async function loadReviews(productId) {
  try {
    const [reviews, rating] = await Promise.all([
      API.request(`/api/reviews/product/${productId}`),
      API.request(`/api/reviews/product/${productId}/rating`),
    ]);

    const avgText = rating.avg_rating ? `${rating.avg_rating} / 5` : t("no_reviews_yet");
    const currentUserId = API.currentUser?.id;
    const userHasReview = reviews.some((r) => r.user.id === currentUserId);

    let html = `<section class="reviews-section card">
      <h3>${escapeHtml(t("reviews_title"))} (${rating.review_count})</h3>
      <div class="reviews-summary">
        ${starsHtml(Math.round(rating.avg_rating || 0))}
        <span class="avg-rating">${avgText}</span>
      </div>`;

    // Review form (only for logged-in users who haven't reviewed yet)
    if (API.currentUser && !userHasReview) {
      html += `<div id="review-form" class="review-form">
        <h4>${escapeHtml(t("write_review"))}</h4>
        ${starsHtml(0, true)}
        <textarea id="review-text" rows="3" placeholder="${escapeHtml(t("review_placeholder"))}" maxlength="2000"></textarea>
        <button class="btn btn-primary btn-sm" onclick="submitReview()">${escapeHtml(t("submit_review"))}</button>
      </div>`;
    } else if (!API.currentUser) {
      html += `<p class="muted"><a href="/pages/auth.html">${escapeHtml(t("login_to_review"))}</a></p>`;
    }

    // Reviews list
    if (reviews.length > 0) {
      html += '<div class="reviews-list">';
      for (const r of reviews) {
        const date = new Date(r.created_at).toLocaleDateString("ru-RU");
        const isOwn = r.user.id === currentUserId;
        html += `<div class="review-item">
          <div class="review-header">
            <strong>${escapeHtml(r.user.full_name)}</strong>
            ${starsHtml(r.rating)}
            <span class="muted">${date}</span>
            ${isOwn ? `<button class="btn-icon" onclick="deleteReview(${r.id})" title="${escapeHtml(t("delete"))}">🗑</button>` : ""}
          </div>
          ${r.text ? `<p class="review-text">${escapeHtml(r.text)}</p>` : ""}
        </div>`;
      }
      html += '</div>';
    }

    html += '</section>';

    // Insert after product detail
    const existing = document.querySelector(".reviews-section");
    if (existing) existing.remove();
    container.insertAdjacentHTML("afterend", html);
  } catch (e) {
    console.warn("Reviews load error:", e.message);
  }
}

async function submitReview() {
  if (!selectedRating) {
    showToast(t("select_rating"), "error");
    return;
  }
  const text = document.getElementById("review-text")?.value.trim() || null;
  try {
    await API.request("/api/reviews/", {
      method: "POST",
      body: JSON.stringify({ product_id: parseInt(id), rating: selectedRating, text }),
    });
    showToast(t("review_submitted"));
    selectedRating = 0;
    loadReviews(parseInt(id));
  } catch (e) {
    showToast(e.message, "error");
  }
}

async function deleteReview(reviewId) {
  if (!confirm(t("confirm_delete_review"))) return;
  try {
    await API.request(`/api/reviews/${reviewId}`, { method: "DELETE" });
    showToast(t("review_deleted"));
    loadReviews(parseInt(id));
  } catch (e) {
    showToast(e.message, "error");
  }
}

window.selectStar = selectStar;
window.hoverStar = hoverStar;
window.resetStars = resetStars;
window.submitReview = submitReview;
window.deleteReview = deleteReview;

loadProduct();
