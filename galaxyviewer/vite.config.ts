import { defineConfig } from "vite";

// GalaxyViewer Vite config — minimal, defaults are good.
export default defineConfig({
  base: "./",            // relative asset URLs so the build works on any host
  server: {
    port: 5173,
    open: true,
    // Allow loading DZI tiles from public archives (MAST, jsdelivr, etc.)
    cors: true,
  },
  preview: {
    port: 4173,
  },
  build: {
    target: "es2020",
    sourcemap: true,
    chunkSizeWarningLimit: 1024,
  },
});
