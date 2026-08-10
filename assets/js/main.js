(function () {
  "use strict";

  // Mobile nav toggle
  var navToggle = document.getElementById("navToggle");
  var siteNav = document.getElementById("siteNav");
  if (navToggle && siteNav) {
    navToggle.addEventListener("click", function () {
      var open = siteNav.classList.toggle("open");
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    siteNav.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () {
        siteNav.classList.remove("open");
        navToggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  // Language switcher dropdown
  var langToggle = document.getElementById("langToggle");
  var langSwitch = langToggle && langToggle.closest(".lang-switch");
  if (langToggle && langSwitch) {
    langToggle.addEventListener("click", function (e) {
      e.stopPropagation();
      var open = langSwitch.classList.toggle("open");
      langToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.addEventListener("click", function (e) {
      if (!langSwitch.contains(e.target)) {
        langSwitch.classList.remove("open");
        langToggle.setAttribute("aria-expanded", "false");
      }
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        langSwitch.classList.remove("open");
        langToggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  // Theme toggle: light -> dark -> system, persisted in localStorage
  var themeToggle = document.getElementById("themeToggle");
  var root = document.documentElement;
  var STORAGE_KEY = "glimpse-alpha-wiki-theme";

  function applyTheme(mode) {
    if (mode === "light" || mode === "dark") {
      root.setAttribute("data-theme", mode);
    } else {
      root.removeAttribute("data-theme");
    }
  }

  function currentMode() {
    try {
      return localStorage.getItem(STORAGE_KEY) || "system";
    } catch (e) {
      return "system";
    }
  }

  applyTheme(currentMode());

  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      var mode = currentMode();
      var next = mode === "system" ? "dark" : mode === "dark" ? "light" : "system";
      try {
        if (next === "system") {
          localStorage.removeItem(STORAGE_KEY);
        } else {
          localStorage.setItem(STORAGE_KEY, next);
        }
      } catch (e) {
        /* private browsing / storage disabled: theme just won't persist */
      }
      applyTheme(next);
    });
  }
})();
