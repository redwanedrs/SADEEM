/**
 * DziService — Deep Zoom Image (DZI) manifest parsing.
 *
 * A .dzi file is a tiny XML document that describes the pyramid:
 *
 *   <Image TileSize="256" Overlap="1" Format="jpeg"
 *          xmlns="http://schemas.microsoft.com/deepzoom/2008">
 *     <Size Width="32768" Height="16384"/>
 *   </Image>
 *
 * This service parses that XML into a typed `DziManifest` object that the
 * rest of the viewer consumes. It also handles the alternative "collection"
 * format and tile-source JSON objects (OpenSeadragon's native config).
 */

import { DziParseError } from "../core/Errors";
import type { Logger } from "../core/Logger";

export interface DziManifest {
  width: number;
  height: number;
  tileSize: number;
  overlap: number;
  format: string;
  /** Base URL for tile requests (without the level/col/row suffix). */
  baseUrl: string;
}

export class DziService {
  constructor(private readonly log: Logger) {}

  async load(source: string | Record<string, unknown>): Promise<DziManifest> {
    if (typeof source === "object" && source !== null) {
      return this.fromTileSourceObject(source as Record<string, unknown>);
    }
    if (typeof source !== "string") {
      throw new DziParseError("DziService.load: source must be a URL string or tile-source object.");
    }
    return source.toLowerCase().endsWith(".dzi")
      ? this.fromUrl(source)
      : this.fromShallowUrl(source);
  }

  // ------------------------------------------------------------------
  // XML manifest parsing
  // ------------------------------------------------------------------
  private async fromUrl(url: string): Promise<DziManifest> {
    this.log.info(`Fetching DZI manifest: ${url}`);
    const response = await fetch(url, { credentials: "omit" });
    if (!response.ok) {
      throw new DziParseError(
        `Failed to fetch DZI manifest (HTTP ${response.status})`,
        { url, status: response.status },
      );
    }
    const xmlText = await response.text();
    return this.parseXml(xmlText, url);
  }

  /**
   * Some servers expose a "shallow" URL that points to a directory
   * containing `image.dzi`. We try a small discovery sequence.
   */
  private async fromShallowUrl(url: string): Promise<DziManifest> {
    const candidates = [
      url.replace(/\/$/, "") + ".dzi",
      url.replace(/\/$/, "") + "/image.dzi",
      url,
    ];
    let lastError: unknown = null;
    for (const candidate of candidates) {
      try {
        return await this.fromUrl(candidate);
      } catch (err) {
        lastError = err;
      }
    }
    throw new DziParseError(
      `Could not locate a DZI manifest at or near: ${url}`,
      { url, lastError: String(lastError) },
    );
  }

  public parseXml(xmlText: string, baseUrl: string): DziManifest {
    const dom = new DOMParser().parseFromString(xmlText, "application/xml");
    if (dom.querySelector("parsererror")) {
      throw new DziParseError("DZI manifest is not well-formed XML.", { baseUrl });
    }
    const imageEl = dom.querySelector("Image") || dom.documentElement;
    if (!imageEl || imageEl.tagName !== "Image") {
      throw new DziParseError(
        "DZI manifest root must be an <Image> element.",
        { baseUrl, rootTag: imageEl?.tagName },
      );
    }
    const sizeEl = imageEl.querySelector("Size");
    if (!sizeEl) {
      throw new DziParseError("DZI manifest is missing the <Size> element.", { baseUrl });
    }

    const tileSize = Number(imageEl.getAttribute("TileSize"));
    const overlap = Number(imageEl.getAttribute("Overlap"));
    const format = imageEl.getAttribute("Format") || "jpeg";
    const width = Number(sizeEl.getAttribute("Width"));
    const height = Number(sizeEl.getAttribute("Height"));

    if (![tileSize, overlap, width, height].every((n) => Number.isFinite(n) && n > 0)) {
      throw new DziParseError(
        "DZI manifest has invalid numeric attributes.",
        { baseUrl, tileSize, overlap, width, height, format },
      );
    }

    // Tile base URL = the .dzi URL with the .dzi suffix stripped.
    const baseUrlClean = baseUrl.replace(/\.dzi$/i, "").replace(/\/[^/]+\.dzi$/i, "");
    // If the .dzi file lives at "/foo/image.dzi" the tiles are at "/foo/image_files/".
    const baseName = baseUrl.split("/").pop()?.replace(/\.dzi$/i, "") || "image";
    const tilesBaseUrl = `${baseUrlClean.replace(/\/$/, "")}/${baseName}_files/`;

    const manifest: DziManifest = {
      width, height, tileSize, overlap, format, baseUrl: tilesBaseUrl,
    };
    this.log.info("DZI manifest parsed.", manifest);
    return manifest;
  }

  // ------------------------------------------------------------------
  // JSON tile-source objects (OpenSeadragon-style)
  // ------------------------------------------------------------------
  private fromTileSourceObject(obj: Record<string, unknown>): DziManifest {
    const width = Number(obj.width);
    const height = Number(obj.height);
    const tileSize = Number(obj.tileSize ?? obj.tileWidth ?? 256);
    const overlap = Number(obj.tileOverlap ?? 0);
    const format = String(obj.format ?? "jpeg");
    const baseUrl = String(obj.baseUrl ?? obj.tilesUrl ?? "");
    if (![width, height, tileSize].every((n) => Number.isFinite(n) && n > 0)) {
      throw new DziParseError("Tile-source object is missing required fields.", { obj });
    }
    return { width, height, tileSize, overlap, format, baseUrl };
  }
}

// ---------------------------------------------------------------------------
// Helper: coerce an unknown value into a Record<string, unknown> safely.
// Used by callers that need to pass a DziManifest into APIs expecting a
// generic record (e.g. EventBus emit payloads).
// ---------------------------------------------------------------------------
export function manifestToRecord(m: DziManifest): Record<string, unknown> {
  return { ...m };
}
