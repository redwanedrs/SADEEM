/**
 * TileLoaderService — tile-level metrics and progress reporting.
 *
 * Wraps OpenSeadragon's tile-load events into a clean observable API.
 * Other UI components (progress bar, status bar) subscribe to this service
 * instead of touching OpenSeadragon directly, which keeps the dependency
 * surface small and the code testable.
 *
 * Responsibilities
 * ----------------
 *   - Track in-flight tile requests
 *   - Emit aggregated progress events (bytes / count / percentage)
 *   - Detect "fully loaded for current viewport" state
 *   - Surface tile-load errors via the EventBus
 */

import { EventBus, ViewerEvents } from "../core/Events";
import type { Logger } from "../core/Logger";

export interface TileProgressSnapshot {
  pending: number;
  loaded: number;
  failed: number;
  total: number;
  /** 0..1 — fraction of currently-needed tiles that have loaded. */
  ratio: number;
}

export class TileLoaderService {
  private pending = 0;
  private loaded = 0;
  private failed = 0;
  private total = 0;
  private fullyLoaded = true;

  constructor(
    private readonly bus: EventBus,
    private readonly log: Logger,
  ) {}

  reset(): void {
    this.pending = 0;
    this.loaded = 0;
    this.failed = 0;
    this.total = 0;
    this.fullyLoaded = true;
    this.emit();
  }

  /** Called when OpenSeadragon requests a new tile. */
  onTileRequested(): void {
    this.pending += 1;
    this.total += 1;
    this.fullyLoaded = false;
    this.bus.emit(ViewerEvents.TileLoadStart, this.snapshot());
  }

  /** Called when a tile successfully loaded. */
  onTileLoaded(): void {
    this.pending = Math.max(0, this.pending - 1);
    this.loaded += 1;
    this.fullyLoaded = this.pending === 0;
    this.bus.emit(ViewerEvents.TileLoadComplete, this.snapshot());
  }

  /** Called when a tile failed to load. */
  onTileFailed(): void {
    this.pending = Math.max(0, this.pending - 1);
    this.failed += 1;
    this.fullyLoaded = this.pending === 0;
    this.log.warn("Tile load failed", this.snapshot());
    this.bus.emit(ViewerEvents.TileLoadError, this.snapshot());
  }

  /** True when every tile needed for the current viewport has loaded. */
  isFullyLoaded(): boolean {
    return this.fullyLoaded;
  }

  snapshot(): TileProgressSnapshot {
    const total = Math.max(this.total, 1);
    return {
      pending: this.pending,
      loaded: this.loaded,
      failed: this.failed,
      total: this.total,
      ratio: this.loaded / total,
    };
  }

  private emit(): void {
    const snap = this.snapshot();
    this.bus.emit(ViewerEvents.TileLoadComplete, snap);
  }
}
