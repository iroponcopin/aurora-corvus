(function () {
  "use strict";

  var LANG = window.SITE_LANG || "ja";
  var STR = window.SITE_STRINGS || {};
  // This page always lives at depth 1 (…/recipes/index.html). Every
  // non-Japanese language adds one extra directory level (/<lang>/…), so the
  // path back to the shared, language-neutral data/ and assets/ folders is
  // one level deeper for those. Mirrors site_common.py's _levels_to_root().
  var LEVELS = 1 + (LANG === "ja" ? 0 : 1);
  var ROOT_PREFIX = new Array(LEVELS + 1).join("../");
  var DATA_URL = ROOT_PREFIX + "data/recipes.json";
  var OVERLAY_URL = ROOT_PREFIX + "data/recipes." + LANG + ".json";
  var IMG_BASE = ROOT_PREFIX + "assets/img/recipes/";

  var state = { master: null, overlay: null, activeTab: "all", query: "" };

  // Must mirror the Python-side search_norm() (see tools/gen_recipe_sheet.py
  // / scripts/extract_recipes.py): lowercase, fullwidth ASCII -> halfwidth,
  // fullwidth space -> halfwidth, katakana -> hiragana. Only meaningfully
  // affects Japanese search blobs; harmless no-op for other scripts.
  function norm(s) {
    s = (s || "").toLowerCase();
    var out = [];
    for (var i = 0; i < s.length; i++) {
      var o = s.codePointAt(i);
      if (o >= 0xff01 && o <= 0xff5e) out.push(String.fromCodePoint(o - 0xfee0));
      else if (o === 0x3000) out.push(" ");
      else if (o >= 0x30a1 && o <= 0x30f6) out.push(String.fromCodePoint(o - 0x60));
      else out.push(s[i]);
    }
    return out.join("");
  }

  function escapeHtml(s) {
    var div = document.createElement("div");
    div.textContent = s == null ? "" : String(s);
    return div.innerHTML;
  }

  // ---- language-aware accessors --------------------------------------
  // For ja: name = master JA name, secondary = master EN name.
  // For en: name = master EN name, secondary = none.
  // For any other lang: name = overlay translated name, secondary = master EN name.
  function itemMeta(itemId) {
    var m = state.master.items[itemId];
    if (!m) return { name: itemId, secondary: null, tex: null };
    var ja = m[0], en = m[1], tex = m[2];
    if (LANG === "ja") return { name: ja, secondary: en && en !== ja ? en : null, tex: tex };
    if (LANG === "en") return { name: en, secondary: null, tex: tex };
    var translated = state.overlay && state.overlay.items && state.overlay.items[itemId];
    return { name: translated || en || ja, secondary: en && en !== translated ? en : null, tex: tex };
  }

  function catName(index) {
    if (LANG === "ja") return state.master.cats[index][0];
    if (state.overlay && state.overlay.cat_names && state.overlay.cat_names[index]) {
      return state.overlay.cat_names[index];
    }
    return state.master.cats[index][0];
  }

  function howtoTopics() {
    if (LANG === "ja") return state.master.guides || [];
    if (state.overlay && state.overlay.howto) return state.overlay.howto;
    return state.master.guides || [];
  }

  function itemImg(itemId, size) {
    size = size || 32;
    var meta = itemMeta(itemId);
    if (!meta.tex) {
      return (
        '<span style="width:' + size + "px;height:" + size + "px;display:inline-flex;" +
        "align-items:center;justify-content:center;background:var(--bg-sunken);" +
        'border-radius:4px;font-size:10px;color:var(--text-muted);">?</span>'
      );
    }
    var src = IMG_BASE + meta.tex + ".png";
    return (
      '<img src="' + src + '" width="' + size + '" height="' + size +
      '" alt="' + escapeHtml(meta.name) + '" loading="lazy">'
    );
  }

  function itemName(itemId) {
    return itemMeta(itemId).name;
  }

  // ---------------------------------------------------------------- tabs --
  function tabButton(key, label, iconItemId, count) {
    var icon = iconItemId ? itemImg(iconItemId, 18) : "";
    var countHtml = count != null ? '<span class="tab-btn__count">' + count + "</span>" : "";
    return (
      '<button class="tab-btn" type="button" role="tab" data-tab="' + key +
      '" aria-selected="' + (state.activeTab === key) + '">' +
      icon + "<span>" + escapeHtml(label) + "</span>" + countHtml + "</button>"
    );
  }

  function renderTabs() {
    var tabs = document.getElementById("recipeTabs");
    var html = tabButton("all", STR.tabAll || "All", null, state.master.total);
    state.master.cats.forEach(function (c, i) {
      html += tabButton(String(i), catName(i), c[1], c[2]);
    });
    if (state.master.guides && state.master.guides.length) {
      html += tabButton("guides", STR.tabGuides || "How-to", null, null);
    }
    tabs.innerHTML = html;
    tabs.querySelectorAll(".tab-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        state.activeTab = btn.dataset.tab;
        history.replaceState(null, "", "#" + state.activeTab);
        renderAll();
      });
    });
  }

  // --------------------------------------------------------------- grid --
  function currentCards() {
    var cards = state.master.cards;
    if (state.activeTab !== "all" && state.activeTab !== "guides") {
      var idx = parseInt(state.activeTab, 10);
      cards = cards.filter(function (c) {
        return c[0] === idx;
      });
    }
    var q = norm(state.query);
    if (q) {
      cards = cards.filter(function (c) {
        if (c[5].indexOf(q) !== -1) return true;
        // Fall back to matching the rendered (possibly translated) name too,
        // since the precomputed search blob (c[5]) is Japanese-only.
        return norm(itemName(c[1])).indexOf(q) !== -1;
      });
    }
    return cards;
  }

  function renderGrid() {
    var grid = document.getElementById("recipeGrid");
    var countEl = document.getElementById("recipeCount");
    var emptyEl = document.getElementById("recipeEmpty");
    var cards = currentCards();
    countEl.hidden = false;
    countEl.textContent = cards.length + " " + (STR.countSuffix || "");
    emptyEl.hidden = cards.length !== 0;
    grid.hidden = cards.length === 0;

    grid.innerHTML = cards
      .map(function (c) {
        var itemId = c[1];
        return (
          '<button class="recipe-card" type="button" data-item="' + itemId + '">' +
          itemImg(itemId, 32) +
          '<span class="recipe-card__name">' + escapeHtml(itemName(itemId)) + "</span></button>"
        );
      })
      .join("");
    grid.querySelectorAll(".recipe-card").forEach(function (btn) {
      btn.addEventListener("click", function () {
        openModal(btn.dataset.item);
      });
    });
  }

  function findCard(itemId) {
    for (var i = 0; i < state.master.cards.length; i++) {
      if (state.master.cards[i][1] === itemId) return state.master.cards[i];
    }
    return null;
  }

  // -------------------------------------------------------------- modal --
  function openModal(itemId) {
    var card = findCard(itemId);
    var backdrop = document.getElementById("recipeModalBackdrop");
    var body = document.getElementById("recipeModalBody");
    var meta = itemMeta(itemId);

    var html = '<h3 id="recipeModalTitle">' + escapeHtml(meta.name) + "</h3>";
    if (meta.secondary) html += '<p class="card__meta">' + escapeHtml(meta.secondary) + "</p>";

    if (card && card[2]) {
      var g = card[2];
      var count = card[3] || 1;
      html +=
        '<div class="craft-grid">' +
        g
          .map(function (cid) {
            if (!cid) return '<div class="slot"></div>';
            return (
              '<div class="slot" title="' + escapeHtml(itemName(cid)) + '">' + itemImg(cid, 28) + "</div>"
            );
          })
          .join("") +
        "</div>";
      html += '<div class="craft-arrow">↓</div>';
      html +=
        '<div class="craft-result">' +
        itemImg(itemId, 40) +
        "<div><strong>" + escapeHtml(meta.name) + "</strong>" + (count > 1 ? " ×" + count : "") + "</div></div>";
    } else if (card && card[4]) {
      html += '<p class="callout callout--info"><strong>' + escapeHtml(STR.howToObtain || "") + "</strong> " + escapeHtml(card[4]) + "</p>";
    } else {
      html += '<p class="card__meta">' + escapeHtml(STR.noRecipeInfo || "") + "</p>";
    }

    body.innerHTML = html;
    backdrop.classList.add("open");
  }

  function closeModal() {
    document.getElementById("recipeModalBackdrop").classList.remove("open");
  }

  // ------------------------------------------------------------- guides --
  function renderGuides() {
    var pane = document.getElementById("guidePane");
    pane.innerHTML = howtoTopics().map(renderGuideTopic).join("");
  }

  function renderGuideTopic(g) {
    return (
      '<div class="guide-topic">' +
      "<h2>" + itemImg(g.icon, 24) + " " + escapeHtml(g.title) + "</h2>" +
      '<p class="guide-topic__lede">' + g.lede + "</p>" +
      (g.sections || []).map(renderGuideSection).join("") +
      "</div>"
    );
  }

  function renderGuideSection(sec) {
    var html = '<div class="guide-section"><h4>' + escapeHtml(sec.title) + "</h4>";
    if (sec.goal) html += '<p class="guide-goal">' + sec.goal + "</p>";
    if (sec.diagram) html += renderDiagram(sec.diagram);
    if (sec.io) html += renderIo(sec.io);
    if (sec.steps && sec.steps.length) {
      html +=
        '<ol class="steps">' +
        sec.steps.map(function (s) { return "<li>" + s + "</li>"; }).join("") +
        "</ol>";
    }
    if (sec.notes && sec.notes.length) {
      html +=
        '<div class="callout"><ul>' +
        sec.notes.map(function (s) { return "<li>" + s + "</li>"; }).join("") +
        "</ul></div>";
    }
    return html + "</div>";
  }

  function renderDiagram(dia) {
    var html = '<div class="diagram">';
    if (dia.caption) html += '<div class="diagram__caption">' + escapeHtml(dia.caption) + "</div>";
    (dia.rows || []).forEach(function (row) {
      html += '<div class="diagram__row">';
      row.forEach(function (cell) {
        if (!cell) {
          html += '<div class="diagram__cell"></div>';
        } else if (cell[0] === "i") {
          html +=
            '<div class="diagram__cell diagram__cell--icon">' +
            itemImg(cell[1], 28) +
            (cell[2] ? '<span class="diagram__cell-label">' + escapeHtml(cell[2]) + "</span>" : "") +
            "</div>";
        } else if (cell[0] === "a") {
          html += '<div class="diagram__cell diagram__arrow">' + escapeHtml(cell[1]) + "</div>";
        } else if (cell[0] === "n") {
          html += '<div class="diagram__cell diagram__text">' + escapeHtml(cell[1]) + "</div>";
        }
      });
      html += "</div>";
    });
    return html + "</div>";
  }

  function ioList(label, items) {
    if (!items || !items.length) return "";
    var html = '<div class="io-list"><h5>' + escapeHtml(label) + "</h5>";
    items.forEach(function (pair) {
      html += '<span class="io-chip">' + itemImg(pair[0], 18) + escapeHtml(pair[1]) + "</span>";
    });
    return html + "</div>";
  }

  function renderIo(io) {
    return '<div class="io-lists">' + ioList(STR.ioIn || "In", io["in"]) + ioList(STR.ioOut || "Out", io["out"]) + "</div>";
  }

  // -------------------------------------------------------------- shell --
  function renderAll() {
    document.querySelectorAll("#recipeTabs .tab-btn").forEach(function (btn) {
      btn.setAttribute("aria-selected", btn.dataset.tab === state.activeTab ? "true" : "false");
    });
    var isGuides = state.activeTab === "guides";
    var guidePane = document.getElementById("guidePane");
    guidePane.hidden = !isGuides;
    document.getElementById("recipeGrid").hidden = isGuides;
    document.getElementById("recipeCount").hidden = isGuides;
    var searchInput = document.getElementById("recipeSearch");
    var filterBar = searchInput && searchInput.closest(".filter-bar");
    if (filterBar) filterBar.hidden = isGuides;
    document.getElementById("recipeEmpty").hidden = true;

    if (isGuides) {
      if (!guidePane.dataset.rendered) {
        renderGuides();
        guidePane.dataset.rendered = "1";
      }
    } else {
      renderGrid();
    }
  }

  function init() {
    if (location.hash) {
      var h = decodeURIComponent(location.hash.slice(1));
      if (/^\d+$/.test(h) && state.master.cats[parseInt(h, 10)]) {
        state.activeTab = h;
      } else if (h === "guides") {
        state.activeTab = "guides";
      }
    }

    document.getElementById("recipeApp").hidden = false;
    renderTabs();
    renderAll();

    document.getElementById("recipeSearch").addEventListener("input", function (e) {
      state.query = e.target.value;
      if (state.activeTab === "guides") state.activeTab = "all";
      renderAll();
    });
    document.getElementById("recipeModalClose").addEventListener("click", closeModal);
    document.getElementById("recipeModalBackdrop").addEventListener("click", function (e) {
      if (e.target === this) closeModal();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeModal();
    });
  }

  function fetchJson(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status + " for " + url);
      return r.json();
    });
  }

  var loads = [fetchJson(DATA_URL)];
  if (LANG !== "ja") {
    // Overlay is best-effort: if a language's translation isn't ready yet,
    // fall back to Japanese/English names rather than failing the page.
    loads.push(fetchJson(OVERLAY_URL).catch(function () { return null; }));
  }

  Promise.all(loads)
    .then(function (results) {
      state.master = results[0];
      state.overlay = results[1] || null;
      init();
    })
    .catch(function (err) {
      document.getElementById("recipeApp").hidden = false;
      document.getElementById("recipeGrid").innerHTML =
        '<p class="empty-state">' + escapeHtml(STR.loadError || "Failed to load.") + "</p>";
      console.error(err);
    });
})();
