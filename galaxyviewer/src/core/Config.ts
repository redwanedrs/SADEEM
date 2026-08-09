/**
 * GalaxyViewer — Configuration.
 *
 * Defaults match the original GalaxyViewer:
 *   - LLM via Groq (free Llama 3.1 8B instant) at https://api.groq.com/openai/v1/chat/completions
 *   - Pre-defined points of interest for the Carina Nebula (Eta Carinae,
 *     Mystic Mountain, Cosmic Cliffs, etc.)
 *   - Tool-calling agent: the LLM can call `goToMarker(markerId)` to fly
 *     the viewport to any POI.
 */

import { ConfigurationError } from "./Errors";

// ---------------------------------------------------------------------------
// AI / LLM (Groq)
// ---------------------------------------------------------------------------

export interface AiConfig {
  /** Enable the AI chat panel + tool-calling agent. */
  enabled: boolean;
  /**
   * OpenAI-compatible chat completions endpoint. Defaults to Groq's free
   * endpoint. Groq hosts open models (Llama 3.1, Mixtral, etc.) at no cost —
   * get a free API key at https://console.groq.com/keys
   */
  endpoint: string;
  /** API key (sent as Bearer token). Leave empty for demo mode. */
  apiKey: string;
  /** Model identifier. Defaults to Groq's free Llama 3.1 8B instant. */
  model: string;
  /** System prompt prepended to every request. */
  systemPrompt: string;
  /** Max tokens in the response. */
  maxTokens: number;
  /** Temperature (0..2). */
  temperature: number;
  /** Enable tool calling (goToMarker). */
  enableTools: boolean;
}

// ---------------------------------------------------------------------------
// Points of Interest
// ---------------------------------------------------------------------------

export interface PoiSeed {
  id?: string;
  /** X position in normalized image coordinates (0..1). */
  x: number;
  /** Y position in normalized image coordinates (0..1). */
  y: number;
  name: string;
  title?: string;
  description?: string;
  category?: string;
}

export interface PoiConfig {
  /** Enable Points-of-Interest overlay + side panel. */
  enabled: boolean;
  /** URL of a JSON file containing POIs (loaded on mount). */
  sourceUrl?: string;
  /** Inline POIs (used when sourceUrl is not set). Defaults to Carina Nebula stars. */
  initial?: PoiSeed[];
  /** Show POI labels under the markers. */
  showLabels: boolean;
  /** Pixel size of POI markers. */
  markerSize: number;
  /** Fly-to zoom rect half-width (normalized). 0.05 → 10% of image. */
  flyToBounds: number;
}

/**
 * The default POIs — the well-known named objects in the Carina Nebula,
 * matching the original GalaxyViewer. These are the "points of interest"
 * that the Groq agent can navigate to via the `goToMarker(markerId)` tool.
 */
export const DEFAULT_CARINA_POIS: PoiSeed[] = [
  {
    id: "eta-carinae",
    name: "Eta Carinae",
    title: "Eta Carinae",
    x: 0.455, y: 0.52,
    description:
      "A colossal stellar system, containing at least two stars with a combined luminosity over five million times that of our sun. It is famous for its 'Great Eruption' in the mid-19th century.",
  },
  {
    id: "homunculus-nebula",
    name: "Homunculus Nebula",
    title: "Homunculus Nebula",
    x: 0.8, y: 0.15,
    description:
      "An emission and reflection nebula shrouding Eta Carinae, formed from material ejected during the Great Eruption. It is the brightest object in the sky at mid-infrared wavelengths.",
  },
  {
    id: "keyhole-nebula",
    name: "Keyhole Nebula",
    title: "Keyhole Nebula",
    x: 0.448, y: 0.44,
    description:
      "A small, dark cloud of cold molecules and dust, seen in silhouette against the brighter background of the Carina Nebula. Its appearance has changed over time due to intense radiation.",
  },
  {
    id: "trumpler-14",
    name: "Trumpler 14",
    title: "Trumpler 14",
    x: 0.53, y: 0.28,
    description:
      "One of the youngest and most populous open star clusters in the nebula, only about 300,000 to 500,000 years old. It contains a high concentration of massive and luminous stars.",
  },
  {
    id: "trumpler-16",
    name: "Trumpler 16",
    title: "Trumpler 16",
    x: 0.46, y: 0.55,
    description:
      "A large open cluster that is home to some of the most luminous stars in the Milky Way, including Eta Carinae and the Wolf-Rayet star WR 25.",
  },
  {
    id: "wr-22",
    name: "WR 22",
    title: "WR 22",
    x: 0.5, y: 0.4,
    description:
      "An eclipsing binary star system containing a rare Wolf-Rayet star, which is rapidly losing mass through powerful stellar winds. It is a bright source of X-rays.",
  },
  {
    id: "hd-93129a",
    name: "HD 93129A",
    title: "HD 93129A",
    x: 0.533, y: 0.295,
    description:
      "A triple star system composed of some of the most luminous and hottest stars in our galaxy. The primary component is one of the earliest and hottest spectral types known.",
  },
  {
    id: "mystic-mountain",
    name: "Mystic Mountain",
    title: "Mystic Mountain",
    x: 0.783, y: 0.51,
    description:
      "A three-light-year-tall pillar of gas and dust, famously imaged by the Hubble Space Telescope. It is a region of intense star-forming activity.",
  },
  {
    id: "cosmic-cliffs",
    name: "Cosmic Cliffs",
    title: "Cosmic Cliffs",
    x: 0.8, y: 0.2,
    description:
      "The edge of a gigantic, gaseous cavity within a young, star-forming region, revealed in stunning detail by the James Webb Space Telescope.",
  },
  {
    id: "bok-globules",
    name: "Bok Globules",
    title: "Bok Globules",
    x: 0.3, y: 0.2,
    description:
      "Small, dark, and dense clouds of dust and gas that are in the process of collapsing to form new stars. They are often referred to as 'cocoons' for protostars.",
  },
];

// ---------------------------------------------------------------------------
// VR (WebXR)
// ---------------------------------------------------------------------------

export interface VrConfig {
  /** Enable the VR entry button (still requires WebXR support at runtime). */
  enabled: boolean;
  /** URL of an external VR view (e.g. a YouTube 360 video). If set, the VR
   * button opens this URL in a new tab instead of launching an in-page
   * WebXR session. */
  externalUrl?: string;
}

// ---------------------------------------------------------------------------
// Top-level config
// ---------------------------------------------------------------------------

export interface ViewerConfig {
  /** Selector (or Element) of the container that will hold the viewer. */
  container: string | HTMLElement;
  /** URL of the .dzi manifest OR a tile source configuration object. */
  source: string | Record<string, unknown>;
  /** Initial zoom hint, where 1.0 means the image fits the viewport. */
  defaultZoomLevel?: number;
  /** Minimum zoom factor (0 = auto-fit). */
  minZoomImageRatio?: number;
  /** Maximum zoom factor (1 = 100% native pixel size). */
  maxZoomPixelRatio?: number;
  /** Enable the navigator (minimap) in the bottom-right corner. */
  showNavigator?: boolean;
  /** Navigator position. */
  navigatorPosition?: "BOTTOM_RIGHT" | "TOP_RIGHT" | "BOTTOM_LEFT" | "TOP_LEFT";
  /** Tile blend duration in seconds. */
  blendTime?: number;
  /** Constrain pan to image bounds. */
  constrainDuringPan?: boolean;
  /** Tile fade-in duration in milliseconds. */
  fadeInDuration?: number;
  /** Background color of the viewer canvas (CSS color string). */
  backgroundColor?: string;
  /** Theme — controls UI chrome colors. */
  theme?: "dark" | "light" | "auto";
  /** Cross-origin tile loading mode. */
  crossOriginPolicy?: "Anonymous" | "use-credentials" | false;
  /** Maximum number of concurrent tile requests. */
  imageLoaderLimit?: number;
  /** AI / LLM sub-config. */
  ai?: AiConfig;
  /** Points-of-Interest sub-config. */
  poi?: PoiConfig;
  /** VR sub-config. */
  vr?: VrConfig;
}

export const DEFAULT_CONFIG: Readonly<ViewerConfig> = {
  container: "#galaxyviewer-root",
  source: "",
  defaultZoomLevel: 0,
  minZoomImageRatio: 0.8,
  maxZoomPixelRatio: 1.5,
  showNavigator: true,
  navigatorPosition: "BOTTOM_RIGHT",
  blendTime: 0.3,
  constrainDuringPan: false,
  fadeInDuration: 220,
  backgroundColor: "#0a0a1a",
  theme: "dark",
  crossOriginPolicy: "Anonymous",
  imageLoaderLimit: 6,
  ai: {
    enabled: true,
    endpoint: "https://api.groq.com/openai/v1/chat/completions",
    apiKey: "",
    model: "llama-3.1-8b-instant",
    systemPrompt:
      "You are an assistant for a deep-space image viewer. You can navigate the viewport by calling the goToMarker tool. " +
      "Available markers are listed below. When the user asks to zoom to or show a named object, call goToMarker with the matching markerId. " +
      "After the tool returns, confirm the action to the user in one short sentence.",
    maxTokens: 400,
    temperature: 0.4,
    enableTools: true,
  },
  poi: {
    enabled: true,
    initial: DEFAULT_CARINA_POIS,
    showLabels: true,
    markerSize: 24,
    flyToBounds: 0.05,
  },
  vr: {
    enabled: true,
  },
};

export function mergeConfig(
  user: Partial<ViewerConfig>,
  defaults: ViewerConfig = DEFAULT_CONFIG,
): ViewerConfig {
  const merged: ViewerConfig = {
    ...defaults,
    ...user,
    ai: { ...defaults.ai!, ...(user.ai ?? {}) },
    poi: { ...defaults.poi!, ...(user.poi ?? {}) },
    vr: { ...defaults.vr!, ...(user.vr ?? {}) },
  };
  if (!merged.container) {
    throw new ConfigurationError("ViewerConfig.container is required.");
  }
  if (!merged.source) {
    throw new ConfigurationError("ViewerConfig.source is required (path to .dzi or tile source).");
  }
  return merged;
}
