/* V4 announcement page — the music player. TEMPORARY, deleted with the page.
 *
 * Owner's request (2026-09-01): music plays while the V4 tab is open, with a
 * mute button, "the same as the official Honkai: Star Rail page".
 *
 * ── The whole difficulty is the autoplay policy ────────────────────────────
 * No current browser will start AUDIBLE sound before a user gesture. Chrome
 * gates it on its Media Engagement Index, Safari on an explicit gesture,
 * Firefox on a per-site permission. So `audio.play()` on DOMContentLoaded
 * returns a promise that REJECTS for most first-time visitors — and a naive
 * implementation then sits there with a button reading "stop the music" over
 * silence. That is worse than no music: the control lies about the state.
 *
 * What this does instead:
 *   1. Try to play immediately. If the browser allows it (returning visitor,
 *      high engagement), the music is on and the button says so.
 *   2. If it rejects, arm ONE listener for the first real gesture
 *      (pointerdown / keydown / touchstart) and start then. The button
 *      truthfully reads "play the music" in the meantime.
 *   3. The button is authoritative either way: pressing it toggles, and once
 *      the visitor has pressed it their choice is remembered in
 *      localStorage and the auto-start is never attempted again.
 *
 * ── Two more things a page like this gets wrong ───────────────────────────
 *   * Leaving the tab: `visibilitychange` pauses. The owner asked for music
 *     "while the V4 tab is open" — a background tab is not open in the sense
 *     anyone means, and browsers do not stop it for you.
 *   * prefers-reduced-motion is NOT a mute signal, but the OS "reduce" flag
 *     often travels with people who do not want surprises, so auto-start is
 *     skipped there. The button still works: it is a preference, not a ban.
 *
 * Everything degrades to silence if JS is off. The <audio> element carries
 * no `autoplay` attribute precisely so a no-JS visitor gets a page with no
 * sound and no broken control, rather than a control that does nothing.
 */
(function () {
  "use strict";

  var STORAGE_KEY = "corvus.v4teaser.music";
  // No wrapping element on purpose (build_v4_teaser.py explains why), so
  // everything is found from the document and the "scripting is alive" flag
  // goes on <html> rather than on a page wrapper.
  var audio = document.getElementById("v4t-theme");
  var button = document.querySelector("[data-v4t-toggle]");
  var label = document.querySelector("[data-v4t-label]");
  if (!audio || !button || !label) { return; }

  // The page is usable without any of this; only reveal the control once we
  // know scripting is alive, so a no-JS reader never sees a dead button.
  document.documentElement.classList.add("v4t-js");

  var wantsMusic = false;      // the state the button advertises
  var armed = false;           // a first-gesture listener is pending
  var chosen = false;          // the visitor pressed the button themselves

  function readStored() {
    try {
      var v = window.localStorage.getItem(STORAGE_KEY);
      if (v === "on") { return true; }
      if (v === "off") { return false; }
    } catch (err) { /* private window, blocked storage — fall through */ }
    return null;
  }

  function store(on) {
    try {
      window.localStorage.setItem(STORAGE_KEY, on ? "on" : "off");
    } catch (err) { /* nothing to do; the page still works this session */ }
  }

  function paint() {
    button.setAttribute("aria-pressed", wantsMusic ? "true" : "false");
    var text = wantsMusic
      ? button.getAttribute("data-label-on")
      : button.getAttribute("data-label-off");
    label.textContent = text;
    button.setAttribute("aria-label", text);
    button.classList.toggle("is-on", wantsMusic);
  }

  function startAudio() {
    var p = audio.play();
    if (p && typeof p.then === "function") {
      return p;
    }
    return Promise.resolve();
  }

  /** Arm a one-shot listener that starts the music on the first gesture. */
  function armFirstGesture() {
    if (armed || chosen) { return; }
    armed = true;
    var events = ["pointerdown", "keydown", "touchstart"];
    var fire = function () {
      events.forEach(function (name) {
        window.removeEventListener(name, fire, true);
      });
      armed = false;
      if (!wantsMusic || chosen) { return; }
      startAudio().catch(function () {
        // Still refused (rare). Tell the truth on the button.
        wantsMusic = false;
        paint();
      });
    };
    events.forEach(function (name) {
      window.addEventListener(name, fire, { capture: true, once: false, passive: true });
    });
  }

  function turnOn(userInitiated) {
    wantsMusic = true;
    paint();
    startAudio().catch(function () {
      if (userInitiated) {
        // A gesture-driven play() that still fails means the file did not
        // load or the codec is unsupported — do not claim it is playing.
        wantsMusic = false;
        paint();
      } else {
        armFirstGesture();
      }
    });
  }

  function turnOff() {
    wantsMusic = false;
    audio.pause();
    paint();
  }

  button.addEventListener("click", function () {
    chosen = true;
    if (wantsMusic) {
      turnOff();
      store(false);
    } else {
      turnOn(true);
      store(true);
    }
  });

  // Music should follow the tab, not the session: a page left open in a
  // background tab keeps playing otherwise, which is exactly the behaviour
  // people complain about on sites that do this.
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) {
      audio.pause();
    } else if (wantsMusic) {
      startAudio().catch(function () { /* will resume on the next gesture */ });
    }
  });

  // Leaving the page entirely (bfcache included) stops it too.
  window.addEventListener("pagehide", function () { audio.pause(); });

  paint();

  var stored = readStored();
  if (stored === false) {
    // The visitor turned it off on a previous visit. Respect that and never
    // auto-start; the button is still there if they change their mind.
    chosen = true;
    return;
  }

  var reduce = window.matchMedia
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce && stored !== true) {
    // Not a ban — just no surprises. The button works normally.
    return;
  }

  audio.preload = "auto";
  turnOn(false);
}());
