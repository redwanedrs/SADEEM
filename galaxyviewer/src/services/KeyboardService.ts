/**
 * KeyboardService — accessible keyboard navigation.
 *
 * Binds a small, predictable set of keyboard shortcuts on the viewer
 * container. All shortcuts are also discoverable via the on-screen help
 * tooltip, so users don't need to memorise them.
 *
 * Shortcuts
 * ---------
 *   + / =       Zoom in
 *   - / _       Zoom out
 *   0           Reset to home (fit) view
 *   Arrow keys  Pan
 *   F           Toggle fullscreen
 *   H           Toggle help overlay
 */

import { EventBus } from "../core/Events";
import type { Logger } from "../core/Logger";

export interface KeyboardShortcuts {
  zoomIn: string[];
  zoomOut: string[];
  home: string[];
  panUp: string[];
  panDown: string[];
  panLeft: string[];
  panRight: string[];
  fullscreen: string[];
  help: string[];
}

export const DEFAULT_SHORTCUTS: KeyboardShortcuts = {
  zoomIn: ["+", "="],
  zoomOut: ["-", "_"],
  home: ["0"],
  panUp: ["ArrowUp", "w"],
  panDown: ["ArrowDown", "s"],
  panLeft: ["ArrowLeft", "a"],
  panRight: ["ArrowRight", "d"],
  fullscreen: ["f"],
  help: ["h"],
};

export class KeyboardService {
  private bound = false;

  constructor(
    private readonly bus: EventBus,
    private readonly log: Logger,
    private readonly shortcuts: KeyboardShortcuts = DEFAULT_SHORTCUTS,
  ) {}

  attach(target: HTMLElement | Document = document): void {
    if (this.bound) return;
    target.addEventListener("keydown", this.onKeyDown as EventListener);
    this.bound = true;
    this.log.debug("KeyboardService attached.");
  }

  detach(target: HTMLElement | Document = document): void {
    if (!this.bound) return;
    target.removeEventListener("keydown", this.onKeyDown as EventListener);
    this.bound = false;
  }

  private onKeyDown = (e: KeyboardEvent): void => {
    // Ignore key events from form fields.
    const target = e.target as HTMLElement | null;
    if (target && /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName)) return;

    const key = e.key;
    const s = this.shortcuts;

    if (s.zoomIn.includes(key)) {
      e.preventDefault();
      this.bus.emit("keyboard:zoom-in");
    } else if (s.zoomOut.includes(key)) {
      e.preventDefault();
      this.bus.emit("keyboard:zoom-out");
    } else if (s.home.includes(key)) {
      e.preventDefault();
      this.bus.emit("keyboard:home");
    } else if (s.panUp.includes(key)) {
      e.preventDefault();
      this.bus.emit("keyboard:pan", { dx: 0, dy: -0.05 });
    } else if (s.panDown.includes(key)) {
      e.preventDefault();
      this.bus.emit("keyboard:pan", { dx: 0, dy: 0.05 });
    } else if (s.panLeft.includes(key)) {
      e.preventDefault();
      this.bus.emit("keyboard:pan", { dx: -0.05, dy: 0 });
    } else if (s.panRight.includes(key)) {
      e.preventDefault();
      this.bus.emit("keyboard:pan", { dx: 0.05, dy: 0 });
    } else if (s.fullscreen.includes(key)) {
      e.preventDefault();
      this.bus.emit("keyboard:fullscreen");
    } else if (s.help.includes(key)) {
      e.preventDefault();
      this.bus.emit("keyboard:help");
    }
  };
}
