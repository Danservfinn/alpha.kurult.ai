/* /markets/: top movers, sector baskets, BTC and ETH dominance.
   CoinGecko public API only. Reuses AlphaDesk (market.js) for fetch, host
   backoff, and localStorage. Pure math lives in AlphaLogic (desk-logic.js).
   Nothing here writes CoinGecko bodies anywhere but this browser. */
(function () {
  "use strict";

  var REFRESH_MS = 120000;
  var MAX_SAVED_MS = 86400000;
  var KEY_MARKETS = "alpha.mkt.movers.v1";
  var KEY_GLOBAL = "alpha.mkt.global.v1";
  var KEY_SECTORS = "alpha.mkt.sectors.v1";
  var view = { window: "24h", sort: "change" };
  var data = { movers: null, global: null, sectors: null };
  var attempts = { movers: 0, global: 0, sectors: 0 };
  var retryTimer = {};
  var pollId = null;

  function desk() { return window.AlphaDesk; }
  function logic() { return window.AlphaLogic; }

  function esc(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function dir(n) {
    if (!Number.isFinite(n) || n === 0) return "";
    return n > 0 ? "tick-up" : "tick-down";
  }

  function pct(n) {
    if (!Number.isFinite(n)) return "n/a";
    var mark = n > 0 ? "\u25b2 " : n < 0 ? "\u25bc " : "";
    return mark + desk().fmtPct(n);
  }

  function money(n) {
    if (!Number.isFinite(n)) return "n/a";
    return "$" + desk().fmtCompact(n);
  }

  function price(n) {
    if (!Number.isFinite(n)) return "n/a";
    if (n !== 0 && Math.abs(n) < 0.01) return Number(n.toPrecision(3)).toString();
    return desk().fmtPx(n);
  }

  function stamp(ms) {
    return ms ? desk().etStamp(ms) : "";
  }

  function readBaskets() {
    var node = document.getElementById("alpha-baskets");
    if (!node) return [];
    try { return JSON.parse(node.textContent || "[]"); } catch (err) { return []; }
  }

  function ownPaths() {
    var map = {};
    (desk().securities() || []).forEach(function (row) {
      if (row.cg) map[row.cg] = row.path;
    });
    return map;
  }

  function saved(key) {
    var pack = desk().load(key);
    if (!pack || !pack.at || Date.now() - pack.at > MAX_SAVED_MS) return null;
    return pack;
  }

  function setText(id, text) {
    var node = document.getElementById(id);
    if (node) node.textContent = text;
  }

  // ---- paint -------------------------------------------------------------

  function moverTable(title, list, label, paths) {
    var rows = list.map(function (row) {
      var chg = logic().changeOf(row, view.window);
      var sym = String(row.symbol || "").toUpperCase();
      var href = paths[row.id];
      var asset = href ? '<a href="' + esc(href) + '">' + esc(sym) + "</a>" : esc(sym);
      return "<tr><td>" + asset + ' <span class="mkt-name">' + esc(row.name) + "</span></td>" +
        "<td>" + esc(price(row.current_price)) + "</td>" +
        '<td class="' + dir(chg) + '">' + esc(pct(chg)) + "</td>" +
        '<td class="mkt-cap">' + esc(money(row.market_cap)) + "</td></tr>";
    });
    if (!rows.length) rows = ['<tr><td colspan="4">None in this window.</td></tr>'];
    return '<div><h3 class="mkt-title">' + esc(title) + "</h3>" +
      '<table class="mkt"><thead><tr><th>Asset</th><th>Price</th><th>' + label + '</th><th class="mkt-cap">Mkt cap</th></tr></thead><tbody>' +
      rows.join("") + "</tbody></table></div>";
  }

  function paintMovers() {
    var body = document.getElementById("movers-body");
    if (!body) return;
    var pack = data.movers;
    if (!pack) return;
    var picked = logic().topMovers(pack.rows, view.window, 10);
    var label = view.window === "7d" ? "7d" : "24h";
    var span = view.window === "7d" ? "7 days" : "24h";
    var paths = ownPaths();
    body.innerHTML = moverTable("Gainers, " + span, picked.gainers, label, paths) +
      moverTable("Losers, " + span, picked.losers, label, paths);
    setText("movers-note", "Top 250 coins by market cap, " + picked.considered + " counted. Stablecoins, wrapped, staked, and tokenized assets left out.");
    setText("movers-badge", pack.stale ? "saved" : "live");
  }

  function paintDominance() {
    var body = document.getElementById("dominance-body");
    if (!body || !data.global) return;
    var dom = data.global.dom;
    if (!dom) return;
    var bar = '<div class="dom-bar" role="img" aria-label="' +
      esc("Bitcoin " + dom.btc.toFixed(2) + "%, Ether " + dom.eth.toFixed(2) + "%, rest " + dom.rest.toFixed(2) + "% of total crypto market cap") + '">' +
      '<span class="dom-btc" style="width:' + dom.btc.toFixed(2) + '%"></span>' +
      '<span class="dom-eth" style="width:' + dom.eth.toFixed(2) + '%"></span>' +
      '<span class="dom-rest" style="width:' + dom.rest.toFixed(2) + '%"></span></div>';
    var cells = [
      ["BTC dominance", dom.btc.toFixed(2) + "%", money(dom.btc_cap)],
      ["ETH dominance", dom.eth.toFixed(2) + "%", money(dom.eth_cap)],
      ["Rest of market", dom.rest.toFixed(2) + "%", ""],
      ["Total crypto cap", money(dom.total), Number.isFinite(dom.change_24h) ? pct(dom.change_24h) + " 24h" : ""]
    ];
    var strip = '<dl class="keystrip dom-strip">' + cells.map(function (cell, i) {
      var cls = i === 3 ? ' class="' + dir(dom.change_24h) + '"' : "";
      return "<div><dt>" + esc(cell[0]) + "</dt><dd>" + esc(cell[1]) + "</dd>" +
        (cell[2] ? '<dd class="key-note"' + cls + ">" + esc(cell[2]) + "</dd>" : "") + "</div>";
    }).join("") + "</dl>";
    var when = dom.updated_at ? '<p class="breadth">CoinGecko stamp ' + esc(stamp(dom.updated_at * 1000)) + ".</p>" : "";
    body.innerHTML = bar + strip + when;
    setText("dominance-badge", data.global.stale ? "saved" : "live");
  }

  function paintSectors() {
    var body = document.getElementById("sectors-body");
    if (!body || !data.sectors) return;
    var rows = logic().sortSectors(data.sectors.rows, view.sort);
    if (!rows.length) return;
    var html = rows.map(function (row) {
      return "<tr><td>" + esc(row.label) + "</td>" +
        "<td>" + esc(money(row.market_cap)) + "</td>" +
        '<td class="' + dir(row.change_24h) + '">' + esc(pct(row.change_24h)) + "</td>" +
        '<td class="mkt-cap">' + esc(money(row.volume_24h)) + "</td></tr>";
    });
    body.innerHTML = '<table class="mkt"><thead><tr><th>Sector</th><th>Mkt cap</th><th>24h</th><th class="mkt-cap">Volume 24h</th></tr></thead><tbody>' +
      html.join("") + "</tbody></table>";
    setText("sectors-badge", data.sectors.stale ? "saved" : "live");
  }

  // ---- fetch with 429 handling --------------------------------------------

  // Fetch key to the DOM prefix of its panel.
  var PANEL = { movers: "movers", global: "dominance", sectors: "sectors" };

  function waiting(name, err) {
    var ms = logic().nextRetryMs(attempts[name]);
    attempts[name] += 1;
    var pack = data[name];
    var id = PANEL[name];
    var limited = err && (err.limited || /429|opaque|backoff/i.test(String(err.message || err)));
    var why = limited ? "CoinGecko is rate limiting this page." : "CoinGecko did not answer.";
    var held = pack ? " Showing saved numbers from " + stamp(pack.at) + "." : "";
    setText(id + "-status", why + held + " Next try in " + Math.round(ms / 1000) + "s.");
    if (pack) {
      pack.stale = true;
    } else {
      var body = document.getElementById(id + "-body");
      if (body) body.innerHTML = '<p class="chart-empty">Waiting on CoinGecko. Next try in ' + Math.round(ms / 1000) + "s.</p>";
      setText(id + "-badge", "waiting");
    }
    clearTimeout(retryTimer[name]);
    retryTimer[name] = setTimeout(function () { pull(name); }, ms);
  }

  function landed(name) {
    attempts[name] = 0;
    clearTimeout(retryTimer[name]);
    setText(PANEL[name] + "-status", "");
  }

  var FETCH = {
    movers: function () {
      var url = desk().CG + "/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false&price_change_percentage=24h,7d";
      return desk().getJson(url).then(function (rows) {
        if (!Array.isArray(rows) || !rows.length) throw new Error("markets shape");
        var slim = rows.map(logic().slimMarketRow);
        data.movers = { at: Date.now(), rows: slim, stale: false };
        desk().save(KEY_MARKETS, { at: data.movers.at, rows: slim });
        paintMovers();
      });
    },
    global: function () {
      return desk().getJson(desk().CG + "/global").then(function (body) {
        var dom = logic().dominance(body);
        if (!dom) throw new Error("global shape");
        data.global = { at: Date.now(), dom: dom, stale: false };
        desk().save(KEY_GLOBAL, { at: data.global.at, dom: dom });
        paintDominance();
      });
    },
    sectors: function () {
      return desk().getJson(desk().CG + "/coins/categories?order=market_cap_desc", 20000).then(function (body) {
        if (!Array.isArray(body) || !body.length) throw new Error("categories shape");
        var rows = logic().sectorRows(body, readBaskets());
        if (!rows.length) throw new Error("no baskets");
        data.sectors = { at: Date.now(), rows: rows, stale: false };
        desk().save(KEY_SECTORS, { at: data.sectors.at, rows: rows });
        paintSectors();
      });
    }
  };

  function pull(name) {
    if (document.hidden) return Promise.resolve();
    return desk().queueChart(function () {
      return FETCH[name]().then(function () { landed(name); }, function (err) {
        waiting(name, err);
        if (name === "movers") paintMovers();
        if (name === "global") paintDominance();
        if (name === "sectors") paintSectors();
      });
    });
  }

  function pullAll() {
    // One at a time through the shared queue so a page load is three calls, not a burst.
    pull("global");
    pull("movers");
    pull("sectors");
  }

  // ---- controls ------------------------------------------------------------

  function wire(group, key, paint) {
    var buttons = document.querySelectorAll("[data-" + group + "]");
    Array.prototype.forEach.call(buttons, function (btn) {
      btn.addEventListener("click", function () {
        view[key] = btn.getAttribute("data-" + group);
        Array.prototype.forEach.call(buttons, function (other) {
          other.setAttribute("aria-pressed", other === btn ? "true" : "false");
        });
        paint();
      });
    });
  }

  function restore() {
    var m = saved(KEY_MARKETS);
    if (m && m.rows) { data.movers = { at: m.at, rows: m.rows, stale: true }; paintMovers(); }
    var g = saved(KEY_GLOBAL);
    if (g && g.dom) { data.global = { at: g.at, dom: g.dom, stale: true }; paintDominance(); }
    var s = saved(KEY_SECTORS);
    if (s && s.rows) { data.sectors = { at: s.at, rows: s.rows, stale: true }; paintSectors(); }
  }

  function start() {
    clearInterval(pollId);
    if (!document.hidden) pollId = setInterval(pullAll, REFRESH_MS);
  }

  function boot() {
    if (!document.getElementById("movers-body") || !desk() || !logic()) return;
    wire("window", "window", paintMovers);
    wire("sort", "sort", paintSectors);
    restore();
    pullAll();
    start();
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) { clearInterval(pollId); return; }
      var oldest = Math.min(
        data.movers ? data.movers.at : 0,
        data.global ? data.global.at : 0,
        data.sectors ? data.sectors.at : 0
      );
      if (Date.now() - oldest >= REFRESH_MS) pullAll();
      start();
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
