const http = require("http");
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

const root = path.join(__dirname, "dist");
const port = 8773;
const chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

const types = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".svg": "image/svg+xml", ".json": "application/json" };
const server = http.createServer((req, res) => {
  let rel = decodeURIComponent(new URL(req.url, "http://127.0.0.1").pathname);
  if (rel.endsWith("/")) rel += "index.html";
  const file = path.join(root, rel);
  fs.readFile(file, (err, buf) => {
    if (err) { res.writeHead(404); res.end("missing"); return; }
    res.writeHead(200, { "content-type": types[path.extname(file)] || "application/octet-stream", "cache-control": "no-cache" });
    res.end(buf);
  });
});

function cdp(ws, id, method, params) {
  return new Promise((resolve) => {
    const onMsg = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id === id) {
        ws.removeEventListener("message", onMsg);
        resolve(msg);
      }
    };
    ws.addEventListener("message", onMsg);
    ws.send(JSON.stringify({ id, method, params }));
  });
}

async function measure(width, height, pagePath) {
  const profile = "/tmp/orda095-cdp-" + width + "x" + height + "-" + pagePath.replace(/\W/g, "");
  fs.rmSync(profile, { recursive: true, force: true });
  const dbg = 9333 + Math.floor(Math.random() * 200);
  const child = spawn(chrome, [
    "--headless=new",
    "--disable-gpu",
    "--no-first-run",
    "--remote-debugging-port=" + dbg,
    "--user-data-dir=" + profile,
    "--window-size=" + width + "," + height
  ], { stdio: "ignore" });
  let version;
  for (let i = 0; i < 40; i++) {
    try {
      version = await fetch("http://127.0.0.1:" + dbg + "/json/version").then((r) => r.json());
      break;
    } catch (err) {
      await new Promise((r) => setTimeout(r, 100));
    }
  }
  if (!version) throw new Error("chrome did not open");
  const targets = await fetch("http://127.0.0.1:" + dbg + "/json/list").then((r) => r.json());
  const page = targets.find((t) => t.type === "page");
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener("open", resolve);
    ws.addEventListener("error", reject);
  });
  let seq = 1;
  await cdp(ws, seq++, "Emulation.setDeviceMetricsOverride", {
    width, height, deviceScaleFactor: 1, mobile: true
  });
  await cdp(ws, seq++, "Page.enable", {});
  await cdp(ws, seq++, "Page.navigate", { url: "http://127.0.0.1:" + port + pagePath });
  await new Promise((r) => setTimeout(r, 600));
  const expr = `(() => {
    const box = (sel) => {
      const el = document.querySelector(sel);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      const s = getComputedStyle(el);
      return { top: Math.round(r.top), bottom: Math.round(r.bottom), h: Math.round(r.height), w: Math.round(r.width), display: s.display };
    };
    const help = document.querySelector("a.fnkey[href='/help/']");
    const crumb = document.querySelector(".crumbs a");
    const plot = document.querySelector(".chart-plot");
    const desk = document.querySelector(".desk-grid");
    return {
      inner: window.innerWidth,
      scroll: document.documentElement.scrollWidth,
      mast: box(".masthead"),
      fnkeys: box(".fnkeys"),
      search: box(".desk-search"),
      toggle: box(".search-toggle"),
      jump: box(".asset-jump"),
      help: help ? { h: Math.round(help.getBoundingClientRect().height), w: Math.round(help.getBoundingClientRect().width) } : null,
      crumb: crumb ? { h: Math.round(crumb.getBoundingClientRect().height), w: Math.round(crumb.getBoundingClientRect().width) } : null,
      notice: box(".notice"),
      panelHead: box(".article .panel-head"),
      main: box("main"),
      call: box(".callstrip"),
      keys: box(".keystrip"),
      position: box(".position-box"),
      touch: plot ? getComputedStyle(plot).touchAction : null,
      cols: desk ? getComputedStyle(desk).gridTemplateColumns : null
    };
  })()`;
  const result = await cdp(ws, seq++, "Runtime.evaluate", { expression: expr, returnByValue: true });
  ws.close();
  child.kill();
  return { width, height, pagePath, value: result.result && result.result.result && result.result.result.value, error: result.result && result.result.exceptionDetails };
}

server.listen(port, "127.0.0.1", async () => {
  try {
    const pages = [
      [375, 667, "/articles/2026-10-02-pearl/"],
      [1440, 900, "/articles/2026-10-02-pearl/"],
      [1440, 900, "/"]
    ];
    const out = [];
    for (const row of pages) out.push(await measure(row[0], row[1], row[2]));
    console.log(JSON.stringify(out, null, 2));
  } catch (err) {
    console.error(err);
    process.exitCode = 1;
  } finally {
    server.close();
    process.exit();
  }
});
