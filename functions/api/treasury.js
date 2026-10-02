/**
 * Treasury daily par yields. US government work. No key.
 * Hardcoded upstream. Not an open proxy.
 */
var TREASURY_URL = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value=2026";

function field(block, tag) {
  var nullish = new RegExp("<d:" + tag + "[^>]*m:null=\"true\"", "i");
  if (nullish.test(block)) return null;
  var match = block.match(new RegExp("<d:" + tag + "[^>]*>([^<]*)</d:" + tag + ">", "i"));
  if (!match) return null;
  var raw = match[1].trim();
  if (!raw) return null;
  return raw;
}

function num(block, tag) {
  var raw = field(block, tag);
  if (raw == null) return null;
  var n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

function parseYields(xml) {
  var parts = String(xml).split("<entry>");
  var rows = [];
  for (var i = 1; i < parts.length; i++) {
    var block = parts[i];
    var date = field(block, "NEW_DATE");
    if (!date) continue;
    var row = {
      date: date.slice(0, 10),
      ust_2y: num(block, "BC_2YEAR"),
      ust_10y: num(block, "BC_10YEAR"),
    };
    if (row.ust_2y == null && row.ust_10y == null) continue;
    rows.push(row);
  }
  rows.sort(function (a, b) {
    return a.date < b.date ? -1 : a.date > b.date ? 1 : 0;
  });
  return rows.length ? rows[rows.length - 1] : null;
}

async function fetchUpstream() {
  var wait = 400;
  var last = 0;
  for (var attempt = 0; attempt < 3; attempt++) {
    var res = await fetch(TREASURY_URL, {
      headers: {
        Accept: "application/xml, text/xml, */*",
        "User-Agent": "alpha.kurult.ai/1.0 (research desk; keyless)",
      },
      signal: AbortSignal.timeout(12000),
    });
    if (res.ok) return parseYields(await res.text());
    last = res.status;
    if (res.status !== 429 && res.status < 500) break;
    var retryAfter = Number(res.headers.get("retry-after"));
    var delay = Number.isFinite(retryAfter) && retryAfter > 0 ? Math.min(retryAfter * 1000, 2000) : wait;
    if (attempt < 2) {
      await new Promise(function (resolve) {
        setTimeout(resolve, delay);
      });
      wait = Math.min(wait * 2, 2000);
    }
  }
  throw new Error("upstream " + last);
}

function jsonResponse(body, status, cacheControl) {
  return new Response(JSON.stringify(body), {
    status: status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": cacheControl,
      "x-content-type-options": "nosniff",
    },
  });
}

export async function onRequestGet(context) {
  var cache = caches.default;
  var url = new URL(context.request.url);
  url.search = "";
  var key = new Request(url.toString(), { method: "GET" });
  var hit = null;
  try {
    hit = await cache.match(key);
  } catch (err) {
    hit = null;
  }
  if (hit) {
    var cached = await hit.json();
    if (cached && cached.ok && Date.now() - cached.stored_at < 3600000) {
      return jsonResponse(cached, 200, "public, max-age=300, s-maxage=3600");
    }
  }
  try {
    var latest = await fetchUpstream();
    if (!latest) throw new Error("empty");
    var body = {
      ok: true,
      stale: false,
      stored_at: Date.now(),
      source: "U.S. Department of the Treasury",
      source_url: "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve",
      as_of: latest.date,
      ust_2y: latest.ust_2y,
      ust_10y: latest.ust_10y,
    };
    var fresh = jsonResponse(body, 200, "public, max-age=300, s-maxage=3600");
    try {
      await cache.put(key, fresh.clone());
    } catch (err) {
      /* edge cache is optional */
    }
    return fresh;
  } catch (err) {
    if (hit) {
      var stale = await hit.json();
      stale.stale = true;
      return jsonResponse(stale, 200, "public, max-age=60");
    }
    return jsonResponse(
      { ok: false, unavailable: true, stale: false, source: "U.S. Department of the Treasury" },
      200,
      "public, max-age=30"
    );
  }
}
