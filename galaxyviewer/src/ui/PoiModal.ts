/**
 * PoiModal — info popup shown when a POI marker is clicked.
 *
 * Mirrors the original GalaxyViewer's `#marker-modal` element: a centered
 * card with the POI title and description, dismissible by clicking the
 * close button or pressing Escape.
 */

import { EventBus, ViewerEvents } from "../core/Events";
import type { Poi } from "../services/PoiService";

export class PoiModal {
  private readonly el: HTMLElement;
  private readonly titleEl: HTMLElement;
  private readonly descEl: HTMLElement;

  constructor(bus: EventBus, target: HTMLElement) {
    [this.el, this.titleEl, this.descEl] = this.render();
    target.appendChild(this.el);

    // Show modal when a POI is focused (via click or agent tool call)
    bus.on<Poi>(ViewerEvents.PoiFocus, (poi) => this.show(poi));

    // Close handlers
    this.el.querySelector(".gv-modal-close")?.addEventListener("click", () => this.hide());
    this.el.addEventListener("click", (e) => {
      if (e.target === this.el) this.hide();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") this.hide();
    });
  }

  show(poi: Poi): void {
    this.titleEl.textContent = poi.title;
    this.descEl.textContent = poi.description;
    this.el.classList.add("gv-modal-visible");
  }

  hide(): void {
    this.el.classList.remove("gv-modal-visible");
  }

  private render(): [HTMLElement, HTMLElement, HTMLElement] {
    const overlay = document.createElement("div");
    overlay.className = "gv-modal";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-hidden", "true");

    const card = document.createElement("div");
    card.className = "gv-modal-card";

    const close = document.createElement("button");
    close.type = "button";
    close.className = "gv-modal-close";
    close.setAttribute("aria-label", "Close");
    close.innerHTML = "&times;";

    const title = document.createElement("h2");
    title.className = "gv-modal-title";

    const desc = document.createElement("p");
    desc.className = "gv-modal-desc";

    card.appendChild(close);
    card.appendChild(title);
    card.appendChild(desc);
    overlay.appendChild(card);
    return [overlay, title, desc];
  }
}
