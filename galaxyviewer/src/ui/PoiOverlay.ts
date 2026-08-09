/**
 * PoiOverlay — renders POI markers on top of the OpenSeadragon canvas.
 *
 * Mirrors the original GalaxyViewer's `MarkerManager.initializeMarkers()`:
 *   - For each POI, add a cyan glowing circle as an OSD overlay
 *   - Add a smaller dot on the minimap (navigator)
 *   - Click a marker → fly-to + emit PoiSelected (the modal subscribes)
 *
 * The overlay re-renders whenever POIs are added or removed.
 */

import { EventBus, ViewerEvents } from "../core/Events";
import type { Logger } from "../core/Logger";
import type { PoiService, Poi } from "../services/PoiService";
import type { GalaxyViewer } from "./Viewer";

export class PoiOverlay {
  private readonly markerElements = new Map<string, HTMLElement>();
  private readonly navMarkerElements = new Map<string, HTMLElement>();
  private readonly container: HTMLElement;

  constructor(
    private readonly viewer: GalaxyViewer,
    private readonly bus: EventBus,
    private readonly log: Logger,
    private readonly pois: PoiService,
    container: HTMLElement,
  ) {
    this.container = container;

    bus.on<Poi>(ViewerEvents.PoiAdded, () => this.refresh());
    bus.on<string>(ViewerEvents.PoiRemoved, () => this.refresh());
    // Refresh after the image opens (OSD needs the viewport ready)
    bus.on(ViewerEvents.Open, () => setTimeout(() => this.refresh(), 100));

    // Click on a marker → fly-to + select
    bus.on<Poi>(ViewerEvents.PoiSelected, (poi) => {
      if (!poi) return;
    });
  }

  refresh(): void {
    const osd = this.viewer.getOsdViewer();
    if (!osd) return;

    // Remove existing overlays
    for (const el of this.markerElements.values()) {
      (osd as unknown as { removeOverlay: (e: HTMLElement) => void }).removeOverlay(el);
      el.remove();
    }
    this.markerElements.clear();

    for (const el of this.navMarkerElements.values()) el.remove();
    this.navMarkerElements.clear();

    // Add fresh overlays for every POI
    for (const poi of this.pois.list()) {
      this.addMarker(poi);
    }
    this.log.info(`PoiOverlay rendered ${this.pois.list().length} markers.`);
  }

  private addMarker(poi: Poi): void {
    const osd = this.viewer.getOsdViewer();
    if (!osd) return;

    const Point = (window as unknown as { OpenSeadragon: { Point: new (x: number, y: number) => unknown } }).OpenSeadragon.Point
      ?? (null as unknown as null);

    // Main viewer marker — cyan glowing circle
    const markerEl = document.createElement("div");
    markerEl.className = "gv-marker";
    markerEl.title = poi.title;
    markerEl.setAttribute("role", "button");
    markerEl.setAttribute("aria-label", `Fly to ${poi.title}`);
    markerEl.addEventListener("click", (e) => {
      e.stopPropagation();
      this.pois.flyTo(poi.id);
    });
    this.container.appendChild(markerEl);

    try {
      (osd as unknown as {
        addOverlay: (opts: { element: HTMLElement; location: unknown; placement: string }) => void;
      }).addOverlay({
        element: markerEl,
        location: new (window as unknown as { OpenSeadragon: { Point: new (x: number, y: number) => unknown } }).OpenSeadragon.Point(poi.x, poi.y),
        placement: "CENTER",
      });
      this.markerElements.set(poi.id, markerEl);
    } catch (err) {
      this.log.warn(`Failed to add overlay for ${poi.id}: ${err}`);
      markerEl.remove();
    }

    // Navigator marker (smaller dot on the minimap)
    const navViewer = (osd as unknown as { navigator?: { viewer?: unknown } }).navigator?.viewer as
      | (unknown & { addOverlay?: (opts: unknown) => void })
      | undefined;
    if (navViewer && typeof (navViewer as { addOverlay?: unknown }).addOverlay === "function") {
      const navEl = document.createElement("div");
      navEl.className = "gv-marker-nav";
      this.container.appendChild(navEl);
      try {
        (navViewer as { addOverlay: (opts: unknown) => void }).addOverlay({
          element: navEl,
          location: new (window as unknown as { OpenSeadragon: { Point: new (x: number, y: number) => unknown } }).OpenSeadragon.Point(poi.x, poi.y),
          placement: "CENTER",
        });
        this.navMarkerElements.set(poi.id, navEl);
      } catch {
        navEl.remove();
      }
    }
  }
}
