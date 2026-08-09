/**
 * VrService — VR entry point.
 *
 * The original GalaxyViewer linked to an external 360° VR view (a YouTube
 * video). This service keeps that pattern: if `externalUrl` is set, the VR
 * button opens it in a new tab. If WebXR is available and no external URL
 * is configured, it falls back to an immersive-vr session (feature-detected).
 *
 * The service is intentionally minimal — it never blocks the rest of the
 * viewer. If VR is unavailable, the VR button is simply hidden.
 */

import { EventBus, ViewerEvents } from "../core/Events";
import type { VrConfig } from "../core/Config";
import { VrError } from "../core/Errors";
import type { Logger } from "../core/Logger";

// Minimal WebXR type stubs (the DOM lib doesn't include XR by default).
interface XRSession {
  end(): Promise<void>;
}
interface XRSystem {
  isSessionSupported(mode: string): Promise<boolean>;
  requestSession(mode: string, opts?: Record<string, unknown>): Promise<XRSession>;
}

export class VrService {
  private supported = false;

  constructor(
    private readonly bus: EventBus,
    private readonly log: Logger,
    private readonly config: VrConfig,
  ) {
    this.detectSupport();
  }

  private async detectSupport(): Promise<void> {
    if (typeof navigator === "undefined" || !("xr" in navigator)) {
      this.supported = false;
      return;
    }
    try {
      const xr = (navigator as Navigator & { xr: XRSystem }).xr;
      this.supported = await xr.isSessionSupported("immersive-vr");
    } catch {
      this.supported = false;
    }
  }

  isAvailable(): boolean {
    return this.config.enabled && (Boolean(this.config.externalUrl) || this.supported);
  }

  async enter(): Promise<void> {
    if (!this.config.enabled) {
      throw new VrError("VR is disabled in config.");
    }

    if (this.config.externalUrl) {
      window.open(this.config.externalUrl, "_blank", "noopener,noreferrer");
      this.bus.emit(ViewerEvents.VrSessionStart);
      this.log.info(`Opened external VR URL: ${this.config.externalUrl}`);
      return;
    }

    if (!this.supported) {
      const msg = "WebXR immersive-vr is not supported on this device.";
      this.bus.emit<string>(ViewerEvents.VrError, msg);
      throw new VrError(msg);
    }

    try {
      const xr = (navigator as Navigator & { xr: XRSystem }).xr;
      const session = await xr.requestSession("immersive-vr");
      this.bus.emit(ViewerEvents.VrSessionStart);
      this.log.info("WebXR VR session started.");
      await session.end();
      this.bus.emit(ViewerEvents.VrSessionEnd);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      this.bus.emit<string>(ViewerEvents.VrError, msg);
      throw new VrError(msg);
    }
  }
}
