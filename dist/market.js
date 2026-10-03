/* alpha.kurult.ai market desk. First-party only. No third-party script host. */
(function () {
  "use strict";

  var CG = "https://api.coingecko.com/api/v3";
  var TICKER_MS = 60000;
  var MARKETS_MS = 120000;
  var CHIPS_MS = 300000;
  var CHAIN_MS = 60000;
  var CHART_TTL = 300000;
  var IDS = { BTC: "bitcoin", ETH: "ethereum", SOL: "solana", PRL: "pearl-2" };
  var NAMES = { BTC: "Bitcoin", ETH: "Ether", SOL: "Solana", PRL: "Pearl" };
  var SKIP = {
    usdt: 1, usdc: 1, usds: 1, dai: 1, fdusd: 1, usde: 1, pyusd: 1, tusd: 1,
    usdd: 1, usd1: 1, wbtc: 1, weth: 1, steth: 1, wsteth: 1, weeth: 1, cbbtc: 1, wbt: 1
  };
  var hostWait = {};
  var hostNext = {};
  var lastTicker = 0;
  var lastChips = 0;
  var lastMarkets = 0;
  var lastChain = 0;
  var pollIds = [];
  var state = { ticker: null, chips: {}, markets: null, chain: null, chart: {} };

  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
    });
  }

  function etDate(ms) {
    try {
      return new Intl.DateTimeFormat("en-CA", {
        timeZone: "America/New_York",
        year: "numeric",
        month: "2-digit",
        day: "2-digit"
      }).format(new Date(ms));
    } catch (err) {
      return "";
    }
  }

  function etClock(ms) {
    try {
      return new Intl.DateTimeFormat("en-US", {
        timeZone: "America/New_York",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false
      }).format(new Date(ms)) + " ET";
    } catch (err) {
      return "";
    }
  }

  function etStamp(ms) {
    try {
      var bag = {};
      new Intl.DateTimeFormat("en-US", {
        timeZone: "America/New_York",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false
      }).formatToParts(new Date(ms)).forEach(function (part) {
        bag[part.type] = part.value;
      });
      if (!bag.month || !bag.day || !bag.hour || !bag.minute) return "";
      return bag.month + " " + bag.day + ", " + bag.hour + ":" + bag.minute + " ET";
    } catch (err) {
      return "";
    }
  }

  function load(key) {
    try {
      var raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : null;
    } catch (err) {
      return null;
    }
  }

  function save(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (err) {
      /* private mode */
    }
  }

  function hostOf(url) {
    if (!url || url.charAt(0) === "/") return "self";
    var match = String(url).match(/^https?:\/\/([^\/]+)/i);
    return match ? match[1].toLowerCase() : "self";
  }

  function isCoinGecko(url) {
    return hostOf(url).indexOf("coingecko.com") !== -1;
  }

  function hostBlocked(host) {
    return Date.now() < (hostNext[host] || 0);
  }

  function backOff(host) {
    var prev = hostWait[host] || 30000;
    var wait = Math.min(Math.max(prev * 2, 60000), 600000);
    hostWait[host] = wait;
    hostNext[host] = Date.now() + wait;
  }

  function clearBackOff(host) {
    delete hostWait[host];
    delete hostNext[host];
  }

  function limitedFailure(url, err) {
    var host = hostOf(url);
    if (isCoinGecko(url)) {
      backOff(host);
      return;
    }
    if (!err) return;
    var name = err.name || "";
    var msg = String(err.message || err);
    if (name === "TypeError" || name === "AbortError" || /429|opaque|failed to fetch|network|cors/i.test(msg)) {
      backOff(host);
    }
  }

  function sourceWhen(raw) {
    var n = Number(raw);
    if (!Number.isFinite(n) || n <= 0) return "";
    var ms = n < 1e12 ? n * 1000 : n;
    var date = etDate(ms);
    var clock = etClock(ms);
    if (date && clock) return date + " " + clock;
    return date || clock;
  }

  function chipSaved(id) {
    var live = state.chips && state.chips[id];
    if (live && live.value && live.value !== "unavailable") return live;
    var saved = load("alpha.chips.v1") || {};
    return saved[id] || null;
  }

  function keepChip(id) {
    var saved = chipSaved(id);
    if (saved) {
      state.chips[id] = {
        value: saved.value,
        asof: saved.asof || "",
        stale: true
      };
    } else {
      state.chips[id] = { value: "unavailable", asof: "", stale: true };
    }
  }

  function opaque(res) {
    return !res || res.type === "opaque" || res.type === "opaqueredirect" || res.status === 0;
  }

  async function getJson(url, timeout) {
    var host = hostOf(url);
    if (hostBlocked(host)) {
      var blocked = new Error("backoff");
      blocked.limited = true;
      throw blocked;
    }
    var ctrl = new AbortController();
    var timer = setTimeout(function () { ctrl.abort(); }, timeout || 12000);
    try {
      var res;
      try {
        res = await fetch(url, {
          headers: { Accept: "application/json" },
          signal: ctrl.signal
        });
      } catch (err) {
        limitedFailure(url, err);
        throw err;
      }
      if (opaque(res) || (isCoinGecko(url) && !res.ok) || res.status === 429) {
        backOff(host);
        throw new Error(opaque(res) ? "opaque" : String(res.status));
      }
      if (!res.ok) {
        if (res.status >= 500) backOff(host);
        throw new Error(String(res.status));
      }
      var body;
      try {
        body = await res.json();
      } catch (err) {
        if (isCoinGecko(url) || err.name === "TypeError") backOff(host);
        throw err;
      }
      clearBackOff(host);
      return body;
    } finally {
      clearTimeout(timer);
    }
  }

  async function getText(url) {
    var host = hostOf(url);
    if (hostBlocked(host)) {
      var blocked = new Error("backoff");
      blocked.limited = true;
      throw blocked;
    }
    var ctrl = new AbortController();
    var timer = setTimeout(function () { ctrl.abort(); }, 12000);
    try {
      var res;
      try {
        res = await fetch(url, { headers: { Accept: "text/csv, text/plain, */*" }, signal: ctrl.signal });
      } catch (err) {
        limitedFailure(url, err);
        throw err;
      }
      if (opaque(res) || res.status === 429) {
        backOff(host);
        throw new Error(opaque(res) ? "opaque" : "429");
      }
      if (!res.ok) {
        if (res.status >= 500) backOff(host);
        throw new Error(String(res.status));
      }
      var text = await res.text();
      clearBackOff(host);
      return text;
    } finally {
      clearTimeout(timer);
    }
  }

  function fmtPx(n) {
    if (!Number.isFinite(n)) return "n/a";
    var abs = Math.abs(n);
    var digits = abs >= 1000 ? 0 : abs >= 10 ? 2 : abs >= 1 ? 3 : 4;
    return n.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
  }

  function fmtPct(n) {
    if (!Number.isFinite(n)) return "";
    var sign = n > 0 ? "+" : "";
    return sign + n.toFixed(2) + "%";
  }

  function fmtCompact(n) {
    if (!Number.isFinite(n)) return "n/a";
    var abs = Math.abs(n);
    if (abs >= 1e12) return (n / 1e12).toFixed(2) + "T";
    if (abs >= 1e9) return (n / 1e9).toFixed(2) + "B";
    if (abs >= 1e6) return (n / 1e6).toFixed(2) + "M";
    return fmtPx(n);
  }

  function dirClass(n) {
    if (!Number.isFinite(n) || n === 0) return "";
    return n > 0 ? "tick-up" : "tick-down";
  }

  function arrow(n) {
    if (!Number.isFinite(n) || n === 0) return "";
    return n > 0 ? "\u25b2 " : "\u25bc ";
  }

  function setStatus(text) {
    var node = document.getElementById("market-status");
    if (node) node.textContent = text;
  }

  function paintTicker(payload, stale) {
    var ids = coinMap();
    var root = document.getElementById("ticker");
    if (!root || !payload) return;
    Object.keys(ids).forEach(function (sym) {
      var row = payload[sym];
      var node = root.querySelector('[data-symbol="' + sym + '"]');
      if (!node) return;
      var px = node.querySelector(".tick-px");
      var chg = node.querySelector(".tick-chg");
      if (!row || row.na || !Number.isFinite(row.price)) {
        if (px) px.textContent = "n/a";
        if (chg) chg.textContent = "";
        node.classList.add("tick-na");
        return;
      }
      node.classList.remove("tick-na");
      if (px) px.textContent = fmtPx(row.price);
      if (chg) {
        chg.textContent = arrow(row.change) + fmtPct(row.change);
        chg.className = "tick-chg " + dirClass(row.change);
      }
      if (!stale && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        node.classList.remove("flash");
        void node.offsetWidth;
        node.classList.add("flash");
      }
    });
    var badge = document.getElementById("ticker-state");
    if (badge) {
      var when = payload && payload.as_of ? (stale ? etStamp(payload.as_of) : etClock(payload.as_of)) : "";
      badge.textContent = stale ? ("stale" + (when ? " as of " + when : "")) : ("agg " + when);
      badge.className = "tick tick-state" + (stale ? " tick-stale" : "");
    }
  }

  function tickerSaved() {
    return state.ticker || load("alpha.ticker.v1");
  }

  async function pullTicker(force) {
    if (document.hidden || !document.getElementById("ticker")) return;
    if (!force && Date.now() - lastTicker < TICKER_MS) return;
    if (hostBlocked(hostOf(CG))) {
      var held = tickerSaved();
      if (held) {
        state.ticker = held;
        paintTicker(held, true);
      }
      return;
    }
    lastTicker = Date.now();
    var ids = coinMap();
    var idList = Object.keys(ids).map(function (sym) { return ids[sym]; }).join(",");
    var url = CG + "/simple/price?ids=" + idList + "&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true";
    try {
      var data = await getJson(url);
      var payload = { as_of: Date.now() };
      Object.keys(ids).forEach(function (sym) {
        var row = data[ids[sym]];
        if (!row || !Number.isFinite(row.usd)) {
          payload[sym] = { na: true };
          return;
        }
        payload[sym] = {
          na: false,
          price: row.usd,
          change: Number(row.usd_24h_change),
          volume: Number(row.usd_24h_vol)
        };
      });
      state.ticker = payload;
      save("alpha.ticker.v1", payload);
      paintTicker(payload, false);
      var bits = Object.keys(ids).map(function (sym) {
        var row = payload[sym];
        return row && !row.na ? sym + " " + fmtPx(row.price) : sym + " n/a";
      });
      setStatus("Aggregated prices. " + bits.join(", ") + ". Data provided by CoinGecko.");
    } catch (err) {
      var saved = tickerSaved();
      if (saved) {
        state.ticker = saved;
        paintTicker(saved, true);
      } else {
        var badge = document.getElementById("ticker-state");
        if (badge) {
          badge.textContent = "unavailable";
          badge.className = "tick tick-state tick-stale";
        }
      }
    }
  }

  function chip(id, label, value, asof, source, stale) {
    var title = source + (asof ? ". As of " + asof : "") + (stale ? ". Stale" : "");
    return '<span class="chip' + (stale ? " chip-stale" : "") + '" role="listitem" tabindex="0" title="' + esc(title) + '" data-chip="' + esc(id) + '">' +
      '<span class="chip-id">' + esc(id) + '</span>' +
      '<span class="chip-px">' + esc(value) + '</span>' +
      '<span class="chip-asof">' + esc(asof || (stale ? "stale" : "n/a")) + '</span>' +
      '</span>';
  }

  function paintChips() {
    var root = document.getElementById("chips");
    if (!root) return;
    var c = state.chips;
    var html = [
      chip("UST10Y", "UST10Y", c.ust10y ? c.ust10y.value : "…", c.ust10y && c.ust10y.asof, "Source: U.S. Treasury", c.ust10y && c.ust10y.stale),
      chip("UST2Y", "UST2Y", c.ust2y ? c.ust2y.value : "…", c.ust2y && c.ust2y.asof, "Source: U.S. Treasury", c.ust2y && c.ust2y.stale),
      chip("SOFR", "SOFR", c.sofr ? c.sofr.value : "…", c.sofr && c.sofr.asof, "Source: Federal Reserve Bank of New York", c.sofr && c.sofr.stale),
      chip("EURUSD", "EURUSD", c.eurusd ? c.eurusd.value : "…", c.eurusd && c.eurusd.asof, "Source: ECB statistics", c.eurusd && c.eurusd.stale),
      chip("BTC.D", "BTC.D", c.btcd ? c.btcd.value : "…", c.btcd && c.btcd.asof, "Source: CoinGecko", c.btcd && c.btcd.stale),
      chip("TOTAL", "TOTAL", c.total ? c.total.value : "…", c.total && c.total.asof, "Source: CoinGecko", c.total && c.total.stale),
      chip("F&G", "F&G", c.fng ? c.fng.value : "…", c.fng && c.fng.asof, "Source: alternative.me", c.fng && c.fng.stale)
    ];
    root.innerHTML = html.join("");
  }

  async function pullTreasury() {
    try {
      var data = await getJson("/api/treasury");
      if (!data || !data.ok) throw new Error("treasury");
      var asof = data.as_of || "";
      state.chips.ust10y = {
        value: Number.isFinite(data.ust_10y) ? data.ust_10y.toFixed(2) + "%" : "n/a",
        asof: asof,
        stale: !!data.stale
      };
      state.chips.ust2y = {
        value: Number.isFinite(data.ust_2y) ? data.ust_2y.toFixed(2) + "%" : "n/a",
        asof: asof,
        stale: !!data.stale
      };
    } catch (err) {
      keepChip("ust10y");
      keepChip("ust2y");
    }
  }

  async function pullSofr() {
    try {
      var data = await getJson("https://markets.newyorkfed.org/api/rates/secured/sofr/last/1.json");
      var row = data && data.refRates && data.refRates[0];
      if (!row || !Number.isFinite(row.percentRate)) throw new Error("sofr");
      state.chips.sofr = { value: row.percentRate.toFixed(2) + "%", asof: row.effectiveDate, stale: false };
    } catch (err) {
      keepChip("sofr");
    }
  }

  function parseEcb(text) {
    var lines = String(text).trim().split(/\r?\n/).filter(Boolean);
    if (lines.length < 2) return null;
    var head = lines[0].split(",");
    var dateIdx = head.indexOf("TIME_PERIOD");
    var valueIdx = head.indexOf("OBS_VALUE");
    if (dateIdx < 0 || valueIdx < 0) return null;
    var last = lines[lines.length - 1].split(",");
    var value = Number(last[valueIdx]);
    if (!Number.isFinite(value)) return null;
    return { date: last[dateIdx], value: value };
  }

  async function pullEcb() {
    try {
      var text = await getText("https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?lastNObservations=2&format=csvdata");
      var row = parseEcb(text);
      if (!row) throw new Error("ecb");
      state.chips.eurusd = { value: row.value.toFixed(4), asof: row.date, stale: false };
    } catch (err) {
      keepChip("eurusd");
    }
  }

  async function pullGlobal() {
    if (hostBlocked(hostOf(CG))) {
      keepChip("btcd");
      keepChip("total");
      return;
    }
    try {
      var data = await getJson(CG + "/global");
      var body = data && data.data;
      var btc = body && body.market_cap_percentage && body.market_cap_percentage.btc;
      var total = body && body.total_market_cap && body.total_market_cap.usd;
      if (!Number.isFinite(btc) || !Number.isFinite(total)) throw new Error("global");
      var asof = sourceWhen(body.updated_at);
      state.chips.btcd = { value: btc.toFixed(1) + "%", asof: asof, stale: false };
      state.chips.total = { value: fmtCompact(total), asof: asof, stale: false };
    } catch (err) {
      keepChip("btcd");
      keepChip("total");
    }
  }

  async function pullFng() {
    try {
      var data = await getJson("https://api.alternative.me/fng/?limit=1");
      var row = data && data.data && data.data[0];
      if (!row || row.value == null) throw new Error("fng");
      var stamp = Number(row.timestamp) * 1000;
      state.chips.fng = {
        value: row.value + " " + (row.value_classification || ""),
        asof: Number.isFinite(stamp) ? etDate(stamp) : "",
        stale: false
      };
    } catch (err) {
      keepChip("fng");
    }
  }

  async function pullChips() {
    if (document.hidden || !document.getElementById("chips")) return;
    lastChips = Date.now();
    await Promise.all([pullTreasury(), pullSofr(), pullEcb(), pullGlobal(), pullFng()]);
    save("alpha.chips.v1", state.chips);
    paintChips();
    paintMarkets();
  }

  function chartUrl(sym, tf) {
    var id = IDS[sym];
    if (!id) return "";
    if (tf === "4H") return CG + "/coins/" + id + "/ohlc?vs_currency=usd&days=14";
    if (tf === "1D") return CG + "/coins/" + id + "/market_chart?vs_currency=usd&days=180";
    return CG + "/coins/" + id + "/market_chart?vs_currency=usd&days=2";
  }

  function normalizeSeries(tf, data) {
    if (tf === "4H" && Array.isArray(data)) {
      return data.map(function (row) {
        return { t: row[0], o: row[1], h: row[2], l: row[3], c: row[4] };
      }).filter(function (row) {
        return Number.isFinite(row.c);
      });
    }
    var prices = data && data.prices;
    if (!Array.isArray(prices)) return [];
    return prices.map(function (row) {
      return { t: row[0], c: row[1] };
    }).filter(function (row) {
      return Number.isFinite(row.c);
    });
  }

  function svgChart(series, tf) {
    if (!series.length) return '<p class="chart-empty">Chart unavailable.</p>';
    var w = 640;
    var h = 220;
    var padL = 8;
    var padR = 72;
    var padT = 14;
    var padB = 22;
    var values = [];
    series.forEach(function (row) {
      values.push(row.h != null ? row.h : row.c);
      values.push(row.l != null ? row.l : row.c);
    });
    var max = Math.max.apply(null, values);
    var min = Math.min.apply(null, values);
    var span = max - min || 1;
    var innerW = w - padL - padR;
    var innerH = h - padT - padB;
    function y(price) {
      return padT + ((max - price) / span) * innerH;
    }
    var parts = [];
    if (series[0].o != null) {
      var slot = innerW / series.length;
      series.forEach(function (row, i) {
        var x = padL + i * slot + slot / 2;
        var up = row.c >= row.o;
        var color = up ? "#39d441" : "#dc5d5e";
        var top = y(Math.max(row.o, row.c));
        var bot = y(Math.min(row.o, row.c));
        var bw = Math.max(slot * 0.55, 1.2);
        parts.push('<line x1="' + x.toFixed(1) + '" y1="' + y(row.h).toFixed(1) + '" x2="' + x.toFixed(1) + '" y2="' + y(row.l).toFixed(1) + '" stroke="' + color + '" stroke-width="1"/>');
        parts.push('<rect x="' + (x - bw / 2).toFixed(1) + '" y="' + top.toFixed(1) + '" width="' + bw.toFixed(1) + '" height="' + Math.max(bot - top, 1).toFixed(1) + '" fill="' + color + '"/>');
      });
    } else {
      var step = series.length > 1 ? innerW / (series.length - 1) : innerW;
      var points = series.map(function (row, i) {
        return (padL + i * step).toFixed(1) + "," + y(row.c).toFixed(1);
      }).join(" ");
      parts.push('<polyline fill="none" stroke="#f1bd59" stroke-width="1.6" points="' + points + '"/>');
    }
    var last = series[series.length - 1];
    parts.push('<text x="' + (w - padR + 6) + '" y="' + Math.max(12, y(last.c)).toFixed(1) + '" fill="#ffffff" font-size="12" font-family="ui-monospace, monospace">' + esc(fmtPx(last.c)) + '</text>');
    var label = tf === "4H" ? "4H aggregated OHLC" : tf + " aggregated price";
    return '<svg class="chart-svg" viewBox="0 0 ' + w + ' ' + h + '" role="img" aria-label="' + esc(label) + '">' + parts.join("") + '</svg>';
  }

  function selectedSymbol() {
    var panel = document.getElementById("chart-panel");
    if (!panel) return "BTC";
    var pressed = panel.querySelector('[data-symbol][aria-pressed="true"]');
    return pressed ? pressed.getAttribute("data-symbol") : (panel.getAttribute("data-default") || "BTC");
  }

  function selectedTf() {
    var panel = document.getElementById("chart-panel");
    if (!panel) return "1D";
    var pressed = panel.querySelector('[data-tf][aria-pressed="true"]');
    return pressed ? pressed.getAttribute("data-tf") : "1D";
  }

  function paintChart(sym, tf, series, stale) {
    var frame = document.getElementById("chart-frame");
    var note = document.getElementById("chart-note");
    var readout = document.getElementById("chart-readout");
    var badge = document.getElementById("chart-badge");
    if (!frame) return;
    var kind = tf === "4H" ? "4-hour OHLC" : tf === "1D" ? "daily price" : "hourly price";
    frame.innerHTML = svgChart(series, tf);
    frame.setAttribute("aria-label", (NAMES[sym] || sym) + " " + kind);
    if (note) {
      note.textContent = (NAMES[sym] || sym) + " " + kind + ". Aggregated price, not one exchange." + (stale ? " Stale." : "");
    }
    if (badge) {
      var last = series.length ? series[series.length - 1] : null;
      var when = last ? etStamp(last.t) : "";
      badge.textContent = stale ? ("stale" + (when ? " as of " + when : "")) : "aggregated";
    }
    if (readout && series.length) {
      var row = series[series.length - 1];
      var stamp = etDate(row.t) + " " + etClock(row.t);
      readout.textContent = "Last " + fmtPx(row.c) + " at " + stamp + ". Data provided by CoinGecko." + (stale ? " Stale." : "");
    } else if (readout) {
      readout.textContent = "Chart unavailable.";
    }
  }

  function chartSaved(key) {
    var live = state.chart[key];
    if (live && live.series && live.series.length) return live;
    var stored = load("alpha.chart.v1");
    if (stored && stored.key === key && stored.series && stored.series.length) {
      return { at: stored.at, series: stored.series };
    }
    return null;
  }

  async function pullChart(sym, tf, force) {
    if (document.hidden || !document.getElementById("chart-panel")) return;
    var key = sym + ":" + tf;
    var cached = state.chart[key];
    if (!force && cached && Date.now() - cached.at < CHART_TTL) {
      paintChart(sym, tf, cached.series, false);
      return;
    }
    if (hostBlocked(hostOf(CG))) {
      var held = chartSaved(key);
      if (held) {
        state.chart[key] = held;
        paintChart(sym, tf, held.series, true);
      } else {
        paintChart(sym, tf, [], true);
      }
      return;
    }
    try {
      var data = await getJson(chartUrl(sym, tf));
      var series = normalizeSeries(tf, data);
      if (!series.length) throw new Error("empty");
      state.chart[key] = { at: Date.now(), series: series };
      save("alpha.chart.v1", { key: key, at: Date.now(), series: series });
      paintChart(sym, tf, series, false);
    } catch (err) {
      var saved = chartSaved(key);
      if (saved) {
        state.chart[key] = saved;
        paintChart(sym, tf, saved.series, true);
      } else {
        paintChart(sym, tf, [], true);
      }
    }
  }

  function bindChart() {
    var panel = document.getElementById("chart-panel");
    if (!panel) return;
    panel.addEventListener("click", function (event) {
      var btn = event.target.closest("button");
      if (!btn || !panel.contains(btn)) return;
      var group = btn.parentElement;
      if (!group) return;
      Array.prototype.forEach.call(group.querySelectorAll("button"), function (peer) {
        peer.setAttribute("aria-pressed", peer === btn ? "true" : "false");
      });
      pullChart(selectedSymbol(), selectedTf(), false);
    });
  }

  function rowHtml(item) {
    var chg = Number(item.price_change_percentage_24h);
    return "<tr><td>" + esc(String(item.symbol || "").toUpperCase()) + "</td><td>" + esc(fmtPx(Number(item.current_price))) +
      '</td><td class="' + dirClass(chg) + '">' + esc(arrow(chg) + fmtPct(chg)) + "</td><td>" + esc(fmtCompact(Number(item.total_volume))) + "</td></tr>";
  }

  function paintMarkets() {
    var body = document.getElementById("markets-body");
    var badge = document.getElementById("markets-badge");
    if (!body) return;
    var pack = state.markets;
    if (!pack || !pack.rows) {
      body.innerHTML = '<p class="chart-empty">Markets unavailable.</p>';
      if (badge) badge.textContent = "unavailable";
      return;
    }
    var rows = pack.rows.filter(function (item) {
      return item && item.symbol && !SKIP[String(item.symbol).toLowerCase()] && Number.isFinite(item.price_change_percentage_24h);
    });
    var gainers = rows.slice().sort(function (a, b) {
      return b.price_change_percentage_24h - a.price_change_percentage_24h;
    }).slice(0, 5);
    var losers = rows.slice().sort(function (a, b) {
      return a.price_change_percentage_24h - b.price_change_percentage_24h;
    }).slice(0, 5);
    var volume = rows.slice().sort(function (a, b) {
      return (b.total_volume || 0) - (a.total_volume || 0);
    }).slice(0, 5);
    var up = rows.filter(function (item) { return item.price_change_percentage_24h > 0; }).length;
    var down = rows.filter(function (item) { return item.price_change_percentage_24h < 0; }).length;
    var head = "<table class=\"mkt\"><thead><tr><th>Asset</th><th>Price</th><th>24h</th><th>Volume</th></tr></thead><tbody>";
    var macro = "";
    if (state.chips.ust10y || state.chips.sofr || state.chips.eurusd) {
      macro = '<p class="macro-line">UST10Y ' + esc(state.chips.ust10y ? state.chips.ust10y.value : "n/a") +
        " · UST2Y " + esc(state.chips.ust2y ? state.chips.ust2y.value : "n/a") +
        " · SOFR " + esc(state.chips.sofr ? state.chips.sofr.value : "n/a") +
        " · EURUSD " + esc(state.chips.eurusd ? state.chips.eurusd.value : "n/a") + "</p>";
    }
    body.innerHTML =
      '<p class="breadth">Breadth ' + up + " up / " + down + " down in the filtered top 250. Stables and wrapped assets excluded.</p>" +
      macro +
      '<div class="mkt-grid"><div><h3 class="mkt-title">Gainers</h3>' + head + gainers.map(rowHtml).join("") + "</tbody></table></div>" +
      '<div><h3 class="mkt-title">Losers</h3>' + head + losers.map(rowHtml).join("") + "</tbody></table></div>" +
      '<div><h3 class="mkt-title">Volume</h3>' + head + volume.map(rowHtml).join("") + "</tbody></table></div></div>" +
      '<p class="src-foot">Prices, movers, volume, BTC.D, and total cap: <a href="https://www.coingecko.com/" rel="noopener">Data provided by CoinGecko</a>. Aggregated, not one exchange.' +
      (pack.stale ? " Stale" + (pack.at ? " as of " + etStamp(pack.at) : "") + "." : "") + "</p>";
    if (badge) badge.textContent = pack.stale ? "stale" : "agg";
  }

  function marketsSaved() {
    if (state.markets && state.markets.rows) return state.markets;
    var stored = load("alpha.markets.v1");
    if (stored && stored.rows) return { rows: stored.rows, at: stored.at, stale: true };
    return null;
  }

  async function pullMarkets() {
    if (document.hidden || !document.getElementById("markets-body")) return;
    lastMarkets = Date.now();
    if (hostBlocked(hostOf(CG))) {
      var held = marketsSaved();
      if (held) {
        state.markets = held;
        state.markets.stale = true;
        paintMarkets();
      }
      return;
    }
    try {
      var data = await getJson(CG + "/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false&price_change_percentage=24h");
      if (!Array.isArray(data) || !data.length) throw new Error("markets");
      state.markets = { at: Date.now(), rows: data, stale: false };
      save("alpha.markets.v1", { at: Date.now(), rows: data.map(function (item) {
        return {
          symbol: item.symbol,
          current_price: item.current_price,
          price_change_percentage_24h: item.price_change_percentage_24h,
          total_volume: item.total_volume
        };
      }) });
      paintMarkets();
    } catch (err) {
      var saved = marketsSaved();
      if (saved) {
        state.markets = saved;
        state.markets.stale = true;
        paintMarkets();
      } else {
        var body = document.getElementById("markets-body");
        if (body) body.innerHTML = '<p class="chart-empty">Markets unavailable.</p>';
      }
    }
  }

  function chainCard(title, lines, credit) {
    var body = lines.map(function (line) {
      return "<li>" + esc(line) + "</li>";
    }).join("");
    return '<article class="chain-card"><h3 class="mkt-title">' + esc(title) + '</h3><ul class="chain-list">' + body + '</ul><p class="src-foot">' + credit + "</p></article>";
  }

  function paintChain(scope) {
    var body = document.getElementById("chain-body");
    var badge = document.getElementById("chain-badge");
    if (!body) return;
    var pack = state.chain || {};
    var cards = [];
    var want = scope === "all" ? ["BTC", "ETH", "SOL", "PRL"] : [scope];
    want.forEach(function (sym) {
      var row = pack[sym];
      if (!row) {
        cards.push(chainCard(sym, ["unavailable"], "No reading yet."));
        return;
      }
      cards.push(chainCard(sym, row.lines, row.credit));
    });
    body.innerHTML = cards.join("");
    if (badge) badge.textContent = pack.stale ? "stale" : "chain";
  }

  async function pullBtc() {
    try {
      var tip = await getText("https://mempool.space/api/blocks/tip/height");
      var fees = await getJson("https://mempool.space/api/v1/fees/recommended");
      var mem = await getJson("https://mempool.space/api/mempool");
      var height = Number(String(tip).trim());
      if (!Number.isFinite(height)) throw new Error("tip");
      return {
        lines: [
          "Height " + height.toLocaleString("en-US"),
          "Fee fastest " + fees.fastestFee + " sat/vB",
          "Fee 30m " + fees.halfHourFee + " sat/vB",
          "Mempool " + Number(mem.count).toLocaleString("en-US") + " tx"
        ],
        credit: '<a href="https://mempool.space/" rel="noopener">mempool.space</a>. alpha.kurult.ai is not affiliated with mempool.space.'
      };
    } catch (err) {
      try {
        var alt = await getText("https://blockstream.info/api/blocks/tip/height");
        var estimates = await getJson("https://blockstream.info/api/fee-estimates");
        var height2 = Number(String(alt).trim());
        if (!Number.isFinite(height2)) throw new Error("alt");
        return {
          lines: [
            "Height " + height2.toLocaleString("en-US"),
            "Fee ~2 blocks " + estimates["2"] + " sat/vB",
            "Fee ~6 blocks " + estimates["6"] + " sat/vB"
          ],
          credit: 'Fallback: <a href="https://blockstream.info/" rel="noopener">Blockstream Esplora</a>. Not affiliated. mempool.space did not answer.'
        };
      } catch (err2) {
        return {
          lines: ["unavailable"],
          credit: '<a href="https://mempool.space/" rel="noopener">mempool.space</a> unavailable. Not affiliated.'
        };
      }
    }
  }

  async function pullChainProxy() {
    try {
      return await getJson("/api/chain");
    } catch (err) {
      return null;
    }
  }

  async function pullChain() {
    if (document.hidden || !document.getElementById("chain-panel")) return;
    lastChain = Date.now();
    var scope = (document.getElementById("chain-panel") || {}).getAttribute ? document.getElementById("chain-panel").getAttribute("data-chain") : "all";
    var btc = scope === "all" || scope === "BTC" ? await pullBtc() : null;
    var proxy = scope === "PRL" || scope === "all" || scope === "ETH" || scope === "SOL" ? await pullChainProxy() : null;
    var next = state.chain || {};
    if (btc) next.BTC = btc;
    if (proxy && proxy.eth && !proxy.eth.unavailable) {
      next.ETH = {
        lines: [
          "Height " + Number(proxy.eth.block).toLocaleString("en-US"),
          "Gas " + proxy.eth.gas_gwei + " gwei"
        ],
        credit: esc(proxy.eth.credit || "Public Ethereum RPC. Not affiliated.")
      };
    } else if (scope === "all" || scope === "ETH") {
      next.ETH = next.ETH || { lines: ["unavailable"], credit: "Public Ethereum RPC unavailable." };
      next.ETH.stale = true;
    }
    if (proxy && proxy.sol && !proxy.sol.unavailable) {
      next.SOL = {
        lines: [
          "Epoch " + proxy.sol.epoch,
          "Progress " + (proxy.sol.progress == null ? "n/a" : proxy.sol.progress + "%"),
          "Slot " + Number(proxy.sol.slot).toLocaleString("en-US")
        ],
        credit: esc(proxy.sol.credit || "Public Solana RPC. Not affiliated.")
      };
    } else if (scope === "all" || scope === "SOL") {
      next.SOL = next.SOL || { lines: ["unavailable"], credit: "Public Solana RPC unavailable." };
    }
    if (proxy && proxy.prl && !proxy.prl.unavailable) {
      next.PRL = {
        lines: [
          "Height " + Number(proxy.prl.height).toLocaleString("en-US"),
          "Hashrate difficulty-derived, unconfirmed"
        ],
        credit: esc(proxy.prl.credit || "pearlchain.live. Not affiliated.")
      };
    } else if (scope === "all" || scope === "PRL") {
      next.PRL = next.PRL || { lines: ["n/a"], credit: "No Pearl chain reading." };
    }
    next.stale = !!(proxy && proxy.stale);
    state.chain = next;
    save("alpha.chain.v1", next);
    paintChain(scope || "all");
  }

  function stopPolls() {
    pollIds.forEach(function (id) { clearInterval(id); });
    pollIds = [];
  }

  function startPolls() {
    stopPolls();
    if (document.hidden) return;
    if (document.getElementById("ticker")) {
      pollIds.push(setInterval(function () { pullTicker(false); }, TICKER_MS));
    }
    if (document.getElementById("chips")) {
      pollIds.push(setInterval(pullChips, CHIPS_MS));
    }
    if (document.getElementById("markets-body")) {
      pollIds.push(setInterval(pullMarkets, MARKETS_MS));
    }
    if (document.getElementById("chain-panel")) {
      pollIds.push(setInterval(pullChain, CHAIN_MS));
    }
  }

  function resumeShown() {
    if (document.hidden) return;
    if (document.getElementById("ticker")) pullTicker(false);
    if (document.getElementById("chips") && Date.now() - lastChips >= CHIPS_MS) pullChips();
    if (document.getElementById("markets-body") && Date.now() - lastMarkets >= MARKETS_MS) pullMarkets();
    if (document.getElementById("chain-panel") && Date.now() - lastChain >= CHAIN_MS) pullChain();
  }

  function boot() {
    state.ticker = load("alpha.ticker.v1");
    state.chips = load("alpha.chips.v1") || {};
    var storedMarkets = load("alpha.markets.v1");
    if (storedMarkets && storedMarkets.rows) {
      state.markets = { rows: storedMarkets.rows, stale: true, at: storedMarkets.at };
    }
    var storedChart = load("alpha.chart.v1");
    if (storedChart && storedChart.key && storedChart.series) {
      state.chart[storedChart.key] = { at: storedChart.at, series: storedChart.series };
    }
    state.chain = load("alpha.chain.v1");
    if (state.ticker) paintTicker(state.ticker, true);
    paintChips();
    paintMarkets();
    var chainPanel = document.getElementById("chain-panel");
    if (chainPanel && state.chain) paintChain(chainPanel.getAttribute("data-chain") || "all");
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) {
        stopPolls();
        return;
      }
      resumeShown();
      startPolls();
    });
    if (document.hidden) return;
    if (document.getElementById("ticker")) pullTicker(true);
    if (document.getElementById("chips")) pullChips();
    if (document.getElementById("markets-body")) setTimeout(pullMarkets, 1500);
    if (document.getElementById("chain-panel")) pullChain();
    startPolls();
  }

  function readSecurities() {
    var node = document.getElementById("alpha-securities");
    if (!node) return [];
    try {
      var data = JSON.parse(node.textContent);
      return Array.isArray(data) ? data : [];
    } catch (err) {
      return [];
    }
  }

  function coinMap() {
    var map = {};
    readSecurities().forEach(function (row) {
      if (row && row.sym && row.cg && row.chart === "crypto") map[row.sym] = row.cg;
    });
    return Object.keys(map).length ? map : IDS;
  }

  window.AlphaDesk = {
    getJson: getJson,
    load: load,
    save: save,
    etDate: etDate,
    etClock: etClock,
    etStamp: etStamp,
    hostBlocked: hostBlocked,
    hostOf: hostOf,
    fmtPx: fmtPx,
    fmtPct: fmtPct,
    fmtCompact: fmtCompact,
    CG: CG,
    CHART_TTL: CHART_TTL,
    coinMap: coinMap,
    securities: readSecurities
  };

  document.addEventListener("click", function (event) {
    var link = event.target.closest("a[data-asset]");
    if (!link) return;
    var panel = document.getElementById("chart-panel");
    if (!panel || panel.getAttribute("data-locked") === "true") return;
    var sym = link.getAttribute("data-asset");
    var row = readSecurities().filter(function (item) { return item.sym === sym; })[0];
    if (!row || row.chart !== "crypto") return;
    event.preventDefault();
    window.dispatchEvent(new CustomEvent("alpha-asset", { detail: { symbol: sym } }));
  });

  window.addEventListener("alpha-asset", function (event) {
    var sym = event.detail && event.detail.symbol;
    if (!sym) return;
    var row = readSecurities().filter(function (item) { return item.sym === sym; })[0];
    var panel = document.getElementById("chain-panel");
    if (panel && row && row.chain) {
      panel.setAttribute("data-chain", row.chain);
      pullChain();
    }
    document.querySelectorAll("[data-asset]").forEach(function (el) {
      if (el.getAttribute("data-asset") === sym) el.setAttribute("aria-current", "true");
      else el.removeAttribute("aria-current");
    });
    var ticks = document.querySelectorAll("#ticker [data-symbol]");
    Array.prototype.forEach.call(ticks, function (el) {
      el.classList.toggle("tick-on", el.getAttribute("data-symbol") === sym);
    });
  });

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
