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
console.log("logic-ok");
