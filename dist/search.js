/* Search bar. Plain English first. Codes are optional. No modal. */
(function () {
  "use strict";

  var logic = window.AlphaLogic;
  var input = document.querySelector(".desk-search input[name='q']");
  var list = document.getElementById("search-list");
  var live = document.getElementById("search-live");
  var form = document.querySelector(".desk-search");
  var index = null;
  var rows = [];
  var active = -1;
  var open = false;

  function setLive(text) {
    if (live) live.textContent = text || "";
  }

  function securities() {
    var node = document.getElementById("alpha-securities");
    if (!node) return [];
    try {
      var data = JSON.parse(node.textContent);
      return Array.isArray(data) ? data : [];
    } catch (err) {
      return [];
    }
  }

  function loadIndex() {
    if (index) return Promise.resolve(index);
    return fetch("/search.json", { headers: { Accept: "application/json" } }).then(function (res) {
      if (!res.ok) throw new Error(String(res.status));
      return res.json();
    }).then(function (data) {
      index = data || {};
      if (!index.assets || !index.assets.length) index.assets = securities();
      return index;
    }).catch(function () {
      index = { notes: [], assets: securities(), pages: [], codes: [] };
      return index;
    });
  }

  function closeList() {
    open = false;
    active = -1;
    if (input) {
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-activedescendant");
    }
    if (list) {
      list.hidden = true;
      list.innerHTML = "";
    }
  }

  function paint() {
    if (!list || !input) return;
    if (!rows.length) {
      closeList();
      return;
    }
    var ordered = rows.slice().sort(function (a, b) {
      var ga = logic.groupRank(a.group);
      var gb = logic.groupRank(b.group);
      if (ga !== gb) return ga - gb;
      return b.score - a.score;
    });
    rows = ordered;
    var best = logic.bestRow(rows);
    active = Math.max(0, rows.indexOf(best));
    var html = "";
    var last = "";
    rows.forEach(function (row, i) {
      if (row.group !== last) {
        html += '<li class="search-group" role="presentation">' + row.group + "</li>";
        last = row.group;
      }
      html += '<li role="option" id="search-opt-' + i + '" data-i="' + i + '"' +
        (i === active ? ' aria-selected="true"' : "") + ">" + escapeText(row.title) + "</li>";
    });
    list.innerHTML = html;
    list.hidden = false;
    open = true;
    input.setAttribute("aria-expanded", "true");
    input.setAttribute("aria-activedescendant", "search-opt-" + active);
  }

  function escapeText(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
    });
  }

  function go(href) {
    if (!href) return;
    window.location.assign(href);
  }

  function refresh() {
    if (!input || !logic) return;
    var q = input.value.trim();
    if (q.length < 1) {
      closeList();
      setLive("");
      return;
    }
    loadIndex().then(function (data) {
      var cmd = logic.parseCommand(q, data.assets || []);
      if (cmd && cmd.kind === "unlicensed") {
        rows = [];
        closeList();
        setLive("No licensed data for " + cmd.symbol);
        return;
      }
      rows = logic.suggest(data, q);
      paint();
      if (cmd && cmd.kind !== "unlicensed") {
        setLive(cmd.code + " opens " + cmd.href);
      } else if (rows[0] && rows[0].kind === "empty") {
        setLive(rows[0].title);
      } else {
        setLive(rows.length + " suggestions");
      }
    });
  }

  function choose(row) {
    if (!row || row.kind === "empty") return;
    go(row.href);
  }

  function collapseSearch() {
    var opener = document.getElementById("search-open");
    if (opener) opener.checked = false;
    closeList();
    if (input) input.blur();
  }

  function submitQuery(event) {
    if (!input || !logic) return;
    var q = input.value.trim();
    if (!q) return;
    if (event) event.preventDefault();
    loadIndex().then(function (data) {
      var highlighted = open && rows[active] && rows[active].kind !== "empty" ? rows[active] : null;
      var resolved = logic.resolveQuery(data, q, data.assets || []);
      if (highlighted && highlighted.href) {
        go(highlighted.href);
        return;
      }
      if (resolved.action === "go" && resolved.href) {
        go(resolved.href);
        return;
      }
      rows = logic.suggest(data, q);
      paint();
      setLive(resolved.title || "No results");
    });
  }

  function move(delta) {
    if (!open || !rows.length || !input) return;
    active = (active + delta + rows.length) % rows.length;
    var options = list.querySelectorAll("[role='option']");
    Array.prototype.forEach.call(options, function (node, i) {
      node.setAttribute("aria-selected", i === active ? "true" : "false");
    });
    input.setAttribute("aria-activedescendant", "search-opt-" + active);
  }

  if (form) {
    form.addEventListener("submit", submitQuery);
  }
  if (input) {
    input.addEventListener("input", refresh);
    input.addEventListener("keydown", function (event) {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        if (!open) refresh();
        else move(1);
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        move(-1);
      } else if (event.key === "Escape") {
        event.preventDefault();
        var step = logic.escapeStep(!!input.value);
        if (step.clear) {
          input.value = "";
          setLive("");
          rows = [];
          closeList();
        }
        if (step.close) collapseSearch();
      } else if (event.key === "Enter") {
        submitQuery(event);
      }
    });
  }
  if (list) {
    list.addEventListener("mousedown", function (event) {
      var option = event.target.closest("[role='option']");
      if (!option) return;
      event.preventDefault();
      var row = rows[Number(option.getAttribute("data-i"))];
      choose(row);
    });
  }
  document.addEventListener("keydown", function (event) {
    if (event.key !== "/" || event.metaKey || event.ctrlKey || event.altKey) return;
    var tag = (event.target && event.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea" || (event.target && event.target.isContentEditable)) return;
    if (!input) return;
    event.preventDefault();
    input.focus();
  });
  document.addEventListener("click", function (event) {
    if (!form || form.contains(event.target)) return;
    closeList();
  });
  var opener = document.getElementById("search-open");
  if (opener) {
    opener.addEventListener("change", function () {
      if (opener.checked && input) input.focus();
    });
  }
  var jump = document.querySelector(".asset-jump");
  if (jump) {
    jump.addEventListener("change", function () {
      if (jump.value) window.location.assign(jump.value);
    });
  }

  var pageQuery = new URLSearchParams(window.location.search).get("q");
  if (pageQuery && document.getElementById("search-static") && logic) {
    loadIndex().then(function (data) {
      var hits = logic.suggest(data, pageQuery);
      var box = document.getElementById("search-static");
      var html = hits.map(function (row) {
        return '<li><a href="' + row.href + '">' + escapeText(row.title) + "</a></li>";
      }).join("");
      var liveHits = document.createElement("ul");
      liveHits.className = "search-hits";
      liveHits.innerHTML = html;
      box.insertAdjacentElement("afterbegin", liveHits);
    });
  }

  window.AlphaSearch = {
    suggest: function (query, data) { return logic.suggest(data || index || { assets: securities() }, query); },
    parseCommand: function (query, assets) { return logic.parseCommand(query, assets || securities()); },
    choose: choose
  };
})();
