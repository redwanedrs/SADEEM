/**
 * HelpOverlay — dismissible overlay listing keyboard shortcuts.
 *
 * Toggled via the "help" control button or the `H` key. Clicking anywhere
 * outside the panel or pressing Escape also closes it.
 */

export class HelpOverlay {
  private readonly el: HTMLElement;

  constructor(target: HTMLElement) {
    this.el = this.render();
    target.appendChild(this.el);
    this.el.addEventListener("click", (e) => {
      if (e.target === this.el) this.hide();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") this.hide();
    });
  }

  show(): void {
    this.el.classList.add("gv-help-visible");
  }

  hide(): void {
    this.el.classList.remove("gv-help-visible");
  }

  toggle(): void {
    this.el.classList.toggle("gv-help-visible");
  }

  private render(): HTMLElement {
    const overlay = document.createElement("div");
    overlay.className = "gv-help";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-hidden", "true");

    const panel = document.createElement("div");
    panel.className = "gv-help-panel";

    panel.innerHTML = `
      <h2 class="gv-help-title">Keyboard shortcuts</h2>
      <ul class="gv-help-list">
        <li><kbd>+</kbd> / <kbd>=</kbd> Zoom in</li>
        <li><kbd>−</kbd> / <kbd>_</kbd> Zoom out</li>
        <li><kbd>0</kbd> Reset to home view</li>
        <li><kbd>↑</kbd> <kbd>↓</kbd> <kbd>←</kbd> <kbd>→</kbd> Pan</li>
        <li><kbd>F</kbd> Toggle fullscreen</li>
        <li><kbd>H</kbd> Toggle this help</li>
        <li><kbd>Esc</kbd> Close dialogs</li>
      </ul>
      <p class="gv-help-tip">Click anywhere outside this panel to close it.</p>
    `;

    overlay.appendChild(panel);
    return overlay;
  }
}
