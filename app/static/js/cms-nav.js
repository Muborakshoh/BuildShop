/* ═══════════════════════════════════════════════════════════════
   CMS Dynamic Navigation — loads menus & pages from database
   Include this script on EVERY page after api.js and i18n.js
   ═══════════════════════════════════════════════════════════════ */

(async function loadCmsNavigation() {
  const nav = document.getElementById("main-nav"); if (!nav) return;
  if (!nav) return;

  try {
    // Parallel fetch for speed
    const [menuItems, cmsPages, newsCheck] = await Promise.all([
      fetch("/api/cms/menus/public/header").then(r => r.ok ? r.json() : []).catch(() => []),
      fetch("/api/cms/pages/public").then(r => r.ok ? r.json() : []).catch(() => []),
      fetch("/api/cms/news/public?limit=1").then(r => r.ok ? r.json() : []).catch(() => []),
    ]);

    const cartLink = nav.querySelector('a[href*="cart.html"]');
    const insertBefore = cartLink || null;

    // Add CMS menu items
    menuItems.forEach(item => {
      if (nav.querySelector('a[href="' + item.url + '"]')) return;
      const a = document.createElement("a");
      a.href = item.url;
      a.textContent = (item.icon ? item.icon + " " : "") + item.label;
      if (item.open_new_tab) a.target = "_blank";
      a.classList.add("cms-nav-link");
      if (location.pathname === item.url || location.href.includes(item.url)) a.classList.add("active");
      nav.insertBefore(a, insertBefore);
    });

    // Add CMS pages with show_in_nav
    cmsPages.filter(p => p.show_in_nav).forEach(page => {
      const pageUrl = "/pages/page.html?slug=" + page.slug;
      if (nav.querySelector('a[href="' + pageUrl + '"]')) return;
      const a = document.createElement("a");
      a.href = pageUrl;
      a.textContent = ml(page, "title");
      a.classList.add("cms-nav-link");
      if (location.search.includes("slug=" + page.slug)) a.classList.add("active");
      nav.insertBefore(a, insertBefore);
    });

    // Add news link if published news exist
    if (newsCheck.length > 0) {
      const newsUrl = "/pages/news.html";
      if (!nav.querySelector('a[href="' + newsUrl + '"]')) {
        const a = document.createElement("a");
        a.href = newsUrl;
        a.textContent = t("cms_news");
        a.classList.add("cms-nav-link");
        if (location.pathname.includes("news.html")) a.classList.add("active");
        nav.insertBefore(a, insertBefore);
      }
    }
  } catch (e) {
    console.warn("CMS nav load failed:", e);
  }
})();
