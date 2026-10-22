/* Bottom Nav — curved notch + dynamic "more" menu with admin & CMS pages */
(function () {
  var path = window.location.pathname;

  /* ── SVG icons ── */
  var icons = {
    home:      '<svg viewBox="0 0 24 24"><path d="M3 9.5L12 3l9 6.5V20a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    search:    '<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    calc:      '<svg viewBox="0 0 24 24"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><circle cx="8" cy="10" r=".5"/><circle cx="12" cy="10" r=".5"/><circle cx="16" cy="10" r=".5"/><circle cx="8" cy="14" r=".5"/><circle cx="12" cy="14" r=".5"/><circle cx="16" cy="14" r=".5"/><line x1="8" y1="18" x2="12" y2="18"/></svg>',
    cart:      '<svg viewBox="0 0 24 24"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 002-1.61L23 6H6"/></svg>',
    orders:    '<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
    categories:'<svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
    news:      '<svg viewBox="0 0 24 24"><path d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2"/><line x1="9" y1="9" x2="13" y2="9"/><line x1="9" y1="13" x2="13" y2="13"/></svg>',
    user:      '<svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    more:      '<svg viewBox="0 0 24 24"><circle cx="12" cy="5" r="1.5" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none"/><circle cx="12" cy="19" r="1.5" fill="currentColor" stroke="none"/></svg>',
    products:  '<svg viewBox="0 0 24 24"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>',
    cms:       '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>',
    analytics: '<svg viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    cashier:   '<svg viewBox="0 0 24 24"><rect x="2" y="4" width="20" height="16" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/><line x1="6" y1="14" x2="10" y2="14"/></svg>',
    admin:     '<svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    page:      '<svg viewBox="0 0 24 24"><path d="M4 4h16a2 2 0 012 2v12a2 2 0 01-2 2H4a2 2 0 01-2-2V6a2 2 0 012-2z"/><line x1="2" y1="10" x2="22" y2="10"/></svg>',
    close:     '<svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>'
  };

  /* ── Helper ── */
  function isActivePath(href) {
    if (href === "/" && (path === "/" || path === "/index.html")) return true;
    if (href !== "/") {
      var slug = href.replace("/pages/", "").replace(".html", "").split("?")[0];
      if (path.indexOf(slug) !== -1) return true;
      if (href.indexOf("?slug=") !== -1 && location.search.indexOf(href.split("?slug=")[1]) !== -1) return true;
    }
    return false;
  }

  /* ── Cart count ── */
  var cartCount = 0;
  try {
    var c = JSON.parse(localStorage.getItem("cart") || "[]");
    cartCount = c.reduce(function (s, i) { return s + i.qty; }, 0);
  } catch (e) {}

  /* ── 4 main tabs (always visible) ── */
  var mainTabs = [
    { href: "/",                      icon: "home",   key: "nav_home",      label: "Асосӣ" },
    { href: "/pages/products.html",   icon: "search", key: "nav_products",  label: "Каталог" },
    { href: "/pages/cart.html",       icon: "cart",   key: "nav_cart",      label: "Сабад", badge: cartCount },
    { href: "/pages/orders.html",     icon: "orders", key: "nav_my_orders", label: "Фармоишҳо" }
  ];

  /* ── Static "more" items (always present) ── */
  var staticMore = [
    { href: "/pages/calculator.html",  icon: "calc",       key: "nav_calculator", label: "Калкулятор" },
    { href: "/pages/categories.html",  icon: "categories", key: "nav_categories", label: "Категорияҳо" }
  ];

  /* ── Admin items (added if user is admin/manager) ── */
  var adminMore = [
    { href: "/pages/admin-products.html",  icon: "products",  key: "admin_products", label: "Молҳо" },
    { href: "/pages/admin-analytics.html", icon: "analytics", key: "nav_analytics",  label: "Аналитика" },
    { href: "/pages/admin-users.html",     icon: "admin",     key: "admin_users",    label: "Админ" },
    { href: "/pages/admin-cms.html",       icon: "cms",       key: "admin_cms",      label: "CMS" },
    { href: "/pages/cashier.html",         icon: "cashier",   key: "nav_cashier",    label: "Касса" }
  ];

  /* ══════════════════════════════════════════
     Build the bottom nav bar (immediate)
     ══════════════════════════════════════════ */
  var nav = document.createElement("nav");
  nav.className = "bottom-nav";
  nav.setAttribute("role", "navigation");

  var html = '';

  /* Main tabs */
  mainTabs.forEach(function (tab) {
    var active = isActivePath(tab.href);
    var badge = (tab.badge && tab.badge > 0) ? '<span class="bnav-badge" id="tab-cart-badge">' + tab.badge + '</span>' : '';
    if (active) {
      html += '<a href="' + tab.href + '" class="bnav-tab bnav-tab--active">';
      html += '<div class="bnav-notch"></div>';
      html += '<div class="bnav-fab">' + badge + icons[tab.icon] + '</div>';
      html += '<span class="bnav-lbl" data-i18n="' + tab.key + '">' + tab.label + '</span>';
      html += '</a>';
    } else {
      html += '<a href="' + tab.href + '" class="bnav-tab">' + badge + icons[tab.icon] + '</a>';
    }
  });

  /* "More" button */
  html += '<button class="bnav-tab bnav-more-btn" id="bnav-more-btn" aria-label="More">';
  html += icons.more;
  html += '</button>';

  /* More panel shell (will be populated dynamically) */
  html += '<div class="bnav-more-panel" id="bnav-more-panel">';
  html += '<div class="bnav-more-header">';
  html += '<span data-i18n="nav_more">Бештар</span>';
  html += '<button class="bnav-more-close" id="bnav-more-close">' + icons.close + '</button>';
  html += '</div>';
  html += '<div class="bnav-more-grid" id="bnav-more-grid"></div>';
  html += '</div>';

  /* Overlay */
  html += '<div class="bnav-overlay" id="bnav-overlay"></div>';

  nav.innerHTML = html;
  document.body.appendChild(nav);

  /* ── More panel toggle ── */
  var moreBtn = document.getElementById("bnav-more-btn");
  var morePanel = document.getElementById("bnav-more-panel");
  var moreClose = document.getElementById("bnav-more-close");
  var overlay = document.getElementById("bnav-overlay");

  function closeMore() {
    morePanel.classList.remove("open");
    overlay.classList.remove("open");
    document.body.style.overflow = "";
  }
  function toggleMore(e) {
    if (e) e.stopPropagation();
    var open = morePanel.classList.toggle("open");
    overlay.classList.toggle("open", open);
    document.body.style.overflow = open ? "hidden" : "";
  }
  moreBtn.addEventListener("click", toggleMore);
  moreClose.addEventListener("click", closeMore);
  overlay.addEventListener("click", closeMore);

  /* ══════════════════════════════════════════
     Populate "more" grid dynamically
     (loads user role + CMS pages from API)
     ══════════════════════════════════════════ */
  function renderMoreItem(item) {
    var active = isActivePath(item.href) ? " bnav-more-item--active" : "";
    return '<a href="' + item.href + '" class="bnav-more-item' + active + '">' +
      '<div class="bnav-more-icon">' + (icons[item.icon] || icons.page) + '</div>' +
      '<span' + (item.key ? ' data-i18n="' + item.key + '"' : '') + '>' + item.label + '</span></a>';
  }

  function renderMoreGrid(items) {
    var grid = document.getElementById("bnav-more-grid");
    grid.innerHTML = items.map(renderMoreItem).join("");
    /* If current page is in the more menu, highlight the more button */
    var inMore = items.some(function(t) { return isActivePath(t.href); });
    moreBtn.classList.toggle("bnav-more-btn--active", inMore);
    /* Apply i18n if available */
    if (typeof applyI18n === "function") applyI18n();
  }

  /* Immediately render static items */
  renderMoreGrid(staticMore);

  /* Then fetch user role + CMS pages and update */
  (async function loadDynamicMore() {
    var allItems = staticMore.slice();

    try {
      /* Fetch user, CMS pages, and news in parallel */
      var results = await Promise.all([
        fetch("/api/users/me", {
          headers: { "Authorization": "Bearer " + (localStorage.getItem("access_token") || "") }
        }).then(function(r) { return r.ok ? r.json() : null; }).catch(function() { return null; }),

        fetch("/api/cms/pages/public")
          .then(function(r) { return r.ok ? r.json() : []; }).catch(function() { return []; }),

        fetch("/api/cms/news/public?limit=1")
          .then(function(r) { return r.ok ? r.json() : []; }).catch(function() { return []; })
      ]);

      var user = results[0];
      var cmsPages = results[1];
      var newsItems = results[2];

      /* Add news link if news exist */
      if (newsItems.length > 0) {
        allItems.push({
          href: "/pages/news.html", icon: "news", key: "nav_news", label: "Навигарон"
        });
      }

      /* Add CMS pages with show_in_nav */
      cmsPages.forEach(function(page) {
        if (page.show_in_nav) {
          var name = page.title;
          if (typeof ml === "function") {
            try { name = ml(page, "title"); } catch(e) {}
          }
          allItems.push({
            href: "/pages/page.html?slug=" + page.slug,
            icon: "page",
            key: "",
            label: name
          });
        }
      });

      /* Add user profile / auth */
      if (user) {
        allItems.push({
          href: "/pages/auth.html", icon: "user", key: "nav_profile", label: user.name || "Профил"
        });
      } else {
        allItems.push({
          href: "/pages/auth.html", icon: "user", key: "login", label: "Ворид шудан"
        });
      }

      /* Add admin section if user is admin/manager */
      if (user && (user.role === "admin" || user.role === "manager")) {
        /* Divider */
        allItems.push({ divider: true, label: "Админ панел" });
        adminMore.forEach(function(item) { allItems.push(item); });
      }

      renderMoreGrid(allItems);

    } catch(e) {
      console.warn("Bottom nav dynamic load failed:", e);
    }
  })();

  /* ── Render including dividers ── */
  var _origRender = renderMoreGrid;
  renderMoreGrid = function(items) {
    var grid = document.getElementById("bnav-more-grid");
    var htmlStr = "";
    items.forEach(function(item) {
      if (item.divider) {
        htmlStr += '<div class="bnav-more-divider"><span>' + item.label + '</span></div>';
      } else {
        htmlStr += renderMoreItem(item);
      }
    });
    grid.innerHTML = htmlStr;
    var inMore = items.some(function(t) { return !t.divider && isActivePath(t.href); });
    moreBtn.classList.toggle("bnav-more-btn--active", inMore);
    if (typeof applyI18n === "function") applyI18n();
  };

  /* ── Cart badge live update ── */
  window.addEventListener("storage", function (e) {
    if (e.key === "cart") {
      try {
        var c = JSON.parse(e.newValue || "[]");
        var count = c.reduce(function (s, i) { return s + i.qty; }, 0);
        var b = document.getElementById("tab-cart-badge");
        if (b) { b.textContent = count; b.style.display = count > 0 ? "flex" : "none"; }
      } catch (err) {}
    }
  });
})();
