/* Changelog behaviour: switch brands, expand a release, reveal a group's older
   releases, and the search / mod / type filters Alpha's history already had.

   THE ROWS WORK WITHOUT THIS FILE.
   Every detail panel is plain markup with `hidden` on it, and every row is a
   real <button aria-expanded aria-controls>. If this script fails to load, the
   page is a readable list of versions and dates -- it does not become a page of
   dead buttons. That is why the panels are not built in JS.

   BRANDS (2026-09-14, owner): 「更新履歴をOUKA、Cherry、Alpha、Aureumを選べる様に
   してください。」 Each brand is a <section class="cl__brand">. Without this file
   they all stay open, one under the other with their own headings; the tab row
   is `hidden` in the markup and only this file reveals it, so nobody without
   the script meets tabs that do nothing. The chosen brand goes into the address
   as ?brand= (Alpha, the default, leaves it clean), so a copied link and the
   language switcher -- which keeps the query -- open the same brand.

   FILTERING HIDES GROUPS TOO.
   A filter that hides every release in a series but leaves the series heading
   and its summary sitting above an empty gap looks like a rendering bug. So a
   group whose visible release count reaches zero hides itself, and when
   everything is hidden the empty-state line appears. */
(function () {
  "use strict";

  var page = document.querySelector(".cl");
  if (!page) return;

  function safeDecode(text) {
    try {
      return decodeURIComponent(text);
    } catch (e) {
      return text;
    }
  }

  /* A deep link like #v3.2 or #cherry-v1.0. document.querySelector("#v3.2")
     THROWS -- ".2" is read as a class selector that starts with a digit -- and
     that took the rest of this file down with it on every such link, so the
     target is looked up by id instead. */
  var hashTarget = window.location.hash
    ? document.getElementById(safeDecode(window.location.hash.slice(1)))
    : null;

  /* --------------------------------------------------------------- brands */

  var tablist = page.querySelector(".cl__brands");
  var tabs = tablist ? Array.prototype.slice.call(tablist.querySelectorAll(".cl__brandTab")) : [];
  var brandPanels = Array.prototype.slice.call(page.querySelectorAll(".cl__brand"));
  var defaultBrand = tablist ? tablist.getAttribute("data-default") : null;

  function hasBrand(brand) {
    return tabs.some(function (tab) { return tab.getAttribute("data-brand") === brand; });
  }

  function selectBrand(brand, options) {
    options = options || {};
    if (!hasBrand(brand)) brand = defaultBrand;
    tabs.forEach(function (tab) {
      var on = tab.getAttribute("data-brand") === brand;
      tab.setAttribute("aria-selected", on ? "true" : "false");
      tab.tabIndex = on ? 0 : -1;
      if (on && options.focus) tab.focus();
    });
    brandPanels.forEach(function (panel) {
      panel.hidden = panel.getAttribute("data-brand") !== brand;
    });
    if (options.remember) {
      try {
        var url = new URL(window.location.href);
        if (brand === defaultBrand) {
          url.searchParams.delete("brand");
        } else {
          url.searchParams.set("brand", brand);
        }
        url.hash = "";
        window.history.replaceState(null, "", url.toString());
      } catch (e) {
        /* An old browser keeps the tab; it just does not write the address. */
      }
    }
  }

  if (tablist && tabs.length && brandPanels.length) {
    brandPanels.forEach(function (panel) {
      panel.setAttribute("role", "tabpanel");
      panel.setAttribute("aria-labelledby", "clTab-" + panel.getAttribute("data-brand"));
    });
    tablist.hidden = false;
    page.classList.add("cl--tabbed");

    tablist.addEventListener("click", function (event) {
      var tab = event.target.closest(".cl__brandTab");
      if (!tab || !tablist.contains(tab)) return;
      selectBrand(tab.getAttribute("data-brand"), { remember: true });
    });

    tablist.addEventListener("keydown", function (event) {
      var index = tabs.indexOf(document.activeElement);
      if (index < 0) return;
      var rtl = window.getComputedStyle(tablist).direction === "rtl";
      var next = null;
      if (event.key === "ArrowRight") next = index + (rtl ? -1 : 1);
      else if (event.key === "ArrowLeft") next = index + (rtl ? 1 : -1);
      else if (event.key === "Home") next = 0;
      else if (event.key === "End") next = tabs.length - 1;
      if (next === null) return;
      event.preventDefault();
      next = (next + tabs.length) % tabs.length;
      selectBrand(tabs[next].getAttribute("data-brand"), { focus: true, remember: true });
    });

    var initial = defaultBrand;
    try {
      var asked = new URL(window.location.href).searchParams.get("brand");
      if (asked && hasBrand(asked)) initial = asked;
    } catch (e) {
      /* no URL API: stay on the default brand */
    }
    // A deep link into a brand's history opens that brand, whatever ?brand= says.
    var hashPanel = hashTarget ? hashTarget.closest(".cl__brand") : null;
    if (hashPanel) initial = hashPanel.getAttribute("data-brand");
    selectBrand(initial);
  }

  /* ---------------------------------------------------------- expand a row */

  page.addEventListener("click", function (event) {
    var row = event.target.closest(".cl__row");
    if (!row || !page.contains(row)) return;
    var panel = document.getElementById(row.getAttribute("aria-controls"));
    if (!panel) return;
    var open = row.getAttribute("aria-expanded") === "true";
    row.setAttribute("aria-expanded", open ? "false" : "true");
    panel.hidden = open;
  });

  /* ------------------------------------ a brand's own groups: "Show more" */

  /* Only Alpha's history has filters; another brand's group just reveals the
     rows past the cut. (No other brand has more than eight releases in a series
     yet, so this is dormant, but a ninth release must not arrive to a dead
     button.) */
  Array.prototype.slice.call(page.querySelectorAll(".cl__groups")).forEach(function (container) {
    var cut = parseInt(container.getAttribute("data-cut"), 10) || 8;
    Array.prototype.slice.call(container.querySelectorAll(".cl__group")).forEach(function (group) {
      var more = group.querySelector(".cl__more");
      if (!more) return;
      more.addEventListener("click", function () {
        var expanded = more.getAttribute("aria-expanded") === "true";
        more.setAttribute("aria-expanded", expanded ? "false" : "true");
        more.textContent = expanded ? more.getAttribute("data-more") : more.getAttribute("data-less");
        Array.prototype.slice.call(group.querySelectorAll(".cl__release")).forEach(function (el, i) {
          if (i >= cut) el.hidden = expanded;
        });
      });
    });
  });

  /* ------------------------------------------------ Alpha's history: filters */

  var root = document.getElementById("changelogGroups");
  if (root) {
    var groups = Array.prototype.slice.call(root.querySelectorAll(".cl__group"));
    var searchInput = document.getElementById("changelogSearch");
    var emptyNote = document.getElementById("changelogEmpty");
    // The "first N" cut is defined ONCE, in build_changelog.py, and travels here
    // as data-cut. Hardcoding it in both places is how the two silently drift --
    // this file said 10 while the generator said 8 for exactly one commit.
    var CUT = parseInt(root.dataset.cut, 10) || 8;
    var activeMods = new Set();
    var activeTypes = new Set();

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

    var wireChips = function (selector, set) {
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
    };

    var matches = function (el, needle) {
      if (!needle) return true;
      return el.textContent.toLowerCase().indexOf(needle) !== -1;
    };

    var passesChips = function (el) {
      var mods = (el.dataset.mods || "").split(/\s+/).filter(Boolean);
      var type = el.dataset.type || "";
      var modOk = activeMods.size === 0 || mods.some(function (m) { return activeMods.has(m); });
      var typeOk = activeTypes.size === 0 || activeTypes.has(type);
      return modOk && typeOk;
    };

    var applyFilters = function () {
      var needle = searchInput ? searchInput.value.trim().toLowerCase() : "";
      var anyVisible = false;

      groups.forEach(function (group) {
        var own = Array.prototype.slice.call(group.querySelectorAll(".cl__release"));
        var shown = 0;
        var limit = group.dataset.overflow === "expanded" ? Infinity : CUT;
        var passedSoFar = 0;

        own.forEach(function (el) {
          var pass = passesChips(el) && matches(el, needle);
          // The "first N" cut counts only releases that PASSED the filter --
          // otherwise filtering could leave a group looking empty while its
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
            if (passesChips(el) && matches(el, needle) && el.hidden) {
              el.hidden = false;
              shown++;
            }
          });
        }

        var more = group.querySelector(".cl__more");
        if (more) {
          var total = own.filter(function (el) {
            return passesChips(el) && matches(el, needle);
          }).length;
          // Offering "Show more" when there is nothing more to show is a dead
          // control; hide it instead.
          more.hidden = total <= shown;
        }

        group.hidden = shown === 0;
        if (shown > 0) anyVisible = true;
      });

      if (emptyNote) emptyNote.hidden = anyVisible;
    };

    wireChips("[data-filter-mod]", activeMods);
    wireChips("[data-filter-type]", activeTypes);
    if (searchInput) searchInput.addEventListener("input", applyFilters);

    applyFilters();
  }

  /* A deep link to a series should open that series rather than land on a
     collapsed heading the reader then has to hunt through. The brand it belongs
     to was already selected above. */
  if (hashTarget && hashTarget.classList.contains("cl__group")) {
    var btn = hashTarget.querySelector(".cl__more");
    if (btn && btn.getAttribute("aria-expanded") !== "true") btn.click();
    hashTarget.scrollIntoView();
  }
})();
