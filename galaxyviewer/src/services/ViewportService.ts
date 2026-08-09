/**
 * ViewportService — viewport state mirror.
 *
 * OpenSeadragon owns the actual viewport, but other components (status bar,
 * minimap, keyboard service) need to *read* the current zoom/pan without
 * coupling to OpenSeadragon's API. This service mirrors the viewport state
 * into a plain object and republishes changes through the EventBus.
 */

import { EventBus, ViewerEvents } from "../core/Events";
import type { Logger } from "../core/Logger";

export interface ViewportState {
  zoom: number;            // 1.0 = image fits the viewport horizontally
  panX: number;            // -1..1 — center offset, normalized to image width
  panY: number;            // -1..1 — center offset, normalized to image height
  /** Native pixel scale: 1.0 = 1 image pixel per screen pixel. */
  scale: number;
  /** Total image bounds in viewport coordinates (0..1 in each axis). */
  bounds: { x: number; y: number; w: number; h: number };
}

export class ViewportService {
  private state: ViewportState = {
    zoom: 1, panX: 0.5, panY: 0.5, scale: 1,
    bounds: { x: 0, y: 0, w: 1, h: 1 },
  };

  constructor(
    private readonly bus: EventBus,
    private readonly log: Logger,
  ) {}

  get(): ViewportState {
    return { ...this.state, bounds: { ...this.state.bounds } };
  }

  update(partial: Partial<ViewportState>): void {
    const previous = this.state;
    this.state = { ...this.state, ...partial, bounds: { ...this.state.bounds, ...(partial.bounds ?? {}) } };
    this.bus.emit(ViewerEvents.ViewportChange, this.get());
    if (previous.zoom !== this.state.zoom) {
      this.bus.emit(ViewerEvents.ZoomChange, this.state.zoom);
    }
    if (previous.panX !== this.state.panX || previous.panY !== this.state.panY) {
      this.bus.emit(ViewerEvents.PanChange, { x: this.state.panX, y: this.state.panY });
    }
  }

  /** Convenience: zoom by a multiplicative factor around the viewport center. */
  zoomBy(_factor: number): void {
    // The actual zoom is applied by the Viewer component (it owns the OSD
    // instance). This method exists so keyboard / button handlers don't
    // need to import OpenSeadragon themselves.
    this.log.debug("ViewportService.zoomBy called (applied by Viewer).");
  }
}
