/* Interactive price chart. Library loads only when a chart is on the page. */
(function () {
  "use strict";

  var logic = window.AlphaLogic;
  var CG = "https://api.coingecko.com/api/v3";
  var VENDOR = "/vendor/lightweight-charts-5.2.1.js";
  var COMPARE_COLORS = ["#ffffff", "#5fa8ff", "#39d441", "#f8c800"];
  var libraryPromise = null;

  function desk() {
    var api = window.AlphaDesk;
    if (api && api.getJson) return api;
    return {
      getJson: function (url) {
        return fetch(url, { headers: { Accept: "application/json" } }).then(function (res) {
          if (!res.ok) {
            var err = new Error(String(res.status));
            err.status = res.status;
            throw err;
          }
          return res.json();
        });
      },
      load: function (key) {
        try {
          var raw = localStorage.getItem(key);
          return raw ? JSON.parse(raw) : null;
        } catch (err) {
          return null;
        }
      },
      save: function (key, value) {
        try { localStorage.setItem(key, JSON.stringify(value)); } catch (err) { /* private mode */ }
      },
      hostBlocked: function () { return false; },
      hostOf: function (url) {
        var match = String(url).match(/^https?:\/\/([^/]+)/i);
        return match ? match[1].toLowerCase() : "self";
      },
      etDate: function (ms) {
        return new Intl.DateTimeFormat("en-CA", { timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(ms));
      },
      etClock: function (ms) {
        return new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", hour: "2-digit", minute: "2-digit", hour12: false }).format(new Date(ms)) + " ET";
      },
      fmtPx: function (n) {
        if (!Number.isFinite(n)) return "n/a";
        var abs = Math.abs(n);
        var digits = abs >= 1000 ? 2 : abs >= 1 ? 2 : 4;
        return n.toLocaleString("en-US", { maximumFractionDigits: digits });
      },
      fmtPct: function (n) {
        if (!Number.isFinite(n)) return "";
        return (n > 0 ? "+" : "") + n.toFixed(2) + "%";
      },
      CHART_TTL: 300000
    };
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

  function whenText(ms) {
    var api = desk();
    var date = api.etDate(ms);
    var clock = api.etClock(ms);
    return (date && clock) ? date + " " + clock : (clock || date || "");
  }

  function loadLibrary(panel) {
    if (window.LightweightCharts) return Promise.resolve(window.LightweightCharts);
    if (libraryPromise) return libraryPromise;
    function inject() {
      libraryPromise = new Promise(function (resolve, reject) {
        var script = document.createElement("script");
        script.src = VENDOR;
        script.defer = true;
        script.onload = function () { resolve(window.LightweightCharts); };
        script.onerror = function () { reject(new Error("chart library")); };
        document.head.appendChild(script);
      });
      return libraryPromise;
    }
    if (panel.getAttribute("data-lazy") === "true" && "IntersectionObserver" in window) {
      return new Promise(function (resolve, reject) {
        var io = new IntersectionObserver(function (entries) {
          if (!entries.some(function (entry) { return entry.isIntersecting; })) return;
          io.disconnect();
          inject().then(resolve, reject);
        }, { rootMargin: "100% 0px" });
        io.observe(panel);
      });
    }
    return inject();
  }

  function cachedGet(url) {
    var api = desk();
    var key = "alpha.cg.v1:" + url;
    var saved = api.load(key);
    var age = saved ? Date.now() - saved.at : Infinity;
    if (saved && age < (api.CHART_TTL || 300000)) {
      return Promise.resolve({ body: saved.body, stale: false, at: saved.at, fromCache: true });
    }
    if (api.hostBlocked && api.hostBlocked(api.hostOf(url))) {
      if (saved && age < 86400000) return Promise.resolve({ body: saved.body, stale: true, at: saved.at, fromCache: true });
      return Promise.reject(new Error("backoff"));
    }
    return api.getJson(url).then(function (body) {
      api.save(key, { at: Date.now(), body: body });
      return { body: body, stale: false, at: Date.now(), fromCache: false };
    }).catch(function (err) {
      if (saved && age < 86400000) return { body: saved.body, stale: true, at: saved.at, fromCache: true };
      throw err;
    });
  }

  function mount(panel) {
    var state = logic.parseChartQuery(window.location.search);
    var locked = panel.getAttribute("data-locked") === "true";
    var symbol = (panel.getAttribute("data-symbol") || state.sym || "BTC").toUpperCase();
    if (!locked && state.sym) symbol = state.sym;
    state.sym = symbol;
    if (!state.range) state.range = "1Y";
    var cg = panel.getAttribute("data-cg") || "";
    var name = panel.getAttribute("data-name") || symbol;
    var plot = panel.querySelector(".chart-plot");
    var legend = panel.querySelector(".chart-legend");
    var status = panel.querySelector(".chart-status");
    var barNode = panel.querySelector("[data-bar-size]");
    var chart = null;
    var priceSeries = null;
    var volumeSeries = null;
    var maSeries = {};
    var compareSeries = {};
    var pack = null;
    var crossIndex = -1;
    var home = panel.getAttribute("data-home") === "true";

    function setStatus(text) {
      if (status) status.textContent = text || "";
    }

    function syncUrl() {
      var next = logic.chartQuery(state, home);
      var path = window.location.pathname;
      if (window.history && window.history.replaceState) {
        window.history.replaceState(null, "", path + (next ? "?" + next : ""));
      }
    }

    function press(selector, value, attr) {
      panel.querySelectorAll(selector).forEach(function (btn) {
        var on = btn.getAttribute(attr) === value;
        if (btn.hasAttribute("aria-pressed")) btn.setAttribute("aria-pressed", on ? "true" : "false");
      });
    }

    function paintControls() {
      press("[data-range]", state.range, "data-range");
      press("[data-type]", state.type, "data-type");
      panel.querySelectorAll("[data-ma]").forEach(function (btn) {
        var on = state.ma.indexOf(btn.getAttribute("data-ma")) >= 0;
        btn.setAttribute("aria-pressed", on ? "true" : "false");
      });
      var logBtn = panel.querySelector("[data-log]");
      if (logBtn) logBtn.setAttribute("aria-pressed", state.log ? "true" : "false");
      var spec = logic.rangeSpec(state.range);
      if (barNode) barNode.textContent = logic.barLabel(spec, state.type);
    }

    function quote() {
      var saved = desk().load("alpha.ticker.v1");
      return saved && saved[symbol] ? saved[symbol] : null;
    }

    function paintHead() {
      var last = panel.querySelector(".chart-last");
      var asof = panel.querySelector(".chart-asof");
      var row = quote();
      if (last) {
        if (row && Number.isFinite(row.price)) {
          last.textContent = desk().fmtPx(row.price) + " " + desk().fmtPct(row.change);
        } else if (pack && pack.line.length) {
          last.textContent = desk().fmtPx(pack.line[pack.line.length - 1].value);
        }
      }
      if (asof && pack && pack.line.length) {
        asof.textContent = "as of " + whenText(pack.line[pack.line.length - 1].time * 1000);
      }
    }

    function legendHtml(point, active) {
      if (!pack) return "";
      var spec = logic.rangeSpec(state.range);
      var bits = [];
      var stamp = point ? whenText(point.time * 1000) : "";
      if (stamp) bits.push(stamp);
      if (state.type === "line" || state.cmp.length) {
        var price = point && point.value != null ? point.value : (pack.line.length ? pack.line[pack.line.length - 1].value : null);
        if (price != null && !state.cmp.length) bits.push("Price " + desk().fmtPx(price));
      } else if (point && point.open != null) {
        bits.push("O " + desk().fmtPx(point.open) + " H " + desk().fmtPx(point.high) + " L " + desk().fmtPx(point.low) + " C " + desk().fmtPx(point.close));
      }
      var vol = point && point.volume != null ? point.volume : null;
      if (vol == null && pack.volume.length) vol = pack.volume[pack.volume.length - 1].value;
      if (vol != null) bits.push("24h volume " + desk().fmtPx(vol));
      state.ma.forEach(function (period) {
        var cover = logic.maCoverage(pack.daily.length, Number(period));
        bits.push(cover.note);
      });
      if (state.cmp.length) {
        var primary = pack.line[0];
        var last = point && point.value != null ? point.value : (pack.line.length ? pack.line[pack.line.length - 1].value : null);
        if (primary && last != null) {
          bits.push(symbol + " " + ((last / primary.value) * 100).toFixed(1) + " (" + desk().fmtPct(((last / primary.value) - 1) * 100) + " since start)");
        }
        state.cmp.forEach(function (sym) {
          var series = pack.compare[sym] || [];
          if (!series.length) return;
          var at = point ? logic.pctSinceStart(series, point.time) : logic.pctSinceStart(series, series[series.length - 1].time);
          var shown = series[series.length - 1].value;
          bits.push(sym + " " + (shown / series[0].value * 100).toFixed(1) + " (" + desk().fmtPct(at) + " since start)");
        });
      }
      bits.push(logic.barLabel(spec, state.type));
      if (!active) bits.push("Last values");
      return bits.join(" · ");
    }

    function paintLegend(point, active) {
      if (legend) legend.textContent = legendHtml(point, active);
    }

    function applyScale() {
      if (!priceSeries) return;
      var mode = window.LightweightCharts.PriceScaleMode;
      var next = mode.Normal;
      if (state.cmp.length) next = mode.IndexedTo100;
      else if (state.log) next = mode.Logarithmic;
      priceSeries.priceScale().applyOptions({ mode: next });
    }

    function clearSeries() {
      if (!chart) return;
      [priceSeries, volumeSeries].concat(Object.values(maSeries), Object.values(compareSeries)).forEach(function (series) {
        if (series) chart.removeSeries(series);
      });
      priceSeries = null;
      volumeSeries = null;
      maSeries = {};
      compareSeries = {};
    }

    function draw() {
      if (!chart || !pack) return;
      var lc = window.LightweightCharts;
      clearSeries();
      var comparing = state.cmp.length > 0;
      var type = comparing ? "line" : state.type;
      if (type === "candle" && pack.ohlc.length) {
        priceSeries = chart.addSeries(lc.CandlestickSeries, {
          upColor: "#39d441",
          downColor: "#dc5d5e",
          borderUpColor: "#39d441",
          borderDownColor: "#dc5d5e",
          wickUpColor: "#39d441",
          wickDownColor: "#dc5d5e",
          priceLineColor: "#f1bd59"
        }, 0);
        priceSeries.setData(pack.ohlc);
      } else if (type === "bar" && pack.ohlc.length) {
        priceSeries = chart.addSeries(lc.BarSeries, {
          upColor: "#39d441",
          downColor: "#dc5d5e",
          priceLineColor: "#f1bd59"
        }, 0);
        priceSeries.setData(pack.ohlc);
      } else {
        var lineData = comparing ? logic.rebase(pack.line) : pack.line;
        priceSeries = chart.addSeries(lc.LineSeries, {
          color: "#f1bd59",
          lineWidth: 2,
          priceLineColor: "#f1bd59",
          lastValueVisible: true
        }, 0);
        priceSeries.setData(lineData);
      }
      volumeSeries = chart.addSeries(lc.HistogramSeries, {
        priceFormat: { type: "volume" },
        priceScaleId: "volume",
        lastValueVisible: false,
        priceLineVisible: false
      }, 1);
      var up = "rgba(57, 212, 65, 0.5)";
      var down = "rgba(220, 93, 94, 0.5)";
      var prev = null;
      volumeSeries.setData(pack.volume.map(function (row) {
        var rose = prev == null ? true : row.close == null ? row.value >= prev : row.close >= prev;
        prev = row.close == null ? row.value : row.close;
        return { time: row.time, value: row.value, color: rose ? up : down };
      }));
      volumeSeries.priceScale().applyOptions({ scaleMargins: { top: 0.15, bottom: 0 } });
      if (!comparing) {
        state.ma.forEach(function (period) {
          var points = logic.sma(pack.daily, Number(period));
          if (!points.length) return;
          var series = chart.addSeries(lc.LineSeries, {
            color: period === "200" ? "#5fa8ff" : "#ffffff",
            lineWidth: 1,
            priceLineVisible: false,
            lastValueVisible: false
          }, 0);
          series.setData(points);
          maSeries[period] = series;
        });
      }
      state.cmp.forEach(function (sym, i) {
        var points = pack.compare[sym];
        if (!points || !points.length) return;
        var series = chart.addSeries(lc.LineSeries, {
          color: COMPARE_COLORS[i % COMPARE_COLORS.length],
          lineWidth: 1,
          priceLineVisible: false,
          lastValueVisible: true
        }, 0);
        series.setData(logic.rebase(points));
        compareSeries[sym] = series;
      });
      applyScale();
      var panes = chart.panes();
      if (panes.length > 1 && plot) {
        var height = plot.clientHeight || 420;
        panes[0].setHeight(Math.round(height * 0.72));
        panes[1].setHeight(Math.round(height * 0.28));
      }
      chart.timeScale().fitContent();
      paintLegend(null, false);
      paintHead();
      panel.setAttribute("data-ready", "true");
    }

    function pointAt(time) {
      var source = (state.type === "line" || state.cmp.length) ? pack.line : pack.ohlc;
      var row = null;
      var i;
      for (i = 0; i < source.length; i++) {
        if (source[i].time <= time) row = source[i];
        else break;
      }
      if (!row) return null;
      var vol = null;
      for (i = 0; i < pack.volume.length; i++) {
        if (pack.volume[i].time <= time) vol = pack.volume[i].value;
        else break;
      }
      return {
        time: row.time,
        value: row.value != null ? row.value : row.close,
        open: row.open,
        high: row.high,
        low: row.low,
        close: row.close,
        volume: vol
      };
    }

    function ensureChart(lib) {
      if (chart) return;
      chart = lib.createChart(plot, {
        autoSize: true,
        layout: {
          background: { type: lib.ColorType.Solid, color: "#000000" },
          textColor: "#f1bd59",
          fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
          fontSize: 12,
          attributionLogo: true
        },
        grid: {
          vertLines: { color: "#1a2a55" },
          horzLines: { color: "#1a2a55" }
        },
        crosshair: {
          mode: lib.CrosshairMode.Normal,
          vertLine: { color: "#507098", style: lib.LineStyle.Dashed, labelBackgroundColor: "#f8c800" },
          horzLine: { color: "#507098", style: lib.LineStyle.Dashed, labelBackgroundColor: "#f8c800" }
        },
        rightPriceScale: { borderColor: "#1a2a55" },
        timeScale: { borderColor: "#1a2a55", timeVisible: true, secondsVisible: false },
        handleScroll: { mouseWheel: true, pressedMouseMove: true, horzTouchDrag: true, vertTouchDrag: false },
        handleScale: { mouseWheel: true, pinch: true, axisPressedMouseMove: true },
        kineticScroll: { touch: true, mouse: false }
      });
      chart.subscribeCrosshairMove(function (param) {
        if (!pack || !param || !param.time) {
          paintLegend(null, false);
          return;
        }
        var point = pointAt(typeof param.time === "number" ? param.time : 0);
        paintLegend(point, true);
      });
      plot.addEventListener("dblclick", function () { resetView(); });
      plot.addEventListener("keydown", onKey);
      panel.__chart = chart;
    }

    function resetView() {
      if (!chart) return;
      chart.timeScale().fitContent();
      if (priceSeries) priceSeries.priceScale().applyOptions({ autoScale: true });
    }

    function moveCrosshair(step) {
      if (!chart || !priceSeries || !pack) return;
      var source = (state.type === "line" || state.cmp.length) ? pack.line : pack.ohlc;
      if (!source.length) return;
      if (crossIndex < 0) crossIndex = source.length - 1;
      crossIndex = Math.max(0, Math.min(source.length - 1, crossIndex + step));
      var row = source[crossIndex];
      var price = row.value != null ? row.value : row.close;
      chart.setCrosshairPosition(price, row.time, priceSeries);
      paintLegend(pointAt(row.time), true);
    }

    function zoom(direction) {
      if (!chart) return;
      var range = chart.timeScale().getVisibleLogicalRange();
      var next = logic.zoomLogical(range, direction);
      if (next) chart.timeScale().setVisibleLogicalRange(next);
    }

    function onKey(event) {
      if (event.key === "ArrowLeft") { moveCrosshair(-1); event.preventDefault(); }
      else if (event.key === "ArrowRight") { moveCrosshair(1); event.preventDefault(); }
      else if (event.key === "+" || event.key === "=") { zoom(1); event.preventDefault(); }
      else if (event.key === "-" || event.key === "_") { zoom(-1); event.preventDefault(); }
      else if (event.key === "0") { resetView(); event.preventDefault(); }
    }

    function colorVolume(volume, closes) {
      var closeAt = {};
      closes.forEach(function (row) { closeAt[row.time] = row.value != null ? row.value : row.close; });
      return volume.map(function (row) {
        return { time: row.time, value: row.value, close: closeAt[row.time] };
      });
    }

    function pullOne(id, spec, wantOhlc) {
      var jobs = [cachedGet(CG + "/coins/" + id + "/market_chart?vs_currency=usd&days=" + spec.marketDays)];
      if (wantOhlc) jobs.push(cachedGet(CG + "/coins/" + id + "/ohlc?vs_currency=usd&days=" + spec.ohlcDays));
      return Promise.all(jobs).then(function (parts) {
        return { market: parts[0], ohlc: parts[1] || null };
      });
    }

    function loadData() {
      var spec = logic.rangeSpec(state.range);
      if (!spec.live) {
        setStatus(spec.reason);
        return Promise.resolve();
      }
      if (!cg) {
        setStatus("No licensed data for " + symbol);
        return Promise.resolve();
      }
      setStatus("Loading " + name + ".");
      var wantOhlc = state.type !== "line";
      var staleAt = 0;
      var stale = false;
      return pullOne(cg, spec, wantOhlc).then(function (primary) {
        stale = primary.market.stale;
        staleAt = primary.market.at;
        var line = logic.lineFromMarket(primary.market.body, spec.trimMs);
        var volume = colorVolume(logic.volumeFromMarket(primary.market.body, spec.trimMs), line);
        var ohlc = primary.ohlc ? logic.ohlcFromApi(primary.ohlc.body, spec.trimMs) : [];
        if (!line.length && !ohlc.length) throw new Error("empty");
        var dailyPromise = spec.marketDays === 365
          ? Promise.resolve(line)
          : cachedGet(CG + "/coins/" + cg + "/market_chart?vs_currency=usd&days=365").then(function (res) {
            if (res.stale) { stale = true; staleAt = res.at; }
            return logic.lineFromMarket(res.body, 0);
          });
        var extras = state.cmp.slice(0, 4);
        return dailyPromise.then(function (daily) {
          var compare = {};
          var chain = Promise.resolve();
          extras.forEach(function (sym) {
            chain = chain.then(function () {
              var row = logic.assetBySym(securities(), sym);
              if (!row || !row.cg || row.chart !== "crypto" || sym === symbol) return null;
              return cachedGet(CG + "/coins/" + row.cg + "/market_chart?vs_currency=usd&days=" + spec.marketDays).then(function (res) {
                if (res.stale) { stale = true; staleAt = res.at; }
                compare[sym] = logic.lineFromMarket(res.body, spec.trimMs);
              });
            });
          });
          return chain.then(function () {
            pack = { line: line, ohlc: ohlc, volume: volume, daily: daily, compare: compare };
            draw();
            if (stale) setStatus("Price source busy, showing data from " + whenText(staleAt) + ".");
            else setStatus("");
          });
        });
      }).catch(function () {
        setStatus("No licensed data for this range.");
        if (legend) legend.textContent = "No licensed data for this range.";
      });
    }

    function setSymbol(next) {
      var row = logic.assetBySym(securities(), next) || { sym: next, cg: panel.getAttribute("data-cg"), name: next, chart: "crypto" };
      if (row.chart && row.chart !== "crypto") {
        window.location.assign(row.path || ("/s/" + String(next).toLowerCase() + "/"));
        return;
      }
      symbol = String(next).toUpperCase();
      cg = row.cg || "";
      name = row.name || symbol;
      state.sym = symbol;
      state.cmp = state.cmp.filter(function (item) { return item !== symbol; });
      panel.setAttribute("data-symbol", symbol);
      var nameNode = panel.querySelector(".chart-name");
      var tickNode = panel.querySelector(".chart-ticker");
      if (nameNode) nameNode.textContent = name;
      if (tickNode) tickNode.textContent = symbol;
      syncUrl();
      paintControls();
      loadData();
    }

    panel.addEventListener("click", function (event) {
      var btn = event.target.closest("button");
      if (!btn || !panel.contains(btn)) return;
      if (btn.hasAttribute("data-range")) {
        var range = btn.getAttribute("data-range");
        var spec = logic.rangeSpec(range);
        if (!spec.live) {
          setStatus(spec.reason);
          return;
        }
        state.range = range;
      } else if (btn.hasAttribute("data-type")) {
        state.type = btn.getAttribute("data-type");
      } else if (btn.hasAttribute("data-ma")) {
        var period = btn.getAttribute("data-ma");
        var idx = state.ma.indexOf(period);
        if (idx >= 0) state.ma.splice(idx, 1);
        else state.ma.push(period);
        state.ma.sort();
      } else if (btn.hasAttribute("data-log")) {
        state.log = !state.log;
      } else if (btn.hasAttribute("data-reset")) {
        resetView();
        return;
      } else if (btn.hasAttribute("data-compare-toggle")) {
        var row = panel.querySelector(".compare-row");
        if (!row) return;
        var show = row.hidden;
        row.hidden = !show;
        btn.setAttribute("aria-expanded", show ? "true" : "false");
        return;
      } else if (btn.hasAttribute("data-vs-btc")) {
        if (symbol !== "BTC" && state.cmp.indexOf("BTC") < 0 && state.cmp.length < 4) state.cmp.push("BTC");
      } else if (btn.hasAttribute("data-cmp")) {
        var sym = btn.getAttribute("data-cmp");
        var at = state.cmp.indexOf(sym);
        if (at >= 0) state.cmp.splice(at, 1);
        else if (state.cmp.length < 4 && sym !== symbol) state.cmp.push(sym);
        else setStatus("4 extra series is the limit.");
      } else {
        return;
      }
      paintControls();
      syncUrl();
      loadData();
    });

    var add = panel.querySelector("[data-compare-add]");
    if (add) {
      add.addEventListener("keydown", function (event) {
        if (event.key !== "Enter") return;
        event.preventDefault();
        var raw = add.value.trim().toUpperCase();
        if (!raw) return;
        var row = logic.assetBySym(securities(), raw);
        if (!row || row.chart !== "crypto") {
          setStatus("No licensed data for " + raw);
          return;
        }
        if (state.cmp.length >= 4) {
          setStatus("4 extra series is the limit.");
          return;
        }
        if (row.sym !== symbol && state.cmp.indexOf(row.sym) < 0) state.cmp.push(row.sym);
        add.value = "";
        paintControls();
        syncUrl();
        loadData();
      });
    }

    window.addEventListener("alpha-asset", function (event) {
      if (locked) return;
      var next = event.detail && event.detail.symbol;
      if (!next || next === symbol) return;
      setSymbol(next);
    });

    paintControls();
    syncUrl();
    loadLibrary(panel).then(function (lib) {
      if (!lib || !plot) {
        setStatus("Chart library did not load.");
        return;
      }
      ensureChart(lib);
      return loadData();
    }).catch(function () {
      setStatus("Chart library did not load.");
    });

    panel.__setSymbol = setSymbol;
    panel.__state = state;
  }

  function boot() {
    if (!logic) return;
    document.querySelectorAll(".desk-chart").forEach(mount);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
