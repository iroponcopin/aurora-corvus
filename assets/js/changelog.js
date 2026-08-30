/* Changelog behaviour: expand a release, reveal a group's older releases, and
   the search / mod / type filters the page already had.

   THE ROWS WORK WITHOUT THIS FILE.
   Every detail panel is plain markup with `hidden` on it, and every row is a
   real <button aria-expanded aria-controls>. If this script fails to load, the
   page is a readable list of versions and dates -- it does not become a page of
   dead buttons. That is why the panels are not built in JS.

   FILTERING HIDES GROUPS TOO.
   A filter that hides every release in a series but leaves the series heading
   and its summary sitting above an empty gap looks like a rendering bug. So a
   group whose visible release count reaches zero hides itself, and when
   everything is hidden the empty-state line appears. */
(function () {
  "use strict";

  var root = document.getElementById("changelogGroups");
  if (!root) return;

  var groups = Array.prototype.slice.call(root.querySelectorAll(".cl__group"));
  var releases = Array.prototype.slice.call(root.querySelectorAll(".cl__release"));
  var searchInput = document.getElementById("changelogSearch");
  var emptyNote = document.getElementById("changelogEmpty");
  // The "first N" cut is defined ONCE, in build_changelog.py, and travels here
  // as data-cut. Hardcoding it in both places is how the two silently drift --
  // this file said 10 while the generator said 8 for exactly one commit.
  var CUT = parseInt(root.dataset.cut, 10) || 8;
  var activeMods = new Set();
  var activeTypes = new Set();

  /* ---------------------------------------------------------- expand a row */

  root.addEventListener("click", function (event) {
    var row = event.target.closest(".cl__row");
    if (!row || !root.contains(row)) return;
    var panel = document.getElementById(row.getAttribute("aria-controls"));
    if (!panel) return;
    var open = row.getAttribute("aria-expanded") === "true";
    row.setAttribute("aria-expanded", open ? "false" : "true");
    panel.hidden = open;
  });

  /* ------------------------------------------------- a group's "Show more" */

  groups.forEach(function (group) {
    var more = group.querySelector(".cl__more");
    if (!more) return;
    more.addEventListener("click", function () {
      var expanded = more.getAttribute("aria-expanded") === "true";
      more.setAttribute("aria-expanded", expanded ? "false" : "true");
      more.textContent = expanded ? more.dataset.more : more.dataset.less;
      // `overflow` is this group's own state; the filter pass below is the only
      // other thing that may hide a release, and it owns `filtered`. Two flags,
      // so neither can silently undo the other.
      group.dataset.overflow = expanded ? "collapsed" : "expanded";
      applyFilters();
    });
    group.dataset.overflow = "collapsed";
  });

  /* ------------------------------------------------------------- filtering */

  function wireChips(selector, set) {
    document.querySelectorAll(selector).forEach(function (chip) {
      chip.addEventListener("click", function () {
        var key = chip.dataset.filterMod || chip.dataset.filterType;
        if (set.has(key)) {
          set.delete(key);
          chip.setAttribute("aria-pressed", "false");
        } else {
          set.add(key);
          chip.setAttribute("aria-pressed", "true");
        }
        applyFilters();
      });
    });
  }

  function matches(el, needle) {
    if (!needle) return true;
    return el.textContent.toLowerCase().indexOf(needle) !== -1;
  }

  function applyFilters() {
    var needle = searchInput ? searchInput.value.trim().toLowerCase() : "";
    var anyVisible = false;

    groups.forEach(function (group) {
      var own = Array.prototype.slice.call(group.querySelectorAll(".cl__release"));
      var shown = 0;
      var limit = group.dataset.overflow === "expanded" ? Infinity : CUT;
      var passedSoFar = 0;

      own.forEach(function (el) {
        var mods = (el.dataset.mods || "").split(/\s+/).filter(Boolean);
        var type = el.dataset.type || "";
        var modOk = activeMods.size === 0 || mods.some(function (m) { return activeMods.has(m); });
        var typeOk = activeTypes.size === 0 || activeTypes.has(type);
        var pass = modOk && typeOk && matches(el, needle);

        // The "first ten" cut counts only releases that PASSED the filter --
        // otherwise filtering could leave a group looking empty while its ten
        // slots were silently spent on hidden rows.
        var withinLimit = pass && passedSoFar < limit;
        if (pass) passedSoFar++;
        el.hidden = !withinLimit;
        if (withinLimit) shown++;
      });

      // Searching should reach history without making people press "Show more"
      // in every series first, so a search reveals matches beyond the cut.
      if (needle && group.dataset.overflow !== "expanded") {
        own.forEach(function (el) {
          var mods = (el.dataset.mods || "").split(/\s+/).filter(Boolean);
          var type = el.dataset.type || "";
          var modOk = activeMods.size === 0 || mods.some(function (m) { return activeMods.has(m); });
          var typeOk = activeTypes.size === 0 || activeTypes.has(type);
          if (modOk && typeOk && matches(el, needle) && el.hidden) {
            el.hidden = false;
            shown++;
          }
        });
      }

      var more = group.querySelector(".cl__more");
      if (more) {
        var total = own.filter(function (el) {
          var mods = (el.dataset.mods || "").split(/\s+/).filter(Boolean);
          var type = el.dataset.type || "";
          var modOk = activeMods.size === 0 || mods.some(function (m) { return activeMods.has(m); });
          var typeOk = activeTypes.size === 0 || activeTypes.has(type);
          return modOk && typeOk && matches(el, needle);
        }).length;
        // Offering "Show more" when there is nothing more to show is a dead
        // control; hide it instead.
        more.hidden = total <= shown;
      }

      group.hidden = shown === 0;
      if (shown > 0) anyVisible = true;
    });

    if (emptyNote) emptyNote.hidden = anyVisible;
  }

  wireChips("[data-filter-mod]", activeMods);
  wireChips("[data-filter-type]", activeTypes);
  if (searchInput) searchInput.addEventListener("input", applyFilters);

  applyFilters();

  /* A deep link like #v3.2 should open that series rather than land on a
     collapsed heading the reader then has to hunt through. */
  if (location.hash) {
    var target = document.querySelector(location.hash);
    if (target && target.classList.contains("cl__group")) {
      var btn = target.querySelector(".cl__more");
      if (btn) btn.click();
      target.scrollIntoView();
    }
  }
})();
