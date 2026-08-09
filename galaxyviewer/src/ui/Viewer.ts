/**
 * GalaxyViewer — the central component that owns the OpenSeadragon instance.
 *
 * Responsibilities
 * ----------------
 *   - Construct OpenSeadragon with the resolved configuration
 *   - Wire OpenSeadragon events into the EventBus
 *   - Bridge keyboard / control / POI / AI events back to OSD actions
 *   - Expose a tiny imperative API (zoomIn, zoomOut, home, flyToPoi,
 *     toggleFullscreen) for external callers
 *
 * The Viewer is the *only* component that imports OpenSeadragon. Every
 * other UI piece talks to it through the EventBus or via the typed
 * imperative API.
 */

import OpenSeadragon from "openseadragon";
import type { Viewer as OsdViewer, TileSource as OsdTileSource, Point as OsdPoint } from "openseadragon";

import type { ViewerConfig } from "../core/Config";
import { mergeConfig } from "../core/Config";
import { EventBus, ViewerEvents } from "../core/Events";
import { Logger } from "../core/Logger";
import { TileLoaderService } from "../services/TileLoaderService";
import { ViewportService } from "../services/ViewportService";
import { DziService } from "../services/DziService";
import type { DziManifest } from "../services/DziService";
import { PoiService } from "../services/PoiService";
import { AiService } from "../services/AiService";
import { VrService } from "../services/VrService";
import type { Poi } from "../services/PoiService";

export class GalaxyViewer {
  public readonly bus = new EventBus();
  public readonly viewport: ViewportService;
  public readonly tiles: TileLoaderService;
  public readonly pois: PoiService;
  public readonly ai: AiService;
  public readonly vr: VrService;
  public readonly log: Logger;

  private readonly dzi: DziService;
  private osdViewer: OsdViewer | null = null;
  private readonly config: ViewerConfig;

  constructor(userConfig: Partial<ViewerConfig>) {
    this.config = mergeConfig(userConfig);
    this.log = new Logger(this.bus);
    this.viewport = new ViewportService(this.bus, this.log);
    this.tiles = new TileLoaderService(this.bus, this.log);
    this.dzi = new DziService(this.log);
    this.pois = new PoiService(this.bus, this.log, this.config.poi!);
    this.ai = new AiService(this.bus, this.log, this.config.ai!, this.pois);
    this.vr = new VrService(this.bus, this.log, this.config.vr!);
  }

  // ------------------------------------------------------------------
  // Lifecycle
  // ------------------------------------------------------------------
  async mount(): Promise<void> {
    const container = this.resolveContainer();
    this.log.info("GalaxyViewer mounting.", { container });

    const manifest = await this.dzi.load(this.config.source);
    this.log.info("Tile source resolved.", {
      width: manifest.width,
      height: manifest.height,
      tileSize: manifest.tileSize,
    });

    this.osdViewer = OpenSeadragon({
      element: container,
      tileSources: this.toOsdTileSource(manifest),
      prefixUrl: "https://cdn.jsdelivr.net/npm/openseadragon@4.1.1/build/openseadragon/images/",
      showNavigationControl: false,
      showNavigator: this.config.showNavigator,
      navigatorPosition: this.config.navigatorPosition ?? "BOTTOM_RIGHT",
      defaultZoomLevel: this.config.defaultZoomLevel,
      minZoomImageRatio: this.config.minZoomImageRatio,
      maxZoomPixelRatio: this.config.maxZoomPixelRatio,
      fadeInDuration: this.config.fadeInDuration,
      imageLoaderLimit: this.config.imageLoaderLimit,
      crossOriginPolicy: this.config.crossOriginPolicy === false ? false : this.config.crossOriginPolicy,
      blendTime: this.config.blendTime,
      constrainDuringPan: this.config.constrainDuringPan,
      gestureSettingsMouse: { clickToZoom: false, dblClickToZoom: true, flickEnabled: true },
      gestureSettingsTouch: { pinchToZoom: true, flickEnabled: true },
      visibilityRatio: 0.7,
    });

    this.bindEvents();

    // Load pre-defined POIs (Carina Nebula stars by default)
    await this.pois.loadInitial();

    this.bus.emit(ViewerEvents.Open, { tileSource: manifest });
    this.log.info("GalaxyViewer mounted.");
  }

  unmount(): void {
    if (this.osdViewer) {
      this.osdViewer.close();
      this.osdViewer.destroy();
      this.osdViewer = null;
    }
    this.bus.emit(ViewerEvents.Close);
    this.log.info("GalaxyViewer unmounted.");
  }

  // ------------------------------------------------------------------
  // Imperative API
  // ------------------------------------------------------------------
  zoomIn(): void {
    this.osdViewer?.viewport.zoomBy(1.4);
  }

  zoomOut(): void {
    this.osdViewer?.viewport.zoomBy(1 / 1.4);
  }

  home(): void {
    this.osdViewer?.viewport.goHome();
  }

  panBy(dx: number, dy: number): void {
    if (!this.osdViewer) return;
    const PointCtor = (OpenSeadragon as unknown as {
      Point: new (x: number, y: number) => OsdPoint;
    }).Point;
    this.osdViewer.viewport.panBy(new PointCtor(dx, dy));
  }

  toggleFullscreen(): void {
    if (this.osdViewer?.isFullPage()) {
      this.osdViewer.setFullPage(false);
    } else {
      this.osdViewer?.setFullPage(true);
    }
  }

  /**
   * Fly the viewport to a POI. Called when the Groq agent invokes the
   * `goToMarker` tool or when the user clicks a marker.
   */
  flyToPoi(poi: Poi): void {
    if (!this.osdViewer) return;
    const Rect = (OpenSeadragon as unknown as {
      Rect: new (x: number, y: number, w: number, h: number) => unknown;
    }).Rect;
    const half = this.config.poi!.flyToBounds;
    const bounds = new Rect(poi.x - half, poi.y - half, half * 2, half * 2);
    // `fitBounds` with immediate=false animates the flight
    (this.osdViewer.viewport as unknown as {
      fitBounds: (rect: unknown, immediate: boolean) => void;
    }).fitBounds(bounds, false);
    this.log.info(`Flying to POI: ${poi.title}`, { id: poi.id, x: poi.x, y: poi.y });
  }

  /** Returns the underlying OSD viewer (used by the PoiOverlay for addOverlay). */
  getOsdViewer(): OsdViewer | null {
    return this.osdViewer;
  }

  // ------------------------------------------------------------------
  // Internals
  // ------------------------------------------------------------------
  private resolveContainer(): HTMLElement {
    const c = this.config.container;
    if (typeof c === "string") {
      const el = document.querySelector<HTMLElement>(c);
      if (!el) throw new Error(`GalaxyViewer: container "${c}" not found.`);
      return el;
    }
    return c;
  }

  private toOsdTileSource(manifest: DziManifest): OsdTileSource {
    const m = manifest;
    return {
      height: m.height,
      width: m.width,
      tileSize: m.tileSize,
      tileOverlap: m.overlap,
      tileFormat: m.format,
      getTileUrl: (level: number, x: number, y: number) =>
        `${m.baseUrl}${level}/${x}_${y}.${m.format}`,
      minLevel: 8,
      maxLevel: Math.ceil(Math.log2(Math.max(m.width, m.height))),
    } as unknown as OsdTileSource;
  }

  private bindEvents(): void {
    if (!this.osdViewer) return;
    const v = this.osdViewer;

    v.addHandler("open", () => {
      this.bus.emit(ViewerEvents.Open);
    });

    v.addHandler("zoom", (e: { zoom?: number } | Record<string, unknown>) => {
      const zoom = (e as { zoom?: number }).zoom ?? 1;
      this.viewport.update({ zoom, scale: zoom });
    });

    v.addHandler("pan", (e: { center?: { x: number; y: number } } | Record<string, unknown>) => {
      const center = (e as { center?: { x: number; y: number } }).center;
      if (center) this.viewport.update({ panX: center.x, panY: center.y });
    });

    v.addHandler("animation", () => {
      if (!v) return;
      const vp = v.viewport;
      const bounds = vp.getBounds();
      this.viewport.update({
        zoom: vp.getZoom(),
        scale: vp.getZoom(true),
        panX: vp.getCenter().x,
        panY: vp.getCenter().y,
        bounds: { x: bounds.x, y: bounds.y, w: bounds.width, h: bounds.height },
      });
    });

    v.addHandler("tile-load-failed", () => {
      this.tiles.onTileFailed();
    });

    // Bridge keyboard events from the EventBus
    this.bus.on<{ dx: number; dy: number }>(ViewerEvents.KeyboardPan, (p) => this.panBy(p.dx, p.dy));
    this.bus.on(ViewerEvents.KeyboardZoomIn, () => this.zoomIn());
    this.bus.on(ViewerEvents.KeyboardZoomOut, () => this.zoomOut());
    this.bus.on(ViewerEvents.KeyboardHome, () => this.home());
    this.bus.on(ViewerEvents.KeyboardFullscreen, () => this.toggleFullscreen());

    // Bridge POI fly-to events (from the Groq agent / click handler)
    this.bus.on<Poi>(ViewerEvents.PoiFlyTo, (poi) => this.flyToPoi(poi));

    // Resize handling
    window.addEventListener("resize", () => {
      this.bus.emit(ViewerEvents.Resize, { width: window.innerWidth, height: window.innerHeight });
    });
  }
}
