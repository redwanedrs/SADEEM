/**
 * StatusBar — bottom overlay showing zoom level, image dimensions, and
 * current pointer coordinates (in image pixels).
 *
 * Subscribes to viewport events and updates its labels without re-rendering
 * the entire DOM. The bar is collapsible on small viewports.
 */

import { EventBus, ViewerEvents } from "../core/Events";
import type { DziManifest } from "../services/DziService";

export class StatusBar {
  private readonly el: HTMLElement;
  private readonly zoomLabel: HTMLElement;
  private readonly dimLabel: HTMLElement;
  private readonly coordLabel: HTMLElement;
  private readonly pixelLabel: HTMLElement;
  private imageWidth = 0;
  private imageHeight = 0;

  constructor(bus: EventBus, target: HTMLElement) {
    [this.el, this.zoomLabel, this.dimLabel, this.coordLabel, this.pixelLabel] = this.render();
    target.appendChild(this.el);

    bus.on<number>(ViewerEvents.ZoomChange, (zoom) => {
      this.zoomLabel.textContent = `${(zoom * 100).toFixed(0)}%`;
      this.pixelLabel.textContent = `${zoom.toFixed(2)}px`;
    });

    bus.on<{ width: number; height: number }>("viewer:metadata", (m) => {
      this.imageWidth = m.width;
      this.imageHeight = m.height;
      this.dimLabel.textContent = `${m.width.toLocaleString()} × ${m.height.toLocaleString()}`;
    });

    // Update pointer coordinates
    target.addEventListener("mousemove", (e: MouseEvent) => {
      if (!this.imageWidth) return;
      const rect = target.getBoundingClientRect();
      const nx = (e.clientX - rect.left) / rect.width;
      const ny = (e.clientY - rect.top) / rect.height;
      const px = Math.round(nx * this.imageWidth);
      const py = Math.round(ny * this.imageHeight);
      this.coordLabel.textContent = `${px.toLocaleString()}, ${py.toLocaleString()}`;
    });
  }

  setMetadata(m: DziManifest): void {
    this.imageWidth = m.width;
    this.imageHeight = m.height;
    this.dimLabel.textContent = `${m.width.toLocaleString()} × ${m.height.toLocaleString()}`;
  }

  private render(): [HTMLElement, HTMLElement, HTMLElement, HTMLElement, HTMLElement] {
    const bar = document.createElement("div");
    bar.className = "gv-statusbar";

    const left = document.createElement("div");
    left.className = "gv-status-group";
    const dim = this.kv("Dimensions", "—");
    left.appendChild(dim[0]);

    const center = document.createElement("div");
    center.className = "gv-status-group";
    const zoom = this.kv("Zoom", "100%");
    const px = this.kv("Scale", "1.00px");
    center.appendChild(zoom[0]);
    center.appendChild(px[0]);

    const right = document.createElement("div");
    right.className = "gv-status-group";
    const coord = this.kv("Cursor", "—");
    right.appendChild(coord[0]);

    bar.appendChild(left);
    bar.appendChild(center);
    bar.appendChild(right);

    return [bar, zoom[1], dim[1], coord[1], px[1]];
  }

  private kv(label: string, value: string): [HTMLElement, HTMLElement] {
    const wrap = document.createElement("div");
    wrap.className = "gv-status-kv";
    const lab = document.createElement("span");
    lab.className = "gv-status-label";
    lab.textContent = label;
    const val = document.createElement("span");
    val.className = "gv-status-value";
    val.textContent = value;
    wrap.appendChild(lab);
    wrap.appendChild(val);
    return [wrap, val];
  }

  destroy(): void {
    this.el.remove();
  }
}
