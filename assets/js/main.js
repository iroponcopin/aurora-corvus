/* Aurora Corvus — shared behaviour layer.
 *
 * Performance contract for everything in this file (owner directive: the
 * site must feel right on a 120Hz ProMotion display, not merely on 60Hz):
 *
 *   1. There is exactly ONE scroll listener and ONE rAF loop. It reads every
 *      value it needs first, then writes — no interleaved read/write, so
 *      nothing forces a synchronous layout mid-frame.
 *   2. Nothing in the scroll path calls getBoundingClientRect(). The hero's
 *      document position is measured once and re-measured only on resize.
 *   3. Nothing here interpolates over time, so nothing is tied to a 16.67ms
 *      frame budget: the parallax is a pure function of scroll position, so
 *      it lands on the identical value whether the display refreshes 60 or
 *      120 times a second. Where a value *is* animated, it is animated by
 *      CSS on transform/opacity only, off the main thread.
 *   4. Every listener that can fire during a scroll or a touch is passive.
 *   5. will-change is set only while an element is actually animating and
 *      cleared on transitionend.
 */
(function () {
  "use strict";

  var root = document.documentElement;
  var body = document.body;

  var reducedMotion = false;
  try {
    reducedMotion = window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch (e) {
    reducedMotion = false;
  }

  // Desktop = the width at which the drawer stops and the mega menu starts;
  // must match the `@media (max-width: 899px)` block in style.css.
  var mqDesktop = window.matchMedia("(min-width: 900px)");
  var mqFinePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
  function hoverMode() { return mqDesktop.matches && mqFinePointer.matches; }

  function isKeyboardFocus(el) {
    // :focus-visible is what separates "tabbed to" from "clicked on"; a
    // browser without it simply doesn't get focus-to-open (click still works).
    try { return el.matches(":focus-visible"); } catch (e) { return false; }
  }

  // =====================================================================
  // Mega menu (desktop hover-reveal / mobile accordion)
  // =====================================================================
  var siteNav = document.getElementById("siteNav");
  var megaItems = Array.prototype.slice.call(
    document.querySelectorAll(".nav-item--mega"));
  var openItem = null;
  var openTimer = 0;
  var closeTimer = 0;
  // Escape returns focus to the trigger; without this guard that programmatic
  // focus would satisfy :focus-visible and immediately reopen what the user
  // just dismissed.
  var suppressFocusOpen = false;

  // Hover intent. OPEN_DELAY stops the panel flashing open as the cursor
  // merely crosses the bar; CLOSE_DELAY is what lets a diagonal move from
  // the nav item down into the panel survive. Once a panel is already open,
  // moving to a sibling switches instantly — that is what makes Apple's bar
  // feel decisive rather than sticky.
  var OPEN_DELAY = 130;
  var CLOSE_DELAY = 220;

  function clearTimers() {
    if (openTimer) { clearTimeout(openTimer); openTimer = 0; }
    if (closeTimer) { clearTimeout(closeTimer); closeTimer = 0; }
  }

  function setItemOpen(item, open) {
    if (!item) return;
    var btn = item.querySelector(".nav-link--mega");
    item.classList.toggle("is-open", open);
    if (btn) btn.setAttribute("aria-expanded", open ? "true" : "false");
  }

  function openMega(item) {
    clearTimers();
    if (openItem && openItem !== item) setItemOpen(openItem, false);
    openItem = item;
    setItemOpen(item, true);
  }

  function closeMega(item) {
    clearTimers();
    setItemOpen(item, false);
    if (openItem === item) openItem = null;
  }

  function closeAllMega() {
    clearTimers();
    megaItems.forEach(function (it) { setItemOpen(it, false); });
    openItem = null;
  }

  megaItems.forEach(function (item) {
    var btn = item.querySelector(".nav-link--mega");
    if (!btn) return;

    btn.addEventListener("click", function (e) {
      e.preventDefault();
      if (item.classList.contains("is-open")) closeMega(item);
      else openMega(item);
    });

    // Keyboard: tabbing onto the trigger reveals its panel, so the grouped
    // links are reachable in DOM order without any extra key. (Closed panels
    // are visibility:hidden in CSS, which keeps them out of the tab order.)
    btn.addEventListener("focus", function () {
      if (suppressFocusOpen) return;
      if (isKeyboardFocus(btn)) openMega(item);
    });

    // Focus leaving the whole item (trigger + panel) closes it.
    item.addEventListener("focusout", function (e) {
      var to = e.relatedTarget;
      if (!to || !item.contains(to)) {
        if (item.classList.contains("is-open") && !item.matches(":hover")) {
          closeMega(item);
        }
      }
    });

    item.addEventListener("mouseenter", function () {
      if (!hoverMode()) return;
      clearTimers();
      if (openItem && openItem !== item) {
        openMega(item);            // already browsing the bar: switch at once
      } else if (!openItem) {
        openTimer = setTimeout(function () { openMega(item); }, OPEN_DELAY);
      }
    });

    item.addEventListener("mouseleave", function () {
      if (!hoverMode()) return;
      if (openTimer) { clearTimeout(openTimer); openTimer = 0; }
      if (!item.classList.contains("is-open")) return;
      closeTimer = setTimeout(function () { closeMega(item); }, CLOSE_DELAY);
    });

    // Following a link inside the panel should not leave it hanging open
    // when the browser restores this page from the back/forward cache.
    item.querySelectorAll(".mega-link").forEach(function (a) {
      a.addEventListener("click", function () { closeMega(item); });
    });
  });

  // =====================================================================
  // Mobile drawer
  // =====================================================================
  var navToggle = document.getElementById("navToggle");
  var navScrim = document.getElementById("navScrim");
  var drawerOpen = false;
  var lockedScrollY = 0;

  function lockScroll() {
    lockedScrollY = window.scrollY || window.pageYOffset || 0;
    body.style.position = "fixed";
    body.style.top = -lockedScrollY + "px";
    body.style.left = "0";
    body.style.right = "0";
    body.style.width = "100%";
  }

  function unlockScroll() {
    body.style.position = "";
    body.style.top = "";
    body.style.left = "";
    body.style.right = "";
    body.style.width = "";
    // html.js sets scroll-behavior:smooth; restoring the position must not
    // become a visible animated scroll back to where the user already was.
    var prev = root.style.scrollBehavior;
    root.style.scrollBehavior = "auto";
    window.scrollTo(0, lockedScrollY);
    root.style.scrollBehavior = prev;
  }

  function setDrawer(open) {
    if (open === drawerOpen) return;
    drawerOpen = open;
    root.classList.toggle("nav-open", open);
    if (navToggle) navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) {
      lockScroll();
      // On mobile the panels are accordions; start with the section that
      // contains the current page already expanded.
      var current = siteNav && siteNav.querySelector(".mega-link.is-current");
      var host = current && current.closest(".nav-item--mega");
      if (host) setItemOpen(host, true);
    } else {
      unlockScroll();
      closeAllMega();
    }
  }

  if (navToggle && siteNav) {
    navToggle.addEventListener("click", function () { setDrawer(!drawerOpen); });
    if (navScrim) {
      navScrim.addEventListener("click", function () { setDrawer(false); });
    }
    // Any real navigation closes the drawer.
    siteNav.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () { setDrawer(false); });
    });
    // Growing past the drawer breakpoint must not leave the body locked.
    var onBreakpoint = function () { if (mqDesktop.matches) setDrawer(false); };
    if (mqDesktop.addEventListener) mqDesktop.addEventListener("change", onBreakpoint);
    else if (mqDesktop.addListener) mqDesktop.addListener(onBreakpoint);
  }

  // =====================================================================
  // Language switcher dropdown
  // =====================================================================
  var langToggle = document.getElementById("langToggle");
  var langSwitch = langToggle && langToggle.closest(".lang-switch");
  function closeLang() {
    if (!langSwitch) return;
    langSwitch.classList.remove("open");
    langToggle.setAttribute("aria-expanded", "false");
  }
  if (langToggle && langSwitch) {
    langToggle.addEventListener("click", function (e) {
      e.stopPropagation();
      var open = langSwitch.classList.toggle("open");
      langToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // ---- one shared document-level dismissal path -----------------------
  document.addEventListener("click", function (e) {
    if (langSwitch && !langSwitch.contains(e.target)) closeLang();
    // Only on the desktop bar: inside the mobile drawer the panels are
    // accordions, and collapsing one because the user tapped the drawer's
    // own padding would just feel broken.
    if (mqDesktop.matches && openItem && !openItem.contains(e.target)) closeAllMega();
  });

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape" && e.key !== "Esc") return;
    closeLang();
    if (openItem) {
      var btn = openItem.querySelector(".nav-link--mega");
      closeAllMega();
      if (btn) {
        suppressFocusOpen = true;
        btn.focus();
        suppressFocusOpen = false;
      }
      return;
    }
    if (drawerOpen) {
      setDrawer(false);
      if (navToggle) navToggle.focus();
    }
  });

  // =====================================================================
  // Theme toggle: dark (flagship default) <-> light, persisted in
  // localStorage. The inline boot script in site_common.py's page() shell
  // already applied the stored theme before first paint; this just handles
  // the toggle itself. A legacy stored "system" value reads as dark.
  //
  // STORAGE_KEY MUST MATCH the key that boot script reads. It did not, for
  // as long as the aurora-corvus rename has been live: the boot script was
  // renamed and this was left on the old name, so the toggle wrote a key
  // nothing read back. A visitor who chose light got a dark flash on every
  // single page load — the flash the boot script exists to prevent — and
  // nothing anywhere errored. Both sides now name both constants, so
  // grepping either one turns up the other.
  //
  // LEGACY_STORAGE_KEY is that old name. Anyone on light right now has
  // their choice stored under it, so it is read as a fallback and migrated
  // (write the new key, then drop the old one) rather than orphaned, which
  // would silently reset them. The remove only runs if the write did not
  // throw. Migration is idempotent and happens in whichever of the two
  // scripts runs first — normally the boot script, one paint earlier.
  // =====================================================================
  var themeToggle = document.getElementById("themeToggle");
  var STORAGE_KEY = "aurora-corvus-theme";
  var LEGACY_STORAGE_KEY = "glimpse-alpha-wiki-theme";

  function applyTheme(mode) {
    root.setAttribute("data-theme", mode === "light" ? "light" : "dark");
  }

  /* The stored theme, "light"/"dark", or null when nothing valid is stored.
     Every localStorage touch is guarded: Safari private mode and blocked
     site data both THROW on access rather than returning null. */
  function storedMode() {
    try {
      var s = localStorage.getItem(STORAGE_KEY);
      if (s === "light" || s === "dark") return s;
      var legacy = localStorage.getItem(LEGACY_STORAGE_KEY);
      if (legacy === "light" || legacy === "dark") {
        try {
          localStorage.setItem(STORAGE_KEY, legacy);
          localStorage.removeItem(LEGACY_STORAGE_KEY);
        } catch (e) {
          /* read-only storage: still honour the value for this page load */
        }
        return legacy;
      }
    } catch (e) {
      /* storage unavailable */
    }
    return null;
  }

  function currentMode() {
    return storedMode() === "light" ? "light" : "dark";
  }

  applyTheme(currentMode());

  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      var next = currentMode() === "dark" ? "light" : "dark";
      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch (e) {
        /* private browsing / storage disabled: theme just won't persist */
      }
      applyTheme(next);
    });
  }

  // =====================================================================
  // Scroll-driven chrome — the single rAF loop
  // =====================================================================
  var header = document.querySelector(".site-header");
  var hero = document.querySelector(".hero");
  var heroTop = 0;
  var heroHeight = 0;
  var scrolledState = null;
  var lastParallax = null;
  var framePending = false;

  function clamp01(v) { return v < 0 ? 0 : (v > 1 ? 1 : v); }

  function measureHero() {
    if (!hero) return;
    // The only layout read in this module, and it never happens inside the
    // scroll path — only at startup and on resize/orientation change.
    var rect = hero.getBoundingClientRect();
    heroTop = rect.top + (window.scrollY || window.pageYOffset || 0);
    heroHeight = rect.height;
  }

  // ---------------------------------------------------------------------
  // Film (home page only): a pinned stage whose six scenes are driven by
  // scroll position. Same contract as everything else in this file — the
  // only thing written per frame is a handful of unitless custom properties,
  // and every CSS rule that consumes them moves transform/opacity alone.
  //
  // The film is an ENHANCEMENT. When it does not run (JS off, reduced
  // motion, markup absent) style.css lays the identical markup out as a
  // static vertical gallery, so there is no state in which a visitor sees a
  // sequence stuck on frame 0.
  // ---------------------------------------------------------------------
  var filmTrack = document.getElementById("filmTrack");
  var filmStage = document.getElementById("filmStage");
  var filmScenes = (filmTrack && filmStage && !reducedMotion)
    ? Array.prototype.slice.call(filmStage.querySelectorAll("[data-film-scene]"))
    : [];
  var filmTop = 0;
  var filmSpan = 1;
  var filmStageH = 0;
  var filmP = -1;
  var filmLive = null;

  // Per scene: [start, end] in overall film progress, plus the fade-in and
  // fade-out lengths (also in progress units).
  //
  // The beats do NOT overlap. They were cross-dissolved at first and it
  // looked wrong for a specific reason: every scene here carries type, so a
  // 50/50 dissolve of two of them is a double exposure — the wordmark
  // printed across the app's own UI — not a transition. Each beat now fades
  // out completely before the next fades in, leaving a ~0.005 gap (about
  // 25px of scroll) of plain night sky between them. That reads as a cut,
  // which is what a product film actually does.
  var FILM_BEATS = [
    { a: 0.000, b: 0.110, fi: 0,     fo: 0.040 },  // 1 mark + wordmark
    { a: 0.115, b: 0.320, fi: 0.040, fo: 0.035 },  // 2 the app arrives
    { a: 0.325, b: 0.530, fi: 0.035, fo: 0.035 },  // 3 surfaces fan apart
    { a: 0.535, b: 0.740, fi: 0.035, fo: 0.035 },  // 4 the update
    { a: 0.745, b: 0.930, fi: 0.035, fo: 0.035 },  // 5 the sheet + its blur
    { a: 0.935, b: 1.000, fi: 0.040, fo: 0     }   // 6 sign-off
  ];

  function measureFilm() {
    if (!filmScenes.length) return;
    var rect = filmTrack.getBoundingClientRect();
    filmTop = rect.top + (window.scrollY || window.pageYOffset || 0);
    filmStageH = filmStage.offsetHeight;
    filmSpan = Math.max(1, rect.height - filmStageH);
  }

  // A ramp of length 0 means "no fade on this edge" rather than a divide by
  // zero — that is what keeps the opening beat fully opaque at scroll 0.
  function ramp(x, d) { return d > 0 ? clamp01(x / d) : 1; }

  // Writes only when the value actually moved. Most frames touch two scenes;
  // the other four are clamped at their end values and cost nothing.
  function setSceneVar(el, name, key, value) {
    if (el[key] !== undefined && Math.abs(el[key] - value) < 0.0015) return;
    el[key] = value;
    el.style.setProperty(name, value.toFixed(4));
  }

  function filmFrame(y, vh) {
    if (!filmScenes.length) return;
    var live = (filmTop - y) < vh &&
               (filmTop + filmStageH + filmSpan - y) > 0;
    if (live !== filmLive) {
      filmLive = live;
      filmStage.classList.toggle("is-live", live);
    }
    var p = clamp01((y - filmTop) / filmSpan);
    if (p === filmP) return;
    filmP = p;
    setSceneVar(filmStage, "--p", "_filmP", p);
    for (var i = 0; i < filmScenes.length; i++) {
      var b = FILM_BEATS[i];
      if (!b) continue;
      var el = filmScenes[i];
      var t = clamp01((p - b.a) / (b.b - b.a));
      setSceneVar(el, "--t", "_filmT", t);
      // easeOutExpo, for the beats that need to land with weight.
      setSceneVar(el, "--e", "_filmE", t >= 1 ? 1 : 1 - Math.pow(2, -9 * t));
      setSceneVar(el, "--o", "_filmO",
                  Math.min(ramp(p - b.a, b.fi), ramp(b.b - p, b.fo)));
    }
  }

  function frame() {
    framePending = false;

    // --- read phase (no writes above this line) ---
    var y = window.scrollY || window.pageYOffset || 0;
    var vh = window.innerHeight;

    // --- write phase ---
    if (header) {
      var scrolled = y > 24;
      if (scrolled !== scrolledState) {
        scrolledState = scrolled;
        header.classList.toggle("is-scrolled", scrolled);
      }
    }

    if (hero && !reducedMotion) {
      var top = heroTop - y;
      if (top < vh + 240 && top + heroHeight > -240) {
        var offset = Math.max(-24, Math.min(24, top * -0.06));
        // Quantise to 0.1px: below that nothing is visible, and skipping the
        // write skips a style invalidation on most frames.
        offset = Math.round(offset * 10) / 10;
        if (offset !== lastParallax) {
          lastParallax = offset;
          hero.style.setProperty("--parallax", String(offset));
        }
      }
    }

    filmFrame(y, vh);
  }

  function requestFrame() {
    if (framePending) return;
    framePending = true;
    window.requestAnimationFrame(frame);
  }

  function measureAll() {
    measureHero();
    measureFilm();
  }

  if (header || hero || filmScenes.length) {
    measureAll();
    frame();
    window.addEventListener("scroll", requestFrame, { passive: true });
    window.addEventListener("resize", function () {
      measureAll();
      requestFrame();
    }, { passive: true });
    window.addEventListener("orientationchange", function () {
      measureAll();
      requestFrame();
    }, { passive: true });
    // The stage is sized in svh and the frames carry width/height, so nothing
    // here reflows as images arrive — but re-measure once after load anyway,
    // since web-font metrics can still nudge the document above the film.
    window.addEventListener("load", function () {
      measureAll();
      requestFrame();
    });
  }

  // =====================================================================
  // Scroll-entrance reveal
  // Progressive enhancement only: <html class="js"> is added by the inline
  // script in site_common.py's page() shell, before any of this runs. If
  // this script never executes (blocked, errors, disabled), the CSS never
  // switches .reveal into its hidden starting state, so content just stays
  // visible with no animation - see the reduced-motion block in style.css.
  // =====================================================================
  if (!reducedMotion) {
    // Elements present in the server-rendered HTML at load time. Content
    // injected later by recipes.js/changelog.js (grid cards, modal body,
    // guide panes) is intentionally not covered here - it renders straight
    // to its normal visible state, which is correct since it wasn't on
    // screen yet for a scroll-entrance to make sense of.
    // The home page's .film is excluded: it drives its own scenes from
    // scroll position, and letting the reveal system park it at opacity 0
    // until it intersects would leave the whole page blank on load.
    var REVEAL_SELECTOR = [
      "main > .hero", "main > section:not(.film)",
      "main > .card", "main > .toc",
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

    // will-change is promoted per element only for the ~0.9s its transition
    // is actually running, then dropped. Declaring it in CSS for every
    // .reveal on the page (which is what this used to do) leaves a
    // composited layer behind for every card, list item and heading — on the
    // recipes and changelog pages that is hundreds of layers held for the
    // lifetime of the page, which costs far more than it saves.
    function release(e) {
      if (e.target !== this) return;
      this.style.willChange = "";
      this.removeEventListener("transitionend", release);
    }

    if ("IntersectionObserver" in window && targets.length) {
      var io = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (!entry.isIntersecting) return;
            var el = entry.target;
            el.style.willChange = "opacity, transform";
            el.addEventListener("transitionend", release);
            el.classList.add("is-visible");
            io.unobserve(el);
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
  }
})();
