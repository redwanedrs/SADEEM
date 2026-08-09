# GalaxyViewer

A modern, modular Deep Zoom Image (DZI) viewer built with **Vite + TypeScript** and powered by **OpenSeadragon**. Designed to render multi-gigabyte astronomical imagery efficiently with progressive tile loading, smooth zoom/pan, **Groq AI navigation** (tool-calling agent), **clickable Points of Interest**, and **VR support**.

---

## Features

- **Deep Zoom rendering** — progressive tile loading via OpenSeadragon; smoothly handles multi-gigapixel images
- **Groq AI agent** — free Llama 3.1 8B inference via [Groq](https://console.groq.com/keys); natural-language navigation ("Zoom to Mystic Mountain")
- **Tool calling** — the agent has a `goToMarker(markerId)` tool that flies the viewport to any POI
- **Points of Interest** — pre-defined Carina Nebula objects (Eta Carinae, Mystic Mountain, Cosmic Cliffs, etc.) rendered as cyan glowing markers; click to fly-to + see description
- **VR support** — opens an external 360° VR URL (or WebXR session if available)
- **Minimap** — bottom-right navigator with POI dots
- **Keyboard shortcuts** — `+`/`-`/`0`/arrows/`F`/`H`/`Esc`
- **Cyan "space" theme** — matches the original GalaxyViewer aesthetic
- **Responsive** — chrome collapses on mobile

---

## Architecture

```
galaxyviewer/
├── index.html              ← HTML entry (root element + splash)
├── package.json            ← Vite + TypeScript + OpenSeadragon
├── tsconfig.json           ← Strict TypeScript config
├── vite.config.ts          ← Vite config (CORS-enabled dev server)
└── src/
    ├── main.ts             ← Bootstrap — wires layers together
    ├── core/
    │   ├── Config.ts       ← ViewerConfig + Groq + POI + VR defaults
    │   ├── Events.ts       ← Typed EventBus + canonical event names
    │   ├── Errors.ts       ← Typed error hierarchy
    │   └── Logger.ts       ← Timestamped leveled logger
    ├── services/
    │   ├── DziService.ts           ← DZI XML manifest parsing
    │   ├── TileLoaderService.ts    ← Tile-load progress tracking
    │   ├── ViewportService.ts      ← Viewport state mirror
    │   ├── KeyboardService.ts      ← Accessible keyboard shortcuts
    │   ├── PoiService.ts           ← POI CRUD + flyTo() (hooks to agent)
    │   ├── AiService.ts            ← Groq LLM + goToMarker tool-calling
    │   └── VrService.ts            ← WebXR / external VR URL
    ├── ui/
    │   ├── Viewer.ts               ← Owns the OpenSeadragon instance
    │   ├── Controls.ts             ← Zoom / home / fullscreen / VR / help
    │   ├── ProgressBar.ts          ← Animated tile-load progress bar
    │   ├── StatusBar.ts            ← Zoom %, dimensions, cursor coords
    │   ├── HelpOverlay.ts          ← Dismissible keyboard-shortcut overlay
    │   ├── PoiOverlay.ts           ← Cyan glowing markers + minimap dots
    │   ├── PoiModal.ts             ← POI info popup (title + description)
    │   ├── ChatPanel.ts            ← Groq chat UI (streaming responses)
    │   └── Theme.ts                ← Design tokens (cyan space theme)
    └── styles/
        └── main.css                ← All chrome styling (CSS variables)
```

### How the Groq agent hooks into the POIs

```
User types: "Zoom to Mystic Mountain"
        │
        ▼
ChatPanel ──► AiService.ask()
        │
        ▼
AiService ──► Groq API (POST /v1/chat/completions)
              • system prompt lists all POIs
              • tools: [{ goToMarker(markerId) }]
        │
        ▼
Groq returns: tool_call { name: "goToMarker", args: { markerId: "mystic-mountain" } }
        │
        ▼
AiService ──► PoiService.flyTo("mystic-mountain")
        │
        ▼
PoiService ──► EventBus.emit(PoiFlyTo)
        │
        ▼
Viewer subscribes ──► OpenSeadragon.viewport.fitBounds()
        │
        ▼
PoiService returns "Successfully zoomed to Mystic Mountain."
        │
        ▼
AiService sends tool result back to Groq ──► final confirmation
        │
        ▼
ChatPanel renders the assistant's confirmation
```

---

## Quickstart

### Develop

```bash
cd galaxyviewer
npm install
npm run dev          # http://localhost:5173
```

### Build for production

```bash
npm run build        # outputs to dist/
npm run preview      # preview the production build
```

### Use it to view an ElectPyNasa DZI pyramid

After running the ElectPyNasa pyramid pipeline, you'll have a directory like:

```
output/deepzoom-images/my_image/my_image.dzi
output/deepzoom-images/my_image/my_image_files/
```

Serve the directory and point GalaxyViewer at the `.dzi` file:

```bash
# From the galaxyviewer directory:
npm run dev
# Then open:
# http://localhost:5173/?src=http://localhost:8000/output/deepzoom-images/my_image/my_image.dzi
```

### Enable the Groq AI agent

Get a free API key at [console.groq.com/keys](https://console.groq.com/keys), then either:

- **URL parameter**: `?groq_key=<your-key>&src=<dzi-url>`
- **Code**: set `ViewerConfig.ai.apiKey` in your bootstrap code

Without a key, the AI runs in **demo mode** — it pattern-matches POI names and flies to them, so you can still test the navigation flow.

### Configure VR

- **External VR URL** (default behavior): `?vr=https://youtube.com/watch?v=...` (opens in a new tab)
- **WebXR**: if no `vr` param is set and the browser supports WebXR immersive-vr, the VR button launches a session

### Pre-defined POIs

By default, the viewer loads 10 named objects in the Carina Nebula:

| ID | Name | Coords (x, y) |
|----|------|---------------|
| `eta-carinae` | Eta Carinae | (0.455, 0.52) |
| `homunculus-nebula` | Homunculus Nebula | (0.8, 0.15) |
| `keyhole-nebula` | Keyhole Nebula | (0.448, 0.44) |
| `trumpler-14` | Trumpler 14 | (0.53, 0.28) |
| `trumpler-16` | Trumpler 16 | (0.46, 0.55) |
| `wr-22` | WR 22 | (0.5, 0.4) |
| `hd-93129a` | HD 93129A | (0.533, 0.295) |
| `mystic-mountain` | Mystic Mountain | (0.783, 0.51) |
| `cosmic-cliffs` | Cosmic Cliffs | (0.8, 0.2) |
| `bok-globules` | Bok Globules | (0.3, 0.2) |

Override them in `ViewerConfig.poi.initial` or load from a JSON URL via `ViewerConfig.poi.sourceUrl`.

---

## Keyboard shortcuts

| Key | Action |
|-----|--------|
| `+` / `=` | Zoom in |
| `−` / `_` | Zoom out |
| `0` | Reset to home (fit) view |
| `↑` `↓` `←` `→` or `WASD` | Pan |
| `F` | Toggle fullscreen |
| `H` | Toggle help overlay |
| `Esc` | Close dialogs |

---

## URL parameters

| Param | Description | Example |
|-------|-------------|---------|
| `src` | URL of the `.dzi` manifest | `?src=https://example.com/image.dzi` |
| `groq_key` | Groq API key (enables real LLM responses) | `?groq_key=gsk_...` |
| `vr` | External VR URL (opens in new tab) | `?vr=https://youtube.com/...` |

---

## Extending the viewer

| You want to… | Where to add code |
|--------------|-------------------|
| Add a new POI | `src/core/Config.ts` — append to `DEFAULT_CARINA_POIS` |
| Add a new AI tool | `src/services/AiService.ts` — extend `buildTools()` + `executeToolCall()` |
| Add a new UI component | `src/ui/` — subscribe to the EventBus in the constructor |
| Add a new keyboard shortcut | `src/services/KeyboardService.ts` — extend `DEFAULT_SHORTCUTS` |
| Replace the rendering engine | `src/ui/Viewer.ts` — swap OpenSeadragon; keep the EventBus API stable |
| Add a new theme | `src/ui/Theme.ts` — define a new `ThemeTokens` object and call `installTheme()` |

---

## License

MIT
