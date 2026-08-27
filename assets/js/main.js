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

  // ---- Cinematic motion layer -----------------------------------------
  // Progressive enhancement only: <html class="js"> is added by the inline
  // script in site_common.py's page() shell, before any of this runs. If
  // this script never executes (blocked, errors, disabled), the CSS never
  // switches .reveal into its hidden starting state, so content just stays
  // visible with no animation - see the reduced-motion block in style.css.
  var reducedMotion = false;
  try {
    reducedMotion = window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch (e) {
    reducedMotion = false;
  }

  if (!reducedMotion) {
    // Elements present in the server-rendered HTML at load time. Content
    // injected later by recipes.js/changelog.js (grid cards, modal body,
    // guide panes) is intentionally not covered here - it renders straight
    // to its normal visible state, which is correct since it wasn't on
    // screen yet for a scroll-entrance to make sense of.
    var REVEAL_SELECTOR = [
      "main > .hero", "main > section", "main > .card", "main > .toc",
      ".grid > *", ".card-list > *", ".timeline-entry", ".callout",
      ".guide-section", ".steps > li", "main > .tab-bar", "main > h2"
    ].join(", ");

    var targets = Array.prototype.slice.call(document.querySelectorAll(REVEAL_SELECTOR));
    // De-dupe (an element can match more than one selector above) and skip
    // anything nested inside another match, so a card's own children don't
    // also get queued with their own independent delay.
    targets = targets.filter(function (el, i) {
      if (targets.indexOf(el) !== i) return false;
      for (var j = 0; j < targets.length; j++) {
        if (targets[j] !== el && targets[j].contains(el)) return false;
      }
      return true;
    });

    // Stagger delay resets per parent, so each independent list/grid on the
    // page counts its own children from 0 rather than sharing one running
    // total (which would make later sections start their reveal absurdly
    // late). Plain array since parent elements repeat across targets;
    // avoids relying on Map/WeakMap for what stays a tiny list per page.
    var groupParents = [];
    var groupCounts = [];
    targets.forEach(function (el) {
      var parent = el.parentElement;
      var gi = groupParents.indexOf(parent);
      if (gi === -1) {
        gi = groupParents.length;
        groupParents.push(parent);
        groupCounts.push(0);
      }
      el.classList.add("reveal");
      el.style.setProperty("--reveal-index", String(groupCounts[gi]));
      groupCounts[gi] += 1;
    });

    if ("IntersectionObserver" in window && targets.length) {
      var io = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              entry.target.classList.add("is-visible");
              io.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
      );
      targets.forEach(function (el) { io.observe(el); });
    } else {
      // No IntersectionObserver support: reveal everything immediately
      // rather than leaving it permanently hidden.
      targets.forEach(function (el) { el.classList.add("is-visible"); });
    }

    // Subtle depth-of-field style parallax on the hero: its glow layer and
    // content drift at slightly different rates as the page scrolls. Small
    // amplitude, capped, and only runs while the hero is near the viewport.
    var hero = document.querySelector(".hero");
    if (hero) {
      var ticking = false;
      var updateParallax = function () {
        ticking = false;
        var rect = hero.getBoundingClientRect();
        if (rect.bottom < -200 || rect.top > window.innerHeight + 200) return;
        var offset = Math.max(-24, Math.min(24, rect.top * -0.06));
        hero.style.setProperty("--parallax", offset.toFixed(2));
      };
      var onScroll = function () {
        if (!ticking) {
          ticking = true;
          window.requestAnimationFrame(updateParallax);
        }
      };
      window.addEventListener("scroll", onScroll, { passive: true });
      updateParallax();
    }
  }
})();
