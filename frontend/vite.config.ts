import { rm } from "node:fs/promises";
import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

/**
 * public/private/ holds temporary, unlicensed-for-publication imagery (portraits, hero film) for local development
 * only. Vite copies the whole public/ folder into the build, so this plugin deletes dist/private after every
 * production build. The app never references those files in production (see USE_PRIVATE_ASSETS in ui.tsx), and
 * scripts/check-build-assets.mjs fails the build if anything private is still found.
 */
function excludePrivatePublicAssets(): Plugin {
  let outDir = "dist";
  return {
    name: "glowcue-exclude-private-assets",
    apply: "build",
    configResolved(config) {
      outDir = path.resolve(config.root, config.build.outDir);
    },
    async closeBundle() {
      await rm(path.join(outDir, "private"), { recursive: true, force: true });
    },
  };
}

export default defineConfig({
  plugins: [react(), tailwindcss(), excludePrivatePublicAssets()],
  server: { port: 5173, strictPort: true },
});
