/* Calculator — construction materials estimator */

// Tab switching
document.querySelectorAll(".calc-tab").forEach(function (tab) {
  tab.addEventListener("click", function () {
    document.querySelectorAll(".calc-tab").forEach(function (t) { t.classList.remove("active"); });
    document.querySelectorAll(".calc-panel").forEach(function (p) { p.classList.remove("active"); });
    tab.classList.add("active");
    var panel = document.getElementById("panel-" + tab.getAttribute("data-tab"));
    if (panel) panel.classList.add("active");
  });
});

// Cached products list
var _cachedProducts = null;

async function getProducts() {
  if (_cachedProducts) return _cachedProducts;
  try {
    _cachedProducts = await API.request("/api/products?limit=500");
  } catch (e) {
    _cachedProducts = [];
  }
  return _cachedProducts;
}

function showResult(containerId, cards, suggestedProducts) {
  var container = document.getElementById(containerId);
  var html = '<h3>' + t("calc_result_title") + '</h3>';
  html += '<div class="result-grid">';
  cards.forEach(function (c) {
    html += '<div class="result-card"><div class="val">' + c.value + '</div><div class="lbl">' + c.label + '</div></div>';
  });
  html += '</div>';

  if (suggestedProducts && suggestedProducts.length) {
    html += '<div class="suggested-products"><h4>' + t("calc_suggested") + '</h4><div class="sug-list">';
    suggestedProducts.forEach(function (p) {
      var name = typeof ml === "function" ? ml(p, "name") : p.name;
      html += '<div class="sug-card">';
      html += '<div class="sug-name">' + escapeHtml(name) + '</div>';
      html += '<div class="sug-price">' + money(p.price) + '</div>';
      if (p._qty) html += '<div class="sug-qty">' + t("calc_need") + ': ' + p._qty + ' ' + (p.unit || t("analytics_pcs")) + '</div>';
      html += '<a href="/pages/product.html?id=' + p.id + '" class="btn btn-primary btn-sm">' + t("calc_view_product") + '</a>';
      html += '</div>';
    });
    html += '</div></div>';
  }

  container.innerHTML = html;
  container.classList.add("show");
}

// Keywords for matching products to calculation types
var WALL_KEYWORDS = ["кирпич", "хишт", "brick", "блок", "block", "газоблок", "пеноблок", "цемент", "cement", "раствор"];
var FLOOR_KEYWORDS = ["плитка", "кошин", "tile", "кафель", "керамогранит", "ламинат", "линолеум"];
var PAINT_KEYWORDS = ["краска", "ранг", "paint", "грунтовка", "лак", "эмаль"];
var ROOF_KEYWORDS = ["кровля", "шифер", "профнастил", "черепица", "металлочерепица", "roofing", "ондулин", "бом"];

function matchProducts(products, keywords) {
  return products.filter(function (p) {
    var name = (p.name || "").toLowerCase();
    var desc = (p.description || "").toLowerCase();
    var tr = JSON.stringify(p.translations || {}).toLowerCase();
    return keywords.some(function (kw) {
      return name.indexOf(kw) !== -1 || desc.indexOf(kw) !== -1 || tr.indexOf(kw) !== -1;
    });
  }).filter(function (p) { return p.stock_quantity > 0; }).slice(0, 6);
}

// ======= WALL CALCULATOR =======
async function calcWalls() {
  var length = parseFloat(document.getElementById("wall-length").value) || 0;
  var height = parseFloat(document.getElementById("wall-height").value) || 0;
  var thicknessCm = parseInt(document.getElementById("wall-thickness").value) || 25;
  var openings = parseFloat(document.getElementById("wall-openings").value) || 0;

  if (length <= 0 || height <= 0) { showToast(t("calc_error_input"), "error"); return; }

  var wallArea = length * height - openings;
  if (wallArea <= 0) { showToast(t("calc_error_area"), "error"); return; }

  // Standard brick: 250×120×65 mm, mortar joint ~10mm
  var brickL = 0.25, brickH = 0.065, joint = 0.01;
  var bricksPerM2;
  if (thicknessCm <= 12) bricksPerM2 = 52;
  else if (thicknessCm <= 25) bricksPerM2 = 104;
  else if (thicknessCm <= 38) bricksPerM2 = 156;
  else bricksPerM2 = 208;

  var totalBricks = Math.ceil(wallArea * bricksPerM2 * 1.07); // 7% waste
  var cementBags = Math.ceil(wallArea * thicknessCm / 25 * 0.25); // ~0.25 bags per m² per brick thickness

  var cards = [
    { value: wallArea.toFixed(1) + " м²", label: t("calc_wall_area") },
    { value: totalBricks.toLocaleString(), label: t("calc_bricks_count") },
    { value: cementBags, label: t("calc_cement_bags") }
  ];

  var products = await getProducts();
  var suggested = matchProducts(products, WALL_KEYWORDS);
  showResult("result-walls", cards, suggested);
}

// ======= FLOOR CALCULATOR =======
async function calcFloor() {
  var length = parseFloat(document.getElementById("floor-length").value) || 0;
  var width = parseFloat(document.getElementById("floor-width").value) || 0;
  var tileSizeCm = parseInt(document.getElementById("tile-size").value) || 50;
  var wastePct = parseInt(document.getElementById("floor-waste").value) || 10;

  if (length <= 0 || width <= 0) { showToast(t("calc_error_input"), "error"); return; }

  var area = length * width;
  var tileSizeM = tileSizeCm / 100;
  var tileArea = tileSizeM * tileSizeM;
  var tilesNeeded = Math.ceil(area / tileArea * (1 + wastePct / 100));
  var glueBags = Math.ceil(area * 5 / 25); // ~5 kg/m², bags of 25 kg

  var cards = [
    { value: area.toFixed(1) + " м²", label: t("calc_floor_area") },
    { value: tilesNeeded.toLocaleString(), label: t("calc_tiles_count") },
    { value: glueBags, label: t("calc_glue_bags") }
  ];

  var products = await getProducts();
  var suggested = matchProducts(products, FLOOR_KEYWORDS);
  showResult("result-floor", cards, suggested);
}

// ======= PAINT CALCULATOR =======
async function calcPaint() {
  var area = parseFloat(document.getElementById("paint-area").value) || 0;
  var layers = parseInt(document.getElementById("paint-layers").value) || 2;
  var consumption = parseFloat(document.getElementById("paint-consumption").value) || 0.15;

  if (area <= 0) { showToast(t("calc_error_input"), "error"); return; }

  var totalKg = area * layers * consumption;
  var buckets10 = Math.ceil(totalKg / 10);

  var cards = [
    { value: area.toFixed(1) + " м²", label: t("calc_paint_total_area") },
    { value: totalKg.toFixed(1) + " " + t("calc_kg"), label: t("calc_paint_total_kg") },
    { value: buckets10 + " × 10" + t("calc_kg"), label: t("calc_paint_buckets") }
  ];

  var products = await getProducts();
  var suggested = matchProducts(products, PAINT_KEYWORDS);
  showResult("result-paint", cards, suggested);
}

// ======= ROOF CALCULATOR =======
async function calcRoof() {
  var length = parseFloat(document.getElementById("roof-length").value) || 0;
  var width = parseFloat(document.getElementById("roof-width").value) || 0;
  var angleDeg = parseFloat(document.getElementById("roof-angle").value) || 30;
  var overlapPct = parseInt(document.getElementById("roof-overlap").value) || 15;

  if (length <= 0 || width <= 0) { showToast(t("calc_error_input"), "error"); return; }

  var angleRad = angleDeg * Math.PI / 180;
  var slopeLength = (width / 2) / Math.cos(angleRad);
  var roofArea = length * slopeLength * 2; // two slopes
  var totalArea = roofArea * (1 + overlapPct / 100);

  // Standard sheet: ~1.18m × 2m effective area
  var sheetArea = 1.18 * 2;
  var sheetsNeeded = Math.ceil(totalArea / sheetArea);

  var cards = [
    { value: roofArea.toFixed(1) + " м²", label: t("calc_roof_area") },
    { value: totalArea.toFixed(1) + " м²", label: t("calc_roof_with_overlap") },
    { value: sheetsNeeded, label: t("calc_roof_sheets") }
  ];

  var products = await getProducts();
  var suggested = matchProducts(products, ROOF_KEYWORDS);
  showResult("result-roof", cards, suggested);
}
