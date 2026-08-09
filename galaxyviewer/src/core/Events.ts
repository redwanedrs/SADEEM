/**
 * GalaxyViewer — Typed event bus.
 *
 * A minimal publish/subscribe mechanism that the services use to communicate
 * without holding direct references to each other.
 */

type EventHandler<T = unknown> = (payload: T) => void;

export class EventBus {
  private readonly handlers = new Map<string, Set<EventHandler<any>>>();

  on<T>(event: string, handler: EventHandler<T>): () => void {
    let set = this.handlers.get(event);
    if (!set) {
      set = new Set();
      this.handlers.set(event, set);
    }
    set.add(handler as EventHandler<any>);
    return () => this.off(event, handler);
  }

  off<T>(event: string, handler: EventHandler<T>): void {
    const set = this.handlers.get(event);
    if (set) {
      set.delete(handler as EventHandler<any>);
      if (set.size === 0) this.handlers.delete(event);
    }
  }

  emit<T>(event: string, payload?: T): void {
    const set = this.handlers.get(event);
    if (!set) return;
    for (const handler of Array.from(set)) {
      try {
        handler(payload as T);
      } catch (err) {
        console.error(`[EventBus] handler for "${event}" threw:`, err);
      }
    }
  }

  clear(): void {
    this.handlers.clear();
  }
}

// ---------------------------------------------------------------------------
// Canonical event names
// ---------------------------------------------------------------------------
export const ViewerEvents = {
  // Viewport
  ViewportChange: "viewport:change",
  ZoomChange: "viewport:zoom",
  PanChange: "viewport:pan",
  // Tiles
  TileLoadStart: "tile:load-start",
  TileLoadComplete: "tile:load-complete",
  TileLoadError: "tile:load-error",
  // Lifecycle
  Open: "viewer:open",
  Close: "viewer:close",
  Resize: "viewer:resize",
  Error: "viewer:error",
  // Points of Interest
  PoiAdded: "poi:added",
  PoiRemoved: "poi:removed",
  PoiSelected: "poi:selected",
  PoiFocus: "poi:focus",
  PoiFlyTo: "poi:fly-to",
  // AI (Groq agent)
  AiMessageStart: "ai:message-start",
  AiMessageChunk: "ai:message-chunk",
  AiMessageComplete: "ai:message-complete",
  AiError: "ai:error",
  AiTypingChange: "ai:typing-change",
  AiToolCall: "ai:tool-call",
  // VR
  VrSessionStart: "vr:session-start",
  VrSessionEnd: "vr:session-end",
  VrError: "vr:error",
  // Keyboard intents
  KeyboardZoomIn: "keyboard:zoom-in",
  KeyboardZoomOut: "keyboard:zoom-out",
  KeyboardHome: "keyboard:home",
  KeyboardPan: "keyboard:pan",
  KeyboardFullscreen: "keyboard:fullscreen",
  KeyboardHelp: "keyboard:help",
} as const;

export type ViewerEventName = (typeof ViewerEvents)[keyof typeof ViewerEvents];
