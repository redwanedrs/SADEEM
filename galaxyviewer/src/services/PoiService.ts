/**
 * PoiService — Points of Interest management.
 *
 * Mirrors the original GalaxyViewer's `MarkerManager`:
 *   - Holds the canonical list of POIs (default = Carina Nebula stars)
 *   - Each POI has a normalized (x, y) coordinate, name, description
 *   - `flyTo(id)` is called by the Groq agent's `goToMarker` tool and by
 *     clicking a marker
 *   - Emits events so the overlay, modal, and chat panel can react
 *
 * The service never touches the OpenSeadragon instance directly — it emits
 * a `PoiFlyTo` event and the Viewer component subscribes to it. This keeps
 * the service testable and decouples it from the rendering engine.
 */

import { EventBus, ViewerEvents } from "../core/Events";
import type { PoiConfig, PoiSeed } from "../core/Config";
import { PoiError } from "../core/Errors";
import type { Logger } from "../core/Logger";

export interface Poi {
  id: string;
  /** X in normalized image coords (0..1). */
  x: number;
  /** Y in normalized image coords (0..1). */
  y: number;
  name: string;
  title: string;
  description: string;
  category: string;
}

let poiIdCounter = 0;
function nextPoiId(): string {
  poiIdCounter += 1;
  return `poi-${Date.now().toString(36)}-${poiIdCounter}`;
}

export class PoiService {
  private readonly pois = new Map<string, Poi>();
  private selectedId: string | null = null;

  constructor(
    private readonly bus: EventBus,
    private readonly log: Logger,
    private readonly config: PoiConfig,
  ) {}

  // ------------------------------------------------------------------
  // Loading
  // ------------------------------------------------------------------
  async loadInitial(): Promise<void> {
    if (!this.config.enabled) return;

    if (this.config.sourceUrl) {
      try {
        const res = await fetch(this.config.sourceUrl);
        if (!res.ok) {
          throw new PoiError(`Failed to fetch POI source (HTTP ${res.status})`,
            { url: this.config.sourceUrl, status: res.status });
        }
        const data = (await res.json()) as PoiSeed[] | { pois: PoiSeed[] };
        const seeds: PoiSeed[] = Array.isArray(data) ? data : data.pois ?? [];
        for (const s of seeds) this.add(s);
        this.log.info(`Loaded ${seeds.length} POIs from ${this.config.sourceUrl}`);
      } catch (err) {
        this.log.warn(`Could not load POI source: ${err}`);
      }
    } else if (this.config.initial) {
      for (const s of this.config.initial) this.add(s);
      this.log.info(`Loaded ${this.config.initial.length} pre-defined POIs.`);
    }
  }

  // ------------------------------------------------------------------
  // CRUD
  // ------------------------------------------------------------------
  add(seed: PoiSeed): Poi {
    if (typeof seed.x !== "number" || typeof seed.y !== "number") {
      throw new PoiError("PoiSeed.x and PoiSeed.y must be numbers.", { seed });
    }
    const poi: Poi = {
      id: seed.id ?? nextPoiId(),
      x: Math.max(0, Math.min(1, seed.x)),
      y: Math.max(0, Math.min(1, seed.y)),
      name: seed.name ?? "Unnamed object",
      title: seed.title ?? seed.name ?? "Unnamed object",
      description: seed.description ?? "",
      category: seed.category ?? "object",
    };
    this.pois.set(poi.id, poi);
    this.bus.emit<Poi>(ViewerEvents.PoiAdded, poi);
    return poi;
  }

  remove(id: string): boolean {
    const existed = this.pois.delete(id);
    if (existed) {
      if (this.selectedId === id) this.selectedId = null;
      this.bus.emit<string>(ViewerEvents.PoiRemoved, id);
    }
    return existed;
  }

  get(id: string): Poi | undefined {
    return this.pois.get(id);
  }

  list(): Poi[] {
    return Array.from(this.pois.values());
  }

  // ------------------------------------------------------------------
  // Selection + fly-to
  // ------------------------------------------------------------------
  select(id: string | null): void {
    this.selectedId = id;
    const poi = id ? this.pois.get(id) ?? null : null;
    this.bus.emit<Poi | null>(ViewerEvents.PoiSelected, poi);
  }

  getSelected(): Poi | null {
    return this.selectedId ? this.pois.get(this.selectedId) ?? null : null;
  }

  /**
   * Fly the viewport to a POI. Returns a human-readable status string that
   * the Groq agent can put back into the conversation (e.g.
   * "Successfully zoomed to Mystic Mountain.").
   *
   * This mirrors the original `MarkerManager.goToMarker(id)` return value.
   */
  flyTo(id: string): string {
    const poi = this.pois.get(id);
    if (!poi) {
      this.log.warn(`flyTo: unknown POI id "${id}"`);
      return `Error: Could not find a marker with the ID ${id}.`;
    }
    this.select(id);
    this.bus.emit<Poi>(ViewerEvents.PoiFocus, poi);
    this.bus.emit<Poi>(ViewerEvents.PoiFlyTo, poi);
    return `Successfully zoomed to ${poi.title}.`;
  }

  // ------------------------------------------------------------------
  // Serialization (for persistence in localStorage / Drive)
  // ------------------------------------------------------------------
  toJSON(): PoiSeed[] {
    return this.list().map((p) => ({
      id: p.id, x: p.x, y: p.y, name: p.name,
      title: p.title, description: p.description, category: p.category,
    }));
  }

  clear(): void {
    for (const id of Array.from(this.pois.keys())) this.remove(id);
  }
}
