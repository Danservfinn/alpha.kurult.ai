/* Pure desk logic. No DOM. Used by the chart, the search bar, and node tests. */
(function (root) {
  "use strict";

  var RANGES = ["1D", "5D", "1M", "3M", "6M", "YTD", "1Y", "5Y", "Max"];
  var BLOCKED_RANGE = "Needs more than 1 year of licensed history";
  var CLASS_WORDS = { CRYPTO: 1, CRNCY: 1, GOVT: 1, "M-MKT": 1, INDEX: 1 };
  var GROUP_ORDER = { Notes: 0, Assets: 1, Pages: 2, Codes: 3 };
  var CREDIT = "Data provided by CoinGecko";
  var CREDIT_URL = "https://www.coingecko.com/";

  function ytdStartMs(now) {
    var year = Number(new Intl.DateTimeFormat("en-US", {
      timeZone: "America/New_York",
      year: "numeric"
    }).format(now));
    return Date.UTC(year, 0, 1, 5, 0, 0);
  }

  function ytdDays(now) {
    return Math.max(1, Math.ceil((now.getTime() - ytdStartMs(now)) / 86400000));
  }

  function nearestDays(need) {
    var allowed = [1, 7, 14, 30, 90, 180, 365];
    var i;
    for (i = 0; i < allowed.length; i++) {
      if (allowed[i] >= need) return allowed[i];
    }
    return 365;
  }

  function intervalLabel(days, kind) {
    if (kind === "ohlc") {
      if (days <= 2) return "30 minutes";
      if (days <= 30) return "4 hours";
      return "4 days";
    }
    if (days <= 1) return "5 minutes";
    if (days <= 90) return "1 hour";
    return "1 day";
  }

  function rangeSpec(range, now) {
    now = now || new Date();
    if (range === "5Y" || range === "Max" || RANGES.indexOf(range) < 0) {
      return { range: range, live: false, reason: BLOCKED_RANGE };
    }
    var marketDays = range === "1D" ? 1
      : range === "5D" ? 5
      : range === "1M" ? 30
      : range === "3M" ? 90
      : range === "6M" ? 180
      : range === "1Y" ? 365
      : ytdDays(now);
    var ohlcDays = range === "1D" ? 1
      : range === "5D" ? 7
      : range === "1M" ? 30
      : range === "3M" ? 90
      : range === "6M" ? 180
      : range === "1Y" ? 365
      : nearestDays(marketDays);
    var trimMs = 0;
    if (range === "5D") trimMs = now.getTime() - 5 * 86400000;
    if (range === "YTD") trimMs = ytdStartMs(now);
    return {
      range: range,
      live: true,
      marketDays: marketDays,
      ohlcDays: ohlcDays,
      lineLabel: intervalLabel(marketDays, "line"),
      ohlcLabel: intervalLabel(ohlcDays, "ohlc"),
      trimMs: trimMs
    };
  }

  function barLabel(spec, type) {
    if (!spec || !spec.live) return "";
    var size = type === "line" ? spec.lineLabel : spec.ohlcLabel;
    return "Bars: " + size;
  }

  function toSeconds(ms) {
    return Math.floor(Number(ms) / 1000);
  }

  function dedupe(rows) {
    var seen = {};
    var out = [];
    rows.forEach(function (row) {
      if (!row || !Number.isFinite(row.time)) return;
      seen[row.time] = row;
    });
    Object.keys(seen).sort(function (a, b) { return Number(a) - Number(b); }).forEach(function (key) {
      out.push(seen[key]);
    });
    return out;
  }

  function trimRows(rows, trimMs) {
    if (!trimMs) return rows;
    var cut = toSeconds(trimMs);
    return rows.filter(function (row) { return row.time >= cut; });
  }

  function lineFromMarket(data, trimMs) {
    var prices = data && data.prices;
    if (!Array.isArray(prices)) return [];
    return trimRows(dedupe(prices.map(function (row) {
      return { time: toSeconds(row[0]), value: Number(row[1]) };
    }).filter(function (row) { return Number.isFinite(row.value); })), trimMs);
  }

  function volumeFromMarket(data, trimMs) {
    var vols = data && data.total_volumes;
    if (!Array.isArray(vols)) return [];
    return trimRows(dedupe(vols.map(function (row) {
      return { time: toSeconds(row[0]), value: Number(row[1]) };
    }).filter(function (row) { return Number.isFinite(row.value); })), trimMs);
  }

  function ohlcFromApi(data, trimMs) {
    if (!Array.isArray(data)) return [];
    return trimRows(dedupe(data.map(function (row) {
      return {
        time: toSeconds(row[0]),
        open: Number(row[1]),
        high: Number(row[2]),
        low: Number(row[3]),
        close: Number(row[4])
      };
    }).filter(function (row) {
      return Number.isFinite(row.open) && Number.isFinite(row.high) && Number.isFinite(row.low) && Number.isFinite(row.close);
    })), trimMs);
  }

  function sma(points, period) {
    var out = [];
    var sum = 0;
    var i;
    if (!points || period < 1) return out;
    for (i = 0; i < points.length; i++) {
      sum += points[i].value;
      if (i >= period) sum -= points[i - period].value;
      if (i >= period - 1) out.push({ time: points[i].time, value: sum / period });
    }
    return out;
  }

  function maCoverage(dailyCount, period) {
    if (dailyCount < period) {
      return { defined: false, note: "MA " + period + " (computed). Not enough daily closes." };
    }
    var definedDays = dailyCount - period + 1;
    var partial = definedDays < dailyCount;
    return {
      defined: true,
      partial: partial,
      definedDays: definedDays,
      note: partial
        ? "MA " + period + " (computed). Partial coverage: defined after " + period + " daily closes."
        : "MA " + period + " (computed)."
    };
  }

  function rebase(points) {
    if (!points || !points.length || !points[0].value) return [];
    var base = points[0].value;
    return points.map(function (row) {
      return { time: row.time, value: (row.value / base) * 100 };
    });
  }

  function pctSinceStart(points, time) {
    if (!points || !points.length || !points[0].value) return null;
    var row = null;
    var i;
    for (i = 0; i < points.length; i++) {
      if (points[i].time <= time) row = points[i];
      else break;
    }
    if (!row) row = points[0];
    return ((row.value / points[0].value) - 1) * 100;
  }

  function parseChartQuery(search) {
    var text = String(search || "");
    if (text.charAt(0) === "?") text = text.slice(1);
    var q = new URLSearchParams(text);
    var range = q.get("r") || "1Y";
    if (RANGES.indexOf(range) < 0) range = "1Y";
    var type = q.get("t") || "line";
    if (type === "candles") type = "candle";
    if (type === "bars") type = "bar";
    if (["line", "candle", "bar"].indexOf(type) < 0) type = "line";
    var ma = String(q.get("ma") || "").split(",").filter(function (item) {
      return item === "50" || item === "200";
    });
    var cmp = String(q.get("cmp") || "").split(",").map(function (item) {
      return item.trim().toUpperCase();
    }).filter(Boolean).slice(0, 4);
    return {
      range: range,
      type: type,
      ma: ma,
      cmp: cmp,
      log: q.get("log") === "1",
      sym: String(q.get("sym") || "").toUpperCase()
    };
  }

  function chartQuery(state, includeSym) {
    var q = new URLSearchParams();
    q.set("r", state.range || "1Y");
    q.set("t", state.type || "line");
    if (state.ma && state.ma.length) q.set("ma", state.ma.join(","));
    if (state.cmp && state.cmp.length) q.set("cmp", state.cmp.slice(0, 4).join(","));
    if (state.log) q.set("log", "1");
    if (includeSym && state.sym) q.set("sym", state.sym);
    return q.toString();
  }

  function zoomLogical(range, direction) {
    if (!range) return null;
    var span = range.to - range.from;
    if (!(span > 0)) return range;
    var mid = (range.from + range.to) / 2;
    var next = direction > 0 ? Math.max(5, span * 0.8) : span * 1.25;
    return { from: mid - next / 2, to: mid + next / 2 };
  }

  function assetBySym(assets, sym) {
    var want = String(sym || "").toUpperCase();
    var i;
    var list = assets || [];
    for (i = 0; i < list.length; i++) {
      if (String(list[i].sym || "").toUpperCase() === want) return list[i];
    }
    return null;
  }

  function parseCommand(raw, assets) {
    var text = String(raw || "").trim().replace(/\s+/g, " ");
    if (!text) return null;
    var upper = text.toUpperCase();
    var bare = {
      HELP: "/help/",
      TOP: "/#ledger",
      GMM: "/#markets-panel",
      MOST: "/#markets-panel",
      BTMM: "/#chips"
    };
    if (bare[upper]) return { kind: "page", href: bare[upper], code: upper };
    var low = text.toLowerCase();
    var chartWord = low.match(/^(?:chart|price chart)\s+([a-z0-9.]+)$/);
    if (chartWord) {
      var named = chartWord[1].toUpperCase();
      if (!assetBySym(assets, named)) return { kind: "unlicensed", symbol: named, code: "chart" };
      return { kind: "chart", href: "/s/" + named.toLowerCase() + "/?r=1Y&t=line", symbol: named, code: "chart" };
    }
    var parts = upper.split(" ").filter(function (part) { return !CLASS_WORDS[part]; });
    if (parts[0] === "COMP" && parts.length >= 2) {
      var primary = parts[1];
      if (!assetBySym(assets, primary)) return { kind: "unlicensed", symbol: primary, code: "COMP" };
      var extra = parts.slice(2, 6);
      var href = "/s/" + primary.toLowerCase() + "/?r=1Y&t=line";
      if (extra.length) href += "&cmp=" + extra.join(",");
      return { kind: "chart", href: href, symbol: primary, code: "COMP" };
    }
    if (parts.length === 2) {
      var fn = parts[1];
      var sym = parts[0];
      if (fn !== "GP" && fn !== "GIP" && fn !== "GPO" && fn !== "GPC" && fn !== "DES") return null;
      if (!assetBySym(assets, sym)) return { kind: "unlicensed", symbol: sym, code: fn };
      var path = "/s/" + sym.toLowerCase() + "/";
      if (fn === "GIP") path += "?r=1D&t=line";
      else if (fn === "GPO") path += "?r=1Y&t=bar";
      else if (fn === "GPC") path += "?r=1Y&t=candle";
      else if (fn === "GP") path += "?r=1Y&t=line";
      return { kind: "chart", href: path, symbol: sym, code: fn };
    }
    return null;
  }

  function tokensOf(query) {
    return String(query || "").toLowerCase().trim().split(/\s+/).filter(Boolean);
  }

  function hasAll(hay, tokens) {
    var text = String(hay || "").toLowerCase();
    return tokens.every(function (token) { return text.indexOf(token) >= 0; });
  }

  function suggest(index, query) {
    var q = String(query || "").trim();
    var tokens = tokensOf(q);
    if (!tokens.length) return [];
    var needle = q.toLowerCase();
    var rows = [];
    (index.assets || []).forEach(function (asset) {
      var sym = String(asset.sym || "").toLowerCase();
      var name = String(asset.name || "").toLowerCase();
      var klass = String(asset["class"] || "").toLowerCase();
      var score = 0;
      if (sym === needle || name === needle) score = 100;
      else if (sym.indexOf(needle) === 0 || name.indexOf(needle) === 0) score = 92;
      else if (hasAll(sym + " " + name + " " + klass, tokens)) score = 70;
      if (score) {
        rows.push({
          group: "Assets",
          score: score,
          title: asset.sym + " " + asset.name,
          href: asset.path,
          kind: "asset"
        });
      }
    });
    (index.notes || []).forEach(function (note) {
      var title = String(note.title || "");
      var summary = String(note.summary || "");
      var tags = (note.tags || []).join(" ");
      var ticker = String(note.ticker || "");
      var body = String(note.keywords || "");
      var score = 0;
      if (ticker && (ticker.toLowerCase() === needle || ticker.toLowerCase().indexOf(needle) === 0)) score = 96;
      if (hasAll(title, tokens)) score = Math.max(score, 88);
      if (hasAll(summary + " " + tags, tokens)) score = Math.max(score, 64);
      if (hasAll(body, tokens)) score = Math.max(score, 42);
      if (score) {
        rows.push({
          group: "Notes",
          score: score,
          title: title,
          href: note.path,
          kind: "note"
        });
      }
    });
    (index.pages || []).forEach(function (page) {
      var bag = (page.title || "") + " " + (page.words || "");
      if (!hasAll(bag, tokens)) return;
      var score = String(page.title || "").toLowerCase().indexOf(needle) === 0 ? 80 : 55;
      rows.push({
        group: "Pages",
        score: score,
        title: page.title,
        href: page.path,
        kind: "page"
      });
    });
    (index.codes || []).forEach(function (code) {
      var bag = (code.code || "") + " " + (code.title || "") + " " + (code.example || "");
      if (!hasAll(bag, tokens) && String(code.code || "").toLowerCase().indexOf(needle) !== 0) return;
      rows.push({
        group: "Codes",
        score: 30,
        title: code.code + " " + code.title,
        href: code.href || "/help/#codes",
        kind: "code"
      });
    });
    rows.sort(function (a, b) { return b.score - a.score; });
    var top = rows.slice(0, 8);
    if (!top.length) {
      return [{
        group: "Notes",
        score: 0,
        title: "No notes or licensed data for " + q,
        href: "/#ledger",
        kind: "empty"
      }];
    }
    return top;
  }

  function bestRow(rows) {
    var best = null;
    (rows || []).forEach(function (row) {
      if (row.kind === "empty") return;
      if (!best || row.score > best.score) best = row;
    });
    return best || (rows && rows[0]) || null;
  }

  function groupRank(name) {
    return GROUP_ORDER[name] == null ? 9 : GROUP_ORDER[name];
  }

  var api = {
    RANGES: RANGES,
    BLOCKED_RANGE: BLOCKED_RANGE,
    CREDIT: CREDIT,
    CREDIT_URL: CREDIT_URL,
    ytdStartMs: ytdStartMs,
    ytdDays: ytdDays,
    rangeSpec: rangeSpec,
    barLabel: barLabel,
    lineFromMarket: lineFromMarket,
    volumeFromMarket: volumeFromMarket,
    ohlcFromApi: ohlcFromApi,
    sma: sma,
    maCoverage: maCoverage,
    rebase: rebase,
    pctSinceStart: pctSinceStart,
    parseChartQuery: parseChartQuery,
    chartQuery: chartQuery,
    zoomLogical: zoomLogical,
    parseCommand: parseCommand,
    suggest: suggest,
    bestRow: bestRow,
    groupRank: groupRank,
    assetBySym: assetBySym
  };

  root.AlphaLogic = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
