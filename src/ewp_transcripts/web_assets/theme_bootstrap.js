"use strict";

// Resolve appearance before styles or the deferred application can paint the page.
(() => {
  let preference = "system";
  try {
    const saved = JSON.parse(localStorage.getItem("ewp-gui-preferences-v1") || "{}");
    if (["light", "dark"].includes(saved?.theme)) preference = saved.theme;
  } catch (_) { /* unavailable or invalid storage follows the system */ }
  document.documentElement.dataset.theme = preference === "system"
    ? (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light") : preference;
})();
