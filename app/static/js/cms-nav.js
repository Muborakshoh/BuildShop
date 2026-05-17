/* ═══════════════════════════════════════════════════════════════
   CMS Dynamic Navigation — loads menus & pages from database
   Include this script on EVERY page after api.js
   ═══════════════════════════════════════════════════════════════ */

(async function loadCmsNavigation() {
  const nav = document.getElementById("main-nav");
  if (!nav) return;

  try {
    // 1) Load CMS menu items for header
    const menuItems = await fetch("/api/cms/menus/public/header").then(r => r.ok ? r.json() : []);

    // 2) Load published CMS pages that should appear in nav
    const cmsPages = await fetch("/api/cms/pages/public").then(r => r.ok ? r.json() : []);
    const navPages = cmsPages.filter(p => p.show_in_nav);

    // Find insertion point — before cart link or admin links
    const cartLink = nav.querySelector('a[href*="cart.html"]');
    const insertBefore = cartLink || null;

    // Add CMS menu items
    menuItems.forEach(item => {
      // Skip if a link with same URL already exists (avoid duplicates)
      if (nav.querySelector('a[href="' + item.url + '"]')) return;

      const a = document.createElement("a");
      a.href = item.url;
      a.textContent = (item.icon ? item.icon + " " : "") + item.label;
      if (item.open_new_tab) a.target = "_blank";
      a.classList.add("cms-nav-link");

      // Highlight current page
      if (location.pathname === item.url || location.href.includes(item.url)) {
        a.classList.add("active");
      }

      nav.insertBefore(a, insertBefore);
    });

    // Add CMS pages with show_in_nav
    navPages.forEach(page => {
      const pageUrl = "/pages/page.html?slug=" + page.slug;
      // Skip if already added by menu items
      if (nav.querySelector('a[href="' + pageUrl + '"]')) return;
      if (nav.querySelector('a.cms-nav-link[href*="' + page.slug + '"]')) return;

      const a = document.createElement("a");
      a.href = pageUrl;
      a.textContent = page.title;
      a.classList.add("cms-nav-link");

      if (location.search.includes("slug=" + page.slug)) {
        a.classList.add("active");
      }

      nav.insertBefore(a, insertBefore);
    });

    // 3) Load CMS news link if there are published news
    const newsCheck = await fetch("/api/cms/news/public?limit=1").then(r => r.ok ? r.json() : []);
    if (newsCheck.length > 0) {
      const newsUrl = "/pages/news.html";
      if (!nav.querySelector('a[href="' + newsUrl + '"]')) {
        const a = document.createElement("a");
        a.href = newsUrl;
        a.textContent = "Навигарӣ";  // Навигарӣ
        a.classList.add("cms-nav-link");
        if (location.pathname.includes("news.html")) a.classList.add("active");
        nav.insertBefore(a, insertBefore);
      }
    }

  } catch (e) {
    console.warn("CMS nav load failed:", e);
  }
})();
