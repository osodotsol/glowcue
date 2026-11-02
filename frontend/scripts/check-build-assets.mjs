// Fails the production build if temporary private imagery (or any reference to it) reached dist/.
// Run automatically by `npm run build`; also usable on its own: `node scripts/check-build-assets.mjs [distDir]`.
import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const dist = path.resolve(root, process.argv[2] ?? "dist");
const FORBIDDEN_NAME = /(^|[\\/])private([\\/]|$)|p1-hero|p2-consultation|p3-storytelling|glowcue-hero/i;
const FORBIDDEN_TEXT = ["/private/", "p1-hero", "p2-consultation", "p3-storytelling", "glowcue-hero"];
const TEXT_EXT = new Set([".html", ".js", ".mjs", ".css", ".json", ".txt", ".svg", ".webmanifest", ".map"]);

function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const full = path.join(dir, name);
    return statSync(full).isDirectory() ? [full, ...walk(full)] : [full];
  });
}

let entries;
try {
  entries = walk(dist);
} catch {
  console.error(`check-build-assets: no build output at ${dist}`);
  process.exit(1);
}

const problems = [];
for (const full of entries) {
  const rel = path.relative(dist, full);
  if (FORBIDDEN_NAME.test(rel)) problems.push(`private asset path in build: ${rel}`);
  if (TEXT_EXT.has(path.extname(full)) && statSync(full).isFile()) {
    const text = readFileSync(full, "utf8");
    for (const needle of FORBIDDEN_TEXT) {
      if (text.includes(needle)) problems.push(`${rel} references "${needle}"`);
    }
  }
}

if (problems.length) {
  console.error("check-build-assets: FAILED, temporary private imagery must not be published:");
  for (const p of problems) console.error(`  - ${p}`);
  process.exit(1);
}
console.log(`check-build-assets: OK (${entries.length} entries in ${path.relative(root, dist) || "."}, nothing private)`);
