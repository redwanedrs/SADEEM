/**
 * Theme — centralised design tokens.
 *
 * The cyan-on-dark "space" aesthetic matches the original GalaxyViewer.
 */

export interface ThemeTokens {
  bgCanvas: string;
  bgChrome: string;
  bgChromeHover: string;
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  accent: string;
  accentHover: string;
  accentGlow: string;
  success: string;
  warning: string;
  error: string;
  border: string;
  radius: string;
  fontStack: string;
  fontMono: string;
}

export const DARK_THEME: ThemeTokens = {
  bgCanvas: "#0a0a1a",
  bgChrome: "rgba(10, 20, 40, 0.85)",
  bgChromeHover: "rgba(20, 35, 60, 0.95)",
  textPrimary: "#e0f7ff",
  textSecondary: "#b9c5d6",
  textMuted: "#6c7178",
  accent: "#00ffff",
  accentHover: "#88f8ff",
  accentGlow: "rgba(0, 255, 255, 0.5)",
  success: "#4ade80",
  warning: "#f5a623",
  error: "#ff5a5a",
  border: "rgba(0, 255, 255, 0.2)",
  radius: "12px",
  fontStack: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  fontMono: '"SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace',
};

export function installTheme(tokens: ThemeTokens = DARK_THEME): void {
  const root = document.documentElement;
  root.style.setProperty("--gv-bg-canvas", tokens.bgCanvas);
  root.style.setProperty("--gv-bg-chrome", tokens.bgChrome);
  root.style.setProperty("--gv-bg-chrome-hover", tokens.bgChromeHover);
  root.style.setProperty("--gv-text-primary", tokens.textPrimary);
  root.style.setProperty("--gv-text-secondary", tokens.textSecondary);
  root.style.setProperty("--gv-text-muted", tokens.textMuted);
  root.style.setProperty("--gv-accent", tokens.accent);
  root.style.setProperty("--gv-accent-hover", tokens.accentHover);
  root.style.setProperty("--gv-accent-glow", tokens.accentGlow);
  root.style.setProperty("--gv-success", tokens.success);
  root.style.setProperty("--gv-warning", tokens.warning);
  root.style.setProperty("--gv-error", tokens.error);
  root.style.setProperty("--gv-border", tokens.border);
  root.style.setProperty("--gv-radius", tokens.radius);
  root.style.setProperty("--gv-font", tokens.fontStack);
  root.style.setProperty("--gv-font-mono", tokens.fontMono);
}
