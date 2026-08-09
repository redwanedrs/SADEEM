/**
 * GalaxyViewer — application entry point.
 *
 * Wires together every layer:
 *   - core:     Config, EventBus, Logger
 *   - services: DziService, TileLoaderService, ViewportService,
 *               KeyboardService, PoiService, AiService, VrService
 *   - ui:       Viewer, Controls, ProgressBar, StatusBar, HelpOverlay,
 *               PoiOverlay, PoiModal, ChatPanel, Theme
 *
 * URL parameters:
 *   ?src=<url>         DZI manifest URL
 *   ?groq_key=<key>    Groq API key (overrides config)
 *   ?vr=<url>          External VR URL (e.g. a YouTube 360 video)
 */

import { GalaxyViewer } from "./ui/Viewer";
import { Controls } from "./ui/Controls";
import { ProgressBar } from "./ui/ProgressBar";
import { StatusBar } from "./ui/StatusBar";
import { HelpOverlay } from "./ui/HelpOverlay";
import { PoiOverlay } from "./ui/PoiOverlay";
import { PoiModal } from "./ui/PoiModal";
import { ChatPanel } from "./ui/ChatPanel";
import { installTheme, DARK_THEME } from "./ui/Theme";
import { KeyboardService } from "./services/KeyboardService";
import { ViewerEvents } from "./core/Events";
import { DEFAULT_CONFIG, type ViewerConfig } from "./core/Config";

// ---------------------------------------------------------------------------
// Theme
// ---------------------------------------------------------------------------
installTheme(DARK_THEME);

// ---------------------------------------------------------------------------
// Resolve URL parameters
// ---------------------------------------------------------------------------
function resolveSource(): string {
  const params = new URLSearchParams(window.location.search);
  const src = params.get("src");
  if (src) return src;
  // Default: OpenSeadragon's public demo DZI
  return "https://openseadragon.github.io/example-images/duomo/duomo.dzi";
}

function resolveGroqKey(): string {
  const params = new URLSearchParams(window.location.search);
  return params.get("groq_key") ?? "";
}

function resolveVrUrl(): string | undefined {
  const params = new URLSearchParams(window.location.search);
  const vr = params.get("vr");
  return vr ?? undefined;
}

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------
async function bootstrap(): Promise<void> {
  const root = document.querySelector<HTMLElement>("#galaxyviewer-root");
  if (!root) {
    console.error("[GalaxyViewer] Root element #galaxyviewer-root not found.");
    return;
  }

  const config: Partial<ViewerConfig> = {
    container: root,
    source: resolveSource(),
    showNavigator: true,
    ai: {
      ...DEFAULT_CONFIG.ai!,
      apiKey: resolveGroqKey(),
    },
    vr: {
      ...DEFAULT_CONFIG.vr!,
      externalUrl: resolveVrUrl(),
    },
  };

  const viewer = new GalaxyViewer(config);
  await viewer.mount();

  // Attach UI components
  new Controls(viewer.bus, viewer.vr, root);
  new ProgressBar(viewer.bus, root);
  new StatusBar(viewer.bus, root);
  const help = new HelpOverlay(root);
  new PoiOverlay(viewer, viewer.bus, viewer.log, viewer.pois, root);
  new PoiModal(viewer.bus, root);
  new ChatPanel(viewer.bus, viewer.ai, root);

  // Keyboard service
  const keyboard = new KeyboardService(viewer.bus, viewer.log);
  keyboard.attach(root);
  viewer.bus.on(ViewerEvents.KeyboardHelp, () => help.toggle());

  // Hide the splash screen once the viewer is open
  viewer.bus.on(ViewerEvents.Open, () => {
    const splash = document.querySelector("#gv-splash");
    if (splash) {
      (splash as HTMLElement).style.opacity = "0";
      setTimeout(() => splash.remove(), 400);
    }
  });

  // Surface the viewer on window for debugging
  (window as unknown as { galaxyviewer: GalaxyViewer }).galaxyviewer = viewer;
  console.info("[GalaxyViewer] Ready. Use window.galaxyviewer for imperative access.");
  if (!viewer.ai.isConfigured()) {
    console.info("[GalaxyViewer] AI in demo mode. Add ?groq_key=<your-key> to the URL or set ViewerConfig.ai.apiKey.");
  }
}

bootstrap().catch((err) => {
  console.error("[GalaxyViewer] Bootstrap failed:", err);
});
