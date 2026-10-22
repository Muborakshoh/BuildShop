/* ═══════════════════════════════════════════════════════════════
   Site Settings — Dynamic loading from CMS
   Loads settings from API and applies them to elements with
   data-site-setting="key" attributes. Supports multilingual.
   ═══════════════════════════════════════════════════════════════ */

(function () {
  "use strict";

  let _siteSettings = null;

  function getSettingValue(setting) {
    if (!setting) return "";
    const lang = (typeof currentLang !== "undefined") ? currentLang : (localStorage.getItem("lang") || "tj");
    if (lang === "tj") return setting.value || "";
    if (setting.translations) {
      try {
        const tr = typeof setting.translations === "string" ? JSON.parse(setting.translations) : setting.translations;
        const key = "value_" + lang;
        if (tr[key]) return tr[key];
      } catch (e) {}
    }
    return setting.value || "";
  }

  function applySettings(settings) {
    _siteSettings = {};
    settings.forEach(function (s) { _siteSettings[s.key] = s; });

    document.querySelectorAll("[data-site-setting]").forEach(function (el) {
      const key = el.getAttribute("data-site-setting");
      const setting = _siteSettings[key];
      if (!setting) return;
      const val = getSettingValue(setting);
      if (!val) return;

      const attr = el.getAttribute("data-setting-attr");
      if (attr === "href") {
        el.setAttribute("href", val);
      } else if (attr === "src") {
        el.setAttribute("src", val);
      } else {
        el.textContent = val;
      }
    });

    document.querySelectorAll("[data-site-setting-href]").forEach(function (el) {
      const key = el.getAttribute("data-site-setting-href");
      const setting = _siteSettings[key];
      if (!setting) return;
      const val = setting.value || "";
      if (val) el.setAttribute("href", val);
    });
  }

  async function loadSiteSettings() {
    try {
      const resp = await fetch("/api/cms/settings/public");
      if (!resp.ok) return;
      const settings = await resp.json();
      applySettings(settings);
    } catch (e) {}
  }

  function reapplySettings() {
    if (_siteSettings) {
      const arr = Object.values(_siteSettings);
      applySettings(arr);
    }
  }

  window.loadSiteSettings = loadSiteSettings;
  window.reapplySettings = reapplySettings;
  window.getSiteSetting = function (key) {
    if (!_siteSettings || !_siteSettings[key]) return "";
    return getSettingValue(_siteSettings[key]);
  };

  loadSiteSettings();

  const origSetLanguage = window.setLanguage;
  if (typeof origSetLanguage === "function") {
    window.setLanguage = function (lang) {
      origSetLanguage(lang);
      setTimeout(reapplySettings, 50);
    };
  } else {
    document.addEventListener("langchange", function () {
      setTimeout(reapplySettings, 50);
    });
  }
})();
