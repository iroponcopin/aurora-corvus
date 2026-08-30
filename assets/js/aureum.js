/* ==========================================================================
   Aureum landing page — pinned two-beat hero sequence.

   Deliberately its own small script, not folded into assets/js/main.js:
   this whole page owns its motion stack independently (see assets/css/
   aureum.css's header), the same reasoning the (deleted) V3 teaser's
   v3-teaser.js gave, so nothing here can ever regress the home page's own
   film or any other page's scroll chrome, and vice versa.

   Same technique as the home page's film module (assets/js/main.js) and the
   V3 teaser before it: a single rAF loop reads scroll position once, then
   writes a handful of unitless CSS custom properties that aureum.css turns
   into transform/opacity only — nothing here ever touches a layout-
   triggering property, so the whole sequence runs on the compositor.

   Progressive enhancement: if this script never runs (blocked, JS disabled,
   errors), aureum.css's DEFAULT rules (outside the
   `prefers-reduced-motion: no-preference` block) already lay the same
   markup out as a plain static column — there is no state in which a
   visitor sees the sequence stuck mid-transition.
   ========================================================================== */
(function () {
  "use strict";

  var reducedMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var track = document.getElementById("auTrack");
  var stage = document.getElementById("auStage");
  var scenes = (track && stage && !reducedMotion)
    ? Array.prototype.slice.call(stage.querySelectorAll("[data-au-scene]"))
    : [];
  if (!scenes.length) return;

  var top = 0, span = 1, stageH = 0, p = -1, live = null, framePending = false;

  // Two beats, not overlapping — a small gap of empty stage between them
  // reads as a cut rather than a double exposure (same reasoning as the
  // home film's FILM_BEATS comment and the V3 teaser's BEATS comment).
  var BEATS = [
    { a: 0.000, b: 0.520, fi: 0,    fo: 0.05 },  // 0 — hero (mark + wordmark + tagline)
    { a: 0.540, b: 1.000, fi: 0.05, fo: 0    }   // 1 — headline stat
  ];

  function clamp01(v) { return v < 0 ? 0 : (v > 1 ? 1 : v); }
  function ramp(x, d) { return d > 0 ? clamp01(x / d) : 1; }

  function setVar(el, name, key, value) {
    if (el[key] !== undefined && Math.abs(el[key] - value) < 0.0015) return;
    el[key] = value;
    el.style.setProperty(name, value.toFixed(4));
  }

  function measure() {
    var rect = track.getBoundingClientRect();
    top = rect.top + (window.scrollY || window.pageYOffset || 0);
    stageH = stage.offsetHeight;
    span = Math.max(1, rect.height - stageH);
  }

  function frame() {
    framePending = false;

    // --- read ---
    var y = window.scrollY || window.pageYOffset || 0;
    var vh = window.innerHeight;

    // --- write ---
    var isLive = (top - y) < vh && (top + stageH + span - y) > 0;
    if (isLive !== live) {
      live = isLive;
      stage.classList.toggle("is-live", isLive);
    }
    var np = clamp01((y - top) / span);
    if (np === p) return;
    p = np;
    setVar(stage, "--p", "_p", p);
    for (var i = 0; i < scenes.length; i++) {
      var b = BEATS[i];
      if (!b) continue;
      var el = scenes[i];
      var t = clamp01((p - b.a) / (b.b - b.a));
      setVar(el, "--t", "_t", t);
      setVar(el, "--e", "_e", t >= 1 ? 1 : 1 - Math.pow(2, -9 * t));
      setVar(el, "--o", "_o", Math.min(ramp(p - b.a, b.fi), ramp(b.b - p, b.fo)));
    }
  }

  function requestFrame() {
    if (framePending) return;
    framePending = true;
    window.requestAnimationFrame(frame);
  }

  measure();
  frame();
  window.addEventListener("scroll", requestFrame, { passive: true });
  window.addEventListener("resize", function () { measure(); requestFrame(); }, { passive: true });
  window.addEventListener("orientationchange", function () { measure(); requestFrame(); }, { passive: true });
  window.addEventListener("load", function () { measure(); requestFrame(); });
})();
