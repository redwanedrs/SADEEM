/**
 * GalaxyViewer — Logger.
 *
 * A thin wrapper around the console that:
 *   - prefixes every message with a timestamp and the `[GalaxyViewer]` tag
 *   - supports log levels (debug / info / warn / error)
 *   - forwards errors to the EventBus so the UI can surface them
 *
 * In production builds the debug level is stripped automatically.
 */

import { EventBus, ViewerEvents } from "./Events";

export type LogLevel = "debug" | "info" | "warn" | "error";

const LEVEL_ORDER: Record<LogLevel, number> = {
  debug: 10,
  info: 20,
  warn: 30,
  error: 40,
};

export class Logger {
  private level: LogLevel = "info";

  constructor(private readonly bus: EventBus) {}

  setLevel(level: LogLevel): void {
    this.level = level;
  }

  debug(message: string, context?: unknown): void {
    this.emit("debug", message, context);
  }

  info(message: string, context?: unknown): void {
    this.emit("info", message, context);
  }

  warn(message: string, context?: unknown): void {
    this.emit("warn", message, context);
  }

  error(message: string, context?: unknown): void {
    this.emit("error", message, context);
    this.bus.emit(ViewerEvents.Error, { message, context });
  }

  private emit(level: LogLevel, message: string, context?: unknown): void {
    if (LEVEL_ORDER[level] < LEVEL_ORDER[this.level]) return;
    const ts = new Date().toISOString().split("T")[1].replace("Z", "");
    const prefix = `%c[${ts}] [GalaxyViewer]`;
    const style =
      level === "error"
        ? "color:#ff5a5a;font-weight:600"
        : level === "warn"
        ? "color:#f5a623;font-weight:600"
        : level === "info"
        ? "color:#5aa8ff"
        : "color:#888";
    const payload = context != null ? ` ${message} ${JSON.stringify(context)}` : ` ${message}`;
    // eslint-disable-next-line no-console
    console[level === "debug" ? "log" : level](prefix + payload, style);
  }
}
