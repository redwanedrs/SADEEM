/**
 * ProgressBar — tile-load progress indicator.
 *
 * Subscribes to tile-load events and renders a thin, animated progress bar
 * at the top of the viewport. When every needed tile is loaded, the bar
 * fades out. Errors are visualised as a brief red flash.
 */

import { EventBus, ViewerEvents } from "../core/Events";
import type { TileProgressSnapshot } from "../services/TileLoaderService";

export class ProgressBar {
  private readonly el: HTMLElement;
  private readonly fill: HTMLElement;
  private flashTimer: number | null = null;

  constructor(bus: EventBus, target: HTMLElement) {
    [this.el, this.fill] = this.render();
    target.appendChild(this.el);
    bus.on<TileProgressSnapshot>(ViewerEvents.TileLoadStart, () => this.show());
    bus.on<TileProgressSnapshot>(ViewerEvents.TileLoadComplete, (s) => this.update(s));
    bus.on<TileProgressSnapshot>(ViewerEvents.TileLoadError, (s) => this.flashError(s));
  }

  private render(): [HTMLElement, HTMLElement] {
    const bar = document.createElement("div");
    bar.className = "gv-progress";
    bar.setAttribute("role", "progressbar");
    bar.setAttribute("aria-valuemin", "0");
    bar.setAttribute("aria-valuemax", "100");
    bar.setAttribute("aria-valuenow", "0");
    bar.style.opacity = "0";

    const fill = document.createElement("div");
    fill.className = "gv-progress-fill";
    bar.appendChild(fill);
    return [bar, fill];
  }

  private show(): void {
    this.el.style.opacity = "1";
  }

  private update(s: TileProgressSnapshot): void {
    const pct = Math.round(s.ratio * 100);
    this.fill.style.width = `${pct}%`;
    this.el.setAttribute("aria-valuenow", String(pct));
    if (s.pending === 0 && s.failed === 0) {
      this.fill.classList.remove("gv-progress-error");
      // Fade out after a brief pause.
      window.setTimeout(() => {
        if (s.pending === 0) this.el.style.opacity = "0";
      }, 400);
    }
  }

  private flashError(_s: TileProgressSnapshot): void {
    this.fill.classList.add("gv-progress-error");
    if (this.flashTimer) window.clearTimeout(this.flashTimer);
    this.flashTimer = window.setTimeout(() => {
      this.fill.classList.remove("gv-progress-error");
    }, 1500);
  }

  destroy(): void {
    this.el.remove();
  }
}
