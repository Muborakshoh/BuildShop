function setTheme(name) {
  document.documentElement.setAttribute("data-theme", name);
  localStorage.setItem("theme", name);
  const toggle = document.getElementById("theme-toggle");
  if (toggle) toggle.checked = name === "dark";
}
// Apply saved theme
(function() {
  const saved = localStorage.getItem("theme") || "light";
  setTheme(saved);
})();
