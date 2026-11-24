const path = require("path");
const logic = require(path.join(__dirname, "..", "static", "desk-logic.js"));
const assets = [
  { sym: "BTC", name: "Bitcoin", path: "/s/btc/", chart: "crypto" },
  { sym: "ETH", name: "Ether", path: "/s/eth/", chart: "crypto" },
  { sym: "PRL", name: "Pearl", path: "/s/prl/", chart: "crypto" },
  { sym: "UST10Y", name: "Treasury par yield, 10 year", path: "/s/ust10y/", chart: "rate" }
];
const index = {
  assets,
  notes: [{ title: "Pearl (PRL): real proof", summary: "Deep dive on Pearl", path: "/articles/2026-10-02-pearl/", ticker: "PRL", tags: ["PRL"], keywords: "pearl token chain" }],
  pages: [{ title: "Rates", path: "/#chips", words: "rates sofr treasury" }],
  codes: [{ code: "GP", title: "Price chart", example: "BTC GP", href: "/help/#codes" }]
};

function assert(cond, msg) {
  if (!cond) throw new Error(msg || "assertion failed");
}

const spec = logic.rangeSpec("1M", new Date("2026-10-03T17:00:00Z"));
assert(spec.live && spec.ohlcLabel === "4 hours", "1M bar size " + spec.ohlcLabel);
assert(logic.barLabel(spec, "candle") === "Bars: 4 hours", logic.barLabel(spec, "candle"));
assert(logic.rangeSpec("5Y").live === false, "5Y blocked");
assert(logic.rangeSpec("5Y").reason.indexOf("Needs more than 1 year") === 0, "5Y reason");

const daily = [];
for (let i = 0; i < 365; i++) daily.push({ time: i, value: 100 + i });
const ma = logic.sma(daily, 200);
assert(ma.length === 166, "ma200 length " + ma.length);
const cover = logic.maCoverage(365, 200);
assert(cover.partial && cover.note.indexOf("computed") >= 0, cover.note);

const rebased = logic.rebase([{ time: 1, value: 50 }, { time: 2, value: 75 }]);
assert(rebased[0].value === 100 && rebased[1].value === 150, "rebase");

const q = logic.parseChartQuery("?r=1Y&t=candle&ma=50,200&cmp=ETH&log=1");
assert(q.range === "1Y" && q.type === "candle" && q.log && q.ma.join() === "50,200" && q.cmp[0] === "ETH", JSON.stringify(q));

assert(logic.parseCommand("BTC GP", assets).href === "/s/btc/?r=1Y&t=line", "GP");
assert(logic.parseCommand("BTC GIP", assets).href === "/s/btc/?r=1D&t=line", "GIP");
assert(logic.parseCommand("BTC GPO", assets).href === "/s/btc/?r=1Y&t=bar", "GPO");
assert(logic.parseCommand("BTC GPC", assets).href === "/s/btc/?r=1Y&t=candle", "GPC");
assert(logic.parseCommand("COMP BTC ETH", assets).href.indexOf("cmp=ETH") > 0, "COMP");
assert(logic.parseCommand("AAPL GP", assets).kind === "unlicensed", "AAPL");
assert(logic.parseCommand("PRL CRYPTO DES", assets).href === "/s/prl/", "DES");

const pearl = logic.suggest(index, "pearl");
assert(pearl.some((row) => row.kind === "note") && pearl.some((row) => row.kind === "asset"), "pearl rows");
const prl = logic.suggest(index, "prl");
assert(prl.some((row) => row.href === "/s/prl/"), "prl asset");
const empty = logic.suggest(index, "spacex");
assert(empty.length === 1 && empty[0].title.indexOf("No notes or licensed data for spacex") === 0, empty[0].title);
const spacex = logic.resolveQuery(index, "spacex", assets);
assert(spacex.action === "stay", "spacex must not navigate");
assert(!spacex.href || spacex.href.indexOf("/s/btc") !== 0, "spacex href " + spacex.href);
assert(spacex.title.indexOf("No notes or licensed data for spacex") === 0, spacex.title);
const pearlGo = logic.resolveQuery(index, "pearl", assets);
assert(pearlGo.action === "go" && pearlGo.href, "pearl navigates");
const firstEsc = logic.escapeStep(true);
const secondEsc = logic.escapeStep(false);
assert(firstEsc.clear === true && firstEsc.close === false, "first Esc clears only");
assert(secondEsc.clear === false && secondEsc.close === true, "second Esc closes");
const zoom = logic.zoomLogical({ from: 0, to: 100 }, 1);
assert(zoom.to - zoom.from === 80, "zoom");

const fs = require("fs");
const vm = require("vm");
const assigns = [];
const sandbox = {
  console,
  URLSearchParams,
  fetch: function () { return Promise.resolve({ ok: false }); }
};
sandbox.window = {
  AlphaLogic: logic,
  location: {
    search: "",
    assign: function (href) { assigns.push(href); }
  }
};
sandbox.document = {
  querySelector: function () { return null; },
  getElementById: function () { return null; },
  addEventListener: function () {}
};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(__dirname, "..", "static", "search.js"), "utf8"), sandbox);
const choose = sandbox.window.AlphaSearch.choose;
assert(typeof choose === "function", "search.js must export choose");
choose({ kind: "empty", href: "/#ledger", title: "No notes or licensed data for spacex" });
assert(assigns.length === 0, "empty choose navigated to " + assigns.join(","));
choose({ kind: "asset", href: "/s/btc/", title: "Bitcoin" });
assert(assigns.length === 1 && assigns[0] === "/s/btc/", "asset choose " + assigns.join(","));
choose(null);
assert(assigns.length === 1, "null choose navigated");

// ---- /markets/ (P1) ------------------------------------------------------
function coin(id, symbol, name, price, d1, d7, cap) {
  return {
    id, symbol, name, current_price: price, market_cap: cap || 1e9, market_cap_rank: 1,
    price_change_percentage_24h_in_currency: d1, price_change_percentage_7d_in_currency: d7,
    price_change_percentage_24h: d1
  };
}
const rows = [
  coin("bitcoin", "btc", "Bitcoin", 90000, -2.5, -7.2, 1.8e12),
  coin("tether", "usdt", "Tether", 1, 0.01, 0.02),
  coin("usd-coin", "usdc", "USDC", 0.9996, 0.004, 0.01),
  coin("some-new-stable", "zusd", "Zeta Dollar", 1.0, 0.1, 0.2),
  coin("wrapped-bitcoin", "wbtc", "Wrapped Bitcoin", 90000, 9, 9),
  coin("tesla-xstock", "tslax", "Tesla xStock", 400, 12, 12),
  coin("pax-gold", "paxg", "PAX Gold", 4000, 30, 30),
  coin("pump", "pmp", "Pump", 0.5, 40, -20),
  coin("dump", "dmp", "Dump", 0.2, -30, 60),
  coin("flat", "flt", "Flat", 3, 0, 0),
  coin("nodata", "nd", "No Data", 3, null, 5)
];
const m24 = logic.topMovers(rows, "24h", 10);
assert(m24.gainers[0].id === "pump", "24h top gainer " + m24.gainers[0].id);
assert(m24.losers[0].id === "dump", "24h top loser " + m24.losers[0].id);
assert(m24.losers.map((r) => r.id).join() === "dump,bitcoin", "24h losers " + m24.losers.map((r) => r.id));
const skipped = ["tether", "usd-coin", "some-new-stable", "wrapped-bitcoin", "tesla-xstock", "pax-gold"];
skipped.forEach((id) => {
  assert(!m24.gainers.concat(m24.losers).some((r) => r.id === id), "not skipped: " + id);
});
assert(!m24.gainers.concat(m24.losers).some((r) => r.id === "flat"), "zero change is neither gainer nor loser");
assert(!m24.gainers.concat(m24.losers).some((r) => r.id === "nodata"), "missing 24h change is left out of 24h");
const m7 = logic.topMovers(rows, "7d", 10);
assert(m7.window === "7d" && m7.gainers[0].id === "dump", "7d top gainer " + m7.gainers[0].id);
assert(m7.gainers.some((r) => r.id === "nodata"), "7d uses its own field");
assert(m7.losers[0].id === "pump", "7d top loser");
assert(logic.topMovers(rows, "bogus", 10).window === "24h", "bad window falls back to 24h");
assert(logic.topMovers(rows, "24h", 1).gainers.length === 1, "count respected");
assert(logic.topMovers(null, "24h").considered === 0, "null rows");
const slim = logic.slimMarketRow({ id: "x", symbol: "x", name: "X", current_price: "2", price_change_percentage_24h: 3, image: "big", ath: 9 });
assert(slim.price_change_percentage_24h_in_currency === 3 && slim.current_price === 2 && slim.image === undefined, "slim row");

const baskets = [{ id: "layer-1", label: "Layer 1" }, { id: "meme-token", label: "Meme" }, { id: "gone", label: "Gone" }, { id: "ai", label: "AI" }];
const cats = [
  { id: "meme-token", name: "Meme", market_cap: 2e10, market_cap_change_24h: 5.5, volume_24h: 1e9, updated_at: "2026-11-24" },
  { id: "layer-1", name: "Layer 1 (L1)", market_cap: 1.7e12, market_cap_change_24h: -2.4, volume_24h: 5e10 },
  { id: "ai", name: "AI", market_cap: 1.7e10, market_cap_change_24h: null, volume_24h: 2e9 },
  { id: "world-liberty-financial-portfolio", name: "Portfolio", market_cap: 9e9, market_cap_change_24h: 135 }
];
const sec = logic.sectorRows(cats, baskets);
assert(sec.length === 3, "allowlist only, missing basket skipped: " + sec.length);
assert(!sec.some((r) => r.id.indexOf("portfolio") >= 0), "portfolio category never shown");
assert(sec[0].label === "Layer 1", "our label wins");
const byChange = logic.sortSectors(sec, "change").map((r) => r.id).join();
assert(byChange === "meme-token,layer-1,ai", "change sort, null last: " + byChange);
const byCap = logic.sortSectors(sec, "cap").map((r) => r.id).join();
assert(byCap === "layer-1,meme-token,ai", "cap sort " + byCap);

const dom = logic.dominance({ data: { market_cap_percentage: { btc: 58.5, eth: 10.01, usdt: 8.5 }, total_market_cap: { usd: 3e12 }, market_cap_change_percentage_24h_usd: -4.71, updated_at: 1795500000 } });
assert(Math.abs(dom.btc - 58.5) < 1e-9 && Math.abs(dom.eth - 10.01) < 1e-9, "dominance pct");
assert(Math.abs(dom.rest - 31.49) < 1e-9, "rest " + dom.rest);
assert(Math.abs(dom.btc_cap - 1.755e12) < 1, "btc cap " + dom.btc_cap);
assert(dom.change_24h === -4.71, "total change");
assert(logic.dominance({ data: { market_cap_percentage: {} } }) === null, "missing pct is null, not 0");
assert(logic.dominance({ data: { market_cap_percentage: { btc: 80, eth: 30 } } }) === null, "over 100 rejected");
assert(logic.dominance(null) === null, "null global");

assert(logic.nextRetryMs(0) === 15000 && logic.nextRetryMs(1) === 30000 && logic.nextRetryMs(9) === 120000, "retry ladder");

// Real CoinGecko payloads, if a probe saved them locally. Never committed.
const probes = { markets: "/tmp/cg_mk.json", cats: "/tmp/cg_cats.json", global: "/tmp/cg_global.json" };
if (Object.values(probes).every((p) => fs.existsSync(p))) {
  const live = JSON.parse(fs.readFileSync(probes.markets, "utf8"));
  const lm = logic.topMovers(live, "24h", 10);
  assert(lm.gainers.length + lm.losers.length > 0, "live movers empty");
  lm.gainers.concat(lm.losers).forEach((r) => {
    assert(!/wrapped|staked|xstock|bstock|tokeni[sz]ed|\bgold\b/i.test(r.name), "live leak " + r.name);
    assert(!(r.current_price > 0.97 && r.current_price < 1.03 && Math.abs(r.price_change_percentage_24h_in_currency || 0) < 2), "live peg leak " + r.id);
  });
  const ls = logic.sectorRows(JSON.parse(fs.readFileSync(probes.cats, "utf8")), require(path.join(__dirname, "..", "data", "markets-baskets.json")));
  assert(ls.length >= 15, "live baskets found " + ls.length);
  const ld = logic.dominance(JSON.parse(fs.readFileSync(probes.global, "utf8")));
  assert(ld && ld.btc > 30 && ld.btc < 80 && ld.eth > 3 && ld.eth < 30, "live dominance");
  console.log("live-probe-ok movers=" + lm.considered + " baskets=" + ls.length + " btc=" + ld.btc.toFixed(2) + " eth=" + ld.eth.toFixed(2));
}
console.log("logic-ok");
