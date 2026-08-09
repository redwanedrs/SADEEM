/**
 * GalaxyViewer — Error hierarchy.
 *
 * Every error in the viewer inherits from `GalaxyViewerError` so callers can
 * catch the entire family with a single `except`-style clause. Each error
 * carries an optional context payload for diagnostic logging.
 */

export class GalaxyViewerError extends Error {
  public readonly category: string;
  public readonly context: Readonly<Record<string, unknown>>;

  constructor(
    message: string,
    category = "GALAXYVIEWER_ERROR",
    context: Record<string, unknown> = {},
  ) {
    super(message);
    this.name = new.target.name;
    this.category = category;
    this.context = Object.freeze({ ...context });
  }
}

export class ConfigurationError extends GalaxyViewerError {
  constructor(message: string, context: Record<string, unknown> = {}) {
    super(message, "CONFIGURATION_ERROR", context);
  }
}

export class DziParseError extends GalaxyViewerError {
  constructor(message: string, context: Record<string, unknown> = {}) {
    super(message, "DZI_PARSE_ERROR", context);
  }
}

export class TileLoadError extends GalaxyViewerError {
  constructor(message: string, context: Record<string, unknown> = {}) {
    super(message, "TILE_LOAD_ERROR", context);
  }
}

export class ViewportError extends GalaxyViewerError {
  constructor(message: string, context: Record<string, unknown> = {}) {
    super(message, "VIEWPORT_ERROR", context);
  }
}

export class PoiError extends GalaxyViewerError {
  constructor(message: string, context: Record<string, unknown> = {}) {
    super(message, "POI_ERROR", context);
  }
}

export class AiError extends GalaxyViewerError {
  constructor(message: string, context: Record<string, unknown> = {}) {
    super(message, "AI_ERROR", context);
  }
}

export class VrError extends GalaxyViewerError {
  constructor(message: string, context: Record<string, unknown> = {}) {
    super(message, "VR_ERROR", context);
  }
}
