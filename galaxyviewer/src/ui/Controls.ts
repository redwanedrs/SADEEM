/**
 * Controls — the on-screen toolbar.
 *
 * Buttons emit high-level intents on the EventBus; the Viewer component
 * subscribes and performs the actual action. This keeps the controls pure
 * and reusable.
 *
 * The VR button is only rendered if `VrService.isAvailable()` returns true.
 */

import { EventBus, ViewerEvents } from "../core/Events";
import type { VrService } from "../services/VrService";

export interface ControlButton {
  id: string;
  label: string;
  icon: string;
  title: string;
  action: string;
}

const ICON = {
  zoomIn: "M11 4v7H4v2h7v7h2v-7h7v-2h-7V4z",
  zoomOut: "M4 11h16v2H4z",
  home: "M12 3l9 8h-3v9h-4v-6h-4v6H6v-9H3z",
  fullscreen: "M7 4H4v3h2V6h1V4zm10 0v2h1v1h2V4h-3zM4 17v3h3v-2H6v-1H4zm14 1v1h-1v2h3v-3h-2z",
  help: "M12 2a10 10 0 100 20 10 10 0 000-20zm1 15h-2v-2h2v2zm1.6-7.4l-.9.9c-.7.7-1.1 1.3-1.1 2.5h-2v-.5c0-1 .4-1.9 1.1-2.5l1.2-1.3c.4-.3.6-.8.6-1.4 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.2 1.8-4 4-4s4 1.8 4 4c0 .9-.4 1.7-1 2.3z",
  chat: "M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.2L4 17.2V4h16v12z",
  vr: "M21 7H3c-1.1 0-2 .9-2 2v6c0 1.1.9 2 2 2h4l3-3h4l3 3h4c1.1 0 2-.9 2-2V9c0-1.1-.9-2-2-2zM9 12H7v2H5v-2H3v-2h2V8h2v2h2v2zm6 1c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm3-3c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1z",
};

export class Controls {
  private readonly el: HTMLElement;

  constructor(
    private readonly bus: EventBus,
    private readonly vr: VrService,
    target: HTMLElement,
  ) {
    this.el = this.render();
    target.appendChild(this.el);
  }

  private render(): HTMLElement {
    const bar = document.createElement("div");
    bar.className = "gv-controls";
    bar.setAttribute("role", "toolbar");
    bar.setAttribute("aria-label", "Viewer controls");

    const buttons: ControlButton[] = [
      { id: "zoom-in", label: "Zoom in", icon: ICON.zoomIn, title: "Zoom in (+)", action: ViewerEvents.KeyboardZoomIn },
      { id: "zoom-out", label: "Zoom out", icon: ICON.zoomOut, title: "Zoom out (-)", action: ViewerEvents.KeyboardZoomOut },
      { id: "home", label: "Home", icon: ICON.home, title: "Reset view (0)", action: ViewerEvents.KeyboardHome },
      { id: "fullscreen", label: "Fullscreen", icon: ICON.fullscreen, title: "Toggle fullscreen (F)", action: ViewerEvents.KeyboardFullscreen },
      { id: "help", label: "Help", icon: ICON.help, title: "Show help (H)", action: ViewerEvents.KeyboardHelp },
    ];

    for (const b of buttons) {
      const btn = document.createElement("button");
      btn.className = "gv-control-btn";
      btn.type = "button";
      btn.title = b.title;
      btn.setAttribute("aria-label", b.label);
      btn.innerHTML = `<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="${b.icon}"/></svg>`;
      btn.addEventListener("click", () => this.bus.emit(b.action));
      bar.appendChild(btn);
    }

    // VR button (only if available)
    if (this.vr.isAvailable()) {
      const vrBtn = document.createElement("button");
      vrBtn.className = "gv-control-btn gv-control-vr";
      vrBtn.type = "button";
      vrBtn.title = "Enter VR";
      vrBtn.setAttribute("aria-label", "Enter VR");
      vrBtn.innerHTML = `<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="${ICON.vr}"/></svg>`;
      vrBtn.addEventListener("click", () => {
        this.vr.enter().catch((err) => console.error("[Controls] VR enter failed:", err));
      });
      bar.appendChild(vrBtn);
    }

    return bar;
  }

  destroy(): void {
    this.el.remove();
  }
}
