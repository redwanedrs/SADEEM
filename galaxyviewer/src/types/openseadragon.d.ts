/**
 * Minimal ambient declaration for OpenSeadragon — the v4.x npm package ships
 * JavaScript only. We declare just enough of the API surface used by
 * GalaxyViewer; for the full type surface, install `@types/openseadragon`
 * (only available for v3.x).
 */

declare module "openseadragon" {
  export interface Point {
    x: number;
    y: number;
    new (x: number, y: number): Point;
  }

  export interface Rect {
    x: number;
    y: number;
    width: number;
    height: number;
  }

  export interface TileSource {
    height?: number;
    width?: number;
    tileSize?: number;
    tileOverlap?: number;
    tileFormat?: string;
    minLevel?: number;
    maxLevel?: number;
    getTileUrl?: (level: number, x: number, y: number) => string;
  }

  export interface ViewerOptions {
    element: string | HTMLElement;
    tileSources: string | TileSource | Record<string, unknown>;
    prefixUrl?: string;
    showNavigationControl?: boolean;
    showNavigator?: boolean;
    navigatorPosition?: string;
    navigatorSizeRatio?: number;
    defaultZoomLevel?: number;
    minZoomImageRatio?: number;
    maxZoomPixelRatio?: number;
    fadeInDuration?: number;
    smoothTileEdgesMinZoom?: number;
    imageLoaderLimit?: number;
    crossOriginPolicy?: string | false;
    gestureSettingsMouse?: Record<string, unknown>;
    gestureSettingsTouch?: Record<string, unknown>;
    visibilityRatio?: number;
    constrainDuringPan?: boolean;
    [key: string]: unknown;
  }

  export interface EventHandler {
    (event: { [key: string]: unknown }): void;
  }

  export interface TiledImage {
    addHandler(eventName: string, handler: EventHandler): void;
  }

  export interface World {
    getItemAt(index: number): TiledImage;
  }

  export interface Viewport {
    zoomBy(factor: number): void;
    panBy(point: Point): void;
    goHome(): void;
    getZoom(current?: boolean): number;
    getCenter(): Point;
    getBounds(): Rect;
  }

  export interface Viewer {
    viewport: Viewport;
    world: World;
    addHandler(eventName: string, handler: EventHandler): void;
    close(): void;
    destroy(): void;
    isFullPage(): boolean;
    setFullPage(full: boolean): void;
  }

  function OpenSeadragon(options: ViewerOptions): Viewer;
  export default OpenSeadragon;
  export { OpenSeadragon };
}
