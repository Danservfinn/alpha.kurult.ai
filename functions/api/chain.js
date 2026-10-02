/**
 * Chain facts that have no browser CORS, or that must not fan out per visitor.
 * Hardcoded upstreams. Not an open proxy.
 * BTC height and fees stay in the browser (mempool.space, Blockstream fallback).
 */

async function fetchJson(url, init) {
  var wait = 300;
  var last = 0;
  for (var attempt = 0; attempt < 3; attempt++) {
    var res = await fetch(url, Object.assign({ signal: AbortSignal.timeout(8000) }, init || {}));
    if (res.ok) return res.json();
    last = res.status;
    if (res.status !== 429 && res.status < 500) break;
    var retryAfter = Number(res.headers.get("retry-after"));
    var delay = Number.isFinite(retryAfter) && retryAfter > 0 ? Math.min(retryAfter * 1000, 1500) : wait;
    if (attempt < 2) {
      await new Promise(function (resolve) {
        setTimeout(resolve, delay);
      });
      wait = Math.min(wait * 2, 1500);
    }
  }
  throw new Error("upstream " + last);
}

async function ethGas() {
  var body = JSON.stringify({ jsonrpc: "2.0", id: 1, method: "eth_gasPrice", params: [] });
  var heightBody = JSON.stringify({ jsonrpc: "2.0", id: 1, method: "eth_blockNumber", params: [] });
  var headers = { "content-type": "application/json", Accept: "application/json" };
  var url = "https://ethereum-rpc.publicnode.com";
  var gas = await fetchJson(url, { method: "POST", headers: headers, body: body });
  var tip = await fetchJson(url, { method: "POST", headers: headers, body: heightBody });
  var wei = Number(gas.result);
  var block = Number(tip.result);
  if (!Number.isFinite(wei) || !Number.isFinite(block)) throw new Error("eth shape");
  return {
    unavailable: false,
    block: block,
    gas_gwei: Math.round((wei / 1e9) * 100) / 100,
    source: "Public Ethereum RPC (publicnode)",
    source_url: "https://ethereum-rpc.publicnode.com",
    credit: "Gas and height from a public Ethereum RPC. Not affiliated.",
  };
}

async function solEpoch() {
  var payload = JSON.stringify({ jsonrpc: "2.0", id: 1, method: "getEpochInfo" });
  var data = await fetchJson("https://api.mainnet-beta.solana.com", {
    method: "POST",
    headers: { "content-type": "application/json", Accept: "application/json" },
    body: payload,
  });
  var result = data && data.result;
  if (!result || !Number.isFinite(result.epoch)) throw new Error("sol shape");
  var slots = Number(result.slotsInEpoch) || 0;
  var index = Number(result.slotIndex) || 0;
  return {
    unavailable: false,
    epoch: result.epoch,
    slot: result.absoluteSlot,
    progress: slots ? Math.round((index / slots) * 1000) / 10 : null,
    source: "Solana public mainnet RPC",
    source_url: "https://api.mainnet-beta.solana.com",
    credit: "Epoch from the public Solana RPC. Not affiliated.",
  };
}

async function pearlStats() {
  var data = await fetchJson("https://pearlchain.live/api/explorer/stats", {
    headers: {
      Accept: "application/json",
      "User-Agent": "alpha.kurult.ai/1.0 (research desk; keyless)",
    },
  });
  if (!data || !Number.isFinite(data.blockHeight)) throw new Error("pearl shape");
  return {
    unavailable: false,
    height: data.blockHeight,
    difficulty: data.difficulty,
    hashrate: data.networkHashPs,
    hash_note: data.hashUnitNote || "difficulty-derived, not measured",
    source: "pearlchain.live",
    source_url: "https://pearlchain.live/",
    credit: "Pearl chain stats from pearlchain.live. Hashrate is difficulty-derived and unconfirmed. Not affiliated.",
  };
}

async function safe(fn) {
  try {
    return await fn();
  } catch (err) {
    return { unavailable: true };
  }
}

function jsonResponse(body, cacheControl) {
  return new Response(JSON.stringify(body), {
    status: 200,
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
    if (cached && cached.ok && Date.now() - cached.stored_at < 15000) {
      return jsonResponse(cached, "public, max-age=15");
    }
  }
  var eth = await safe(ethGas);
  var sol = await safe(solEpoch);
  var prl = await safe(pearlStats);
  var any = !eth.unavailable || !sol.unavailable || !prl.unavailable;
  if (!any && hit) {
    var stale = await hit.json();
    stale.stale = true;
    return jsonResponse(stale, "public, max-age=15");
  }
  var body = {
    ok: any,
    stale: false,
    stored_at: Date.now(),
    eth: eth,
    sol: sol,
    prl: prl,
  };
  var fresh = jsonResponse(body, "public, max-age=15");
  if (any) {
    try {
      await cache.put(key, fresh.clone());
    } catch (err) {
      /* edge cache is optional */
    }
  }
  return fresh;
}
