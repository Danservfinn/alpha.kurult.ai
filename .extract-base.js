const { execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const dest = path.join(__dirname, ".orda-base");
const files = [
  "dist/styles.css",
  "dist/mark.svg",
  "dist/articles/2026-10-02-pearl/index.html"
];
for (const rel of files) {
  const buf = execFileSync("git", ["show", "976908a:" + rel], { maxBuffer: 8 * 1024 * 1024 });
  const out = path.join(dest, rel);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, buf);
  console.log("wrote", out, buf.length);
}
