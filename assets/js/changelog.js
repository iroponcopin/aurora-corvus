(function () {
  "use strict";
  var timeline = document.getElementById("changelogTimeline");
  var emptyState = document.getElementById("changelogEmpty");
  var searchInput = document.getElementById("changelogSearch");
  if (!timeline) return;

  var entries = Array.prototype.slice.call(timeline.querySelectorAll(".timeline-entry"));
  var activeMods = new Set();
  var activeTypes = new Set();

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
  wireChips("[data-filter-mod]", activeMods);
  wireChips("[data-filter-type]", activeTypes);

  function applyFilters() {
    var query = (searchInput && searchInput.value || "").trim().toLowerCase();
    var visibleCount = 0;
    entries.forEach(function (el) {
      var mods = (el.dataset.mods || "").split(" ");
      var type = el.dataset.type || "";
      var text = el.textContent.toLowerCase();

      var modOk = activeMods.size === 0 || mods.some(function (m) { return activeMods.has(m); });
      var typeOk = activeTypes.size === 0 || activeTypes.has(type);
      var textOk = !query || text.indexOf(query) !== -1;

      var show = modOk && typeOk && textOk;
      el.hidden = !show;
      if (show) visibleCount++;
    });
    if (emptyState) emptyState.hidden = visibleCount !== 0;
  }

  if (searchInput) {
    searchInput.addEventListener("input", applyFilters);
  }
})();
