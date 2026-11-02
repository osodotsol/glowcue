// Fails the production build if private imagery (or any reference to it) reached dist/, or if the published brand
// imagery is not exactly the approved set. Run automatically by `npm run build`; also usable on its own:
// `node scripts/check-build-assets.mjs [distDir]`.
import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const dist = path.resolve(root, process.argv[2] ?? "dist");

// 1. Nothing from frontend/public/private/ may be published, and nothing may point at it.
const FORBIDDEN_NAME = /(^|[\\/])private([\\/]|$)/i;
const FORBIDDEN_TEXT = ["/private/"];
const TEXT_EXT = new Set([".html", ".js", ".mjs", ".css", ".json", ".txt", ".svg", ".webmanifest", ".map"]);

// 2. dist/brand holds exactly the approved brand imagery: the two portraits and the hero film with its poster.
const BRAND_DIR = "brand";
const BRAND_FILES = new Set([
  "brand/portraits/p2-consultation.webp",
  "brand/portraits/p3-storytelling.webp",
  "brand/videos/glowcue-hero.mp4",
  "brand/videos/glowcue-hero-poster.webp",
]);

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
const brandFound = new Set();
for (const full of entries) {
  const rel = path.relative(dist, full).split(path.sep).join("/");
  if (FORBIDDEN_NAME.test(rel)) problems.push(`private asset path in build: ${rel}`);
  if (statSync(full).isFile() && rel.startsWith(`${BRAND_DIR}/`)) {
    if (BRAND_FILES.has(rel)) brandFound.add(rel);
    else problems.push(`unapproved file in ${BRAND_DIR}/: ${rel}`);
  }
  if (TEXT_EXT.has(path.extname(full)) && statSync(full).isFile()) {
    const text = readFileSync(full, "utf8");
    for (const needle of FORBIDDEN_TEXT) {
      if (text.includes(needle)) problems.push(`${rel} references "${needle}"`);
    }
  }
}
for (const required of BRAND_FILES) {
  if (!brandFound.has(required)) problems.push(`approved brand file missing from build: ${required}`);
}

if (problems.length) {
  console.error("check-build-assets: FAILED");
  for (const p of problems) console.error(`  - ${p}`);
  process.exit(1);
}
console.log(
  `check-build-assets: OK (${entries.length} entries in ${path.relative(root, dist) || "."}; ${brandFound.size} brand files; nothing private)`,
);
