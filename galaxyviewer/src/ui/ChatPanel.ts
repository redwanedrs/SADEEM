/**
 * ChatPanel — Groq LLM chat interface.
 *
 * Mirrors the original GalaxyViewer's chat panel:
 *   - Side panel on the left
 *   - Message list (user messages right-aligned, bot messages left-aligned)
 *   - Input + Send button
 *   - Typing indicator while the agent is thinking
 *
 * Subscribes to AI events on the EventBus and renders incrementally as
 * chunks arrive. Never calls the LLM directly — that's AiService's job.
 */

import { EventBus, ViewerEvents } from "../core/Events";
import type { AiService, AiMessage } from "../services/AiService";

interface ChatLine {
  role: "user" | "assistant";
  content: string;
  /** DOM node for incremental updates while streaming. */
  node?: HTMLElement;
}

export class ChatPanel {
  private readonly el: HTMLElement;
  private readonly messagesEl: HTMLElement;
  private readonly input: HTMLInputElement;
  private readonly sendBtn: HTMLButtonElement;
  private readonly typingEl: HTMLElement;
  private currentAssistantNode: HTMLElement | null = null;
  private readonly lines: ChatLine[] = [];

  constructor(
    private readonly bus: EventBus,
    private readonly ai: AiService,
    target: HTMLElement,
  ) {
    [this.el, this.messagesEl, this.input, this.sendBtn, this.typingEl] = this.render();
    target.appendChild(this.el);

    // Welcome message
    this.addBotMessage(
      "Hello! I'm your deep-space assistant, powered by Groq. " +
      "Tell me where to go — for example: \"Zoom to Mystic Mountain\".",
    );

    // Wire events
    this.sendBtn.addEventListener("click", () => this.onSend());
    this.input.addEventListener("keypress", (e) => {
      if (e.key === "Enter") this.onSend();
    });

    bus.on<AiMessage>(ViewerEvents.AiMessageStart, (msg) => {
      if (msg.role === "user") this.addUserMessage(msg.content);
    });
    bus.on<string>(ViewerEvents.AiMessageChunk, (chunk) => this.appendChunk(chunk));
    bus.on<boolean>(ViewerEvents.AiTypingChange, (typing) => this.setTyping(typing));
    bus.on<string>(ViewerEvents.AiError, (msg) => this.addBotMessage(`⚠️ ${msg}`));
  }

  private onSend(): void {
    const text = this.input.value.trim();
    if (!text) return;
    this.input.value = "";
    // Disable while processing
    this.sendBtn.disabled = true;
    this.ai.ask(text).catch((err) => {
      console.error("[ChatPanel] ask failed:", err);
    }).finally(() => {
      this.sendBtn.disabled = false;
    });
  }

  private addUserMessage(content: string): void {
    const msg = document.createElement("div");
    msg.className = "gv-chat-message gv-chat-user";
    msg.textContent = content;
    this.messagesEl.appendChild(msg);
    this.scrollToBottom();
  }

  private addBotMessage(content: string): void {
    const msg = document.createElement("div");
    msg.className = "gv-chat-message gv-chat-bot";
    msg.textContent = content;
    this.messagesEl.appendChild(msg);
    this.scrollToBottom();
  }

  private appendChunk(chunk: string): void {
    if (!this.currentAssistantNode) {
      const msg = document.createElement("div");
      msg.className = "gv-chat-message gv-chat-bot";
      this.messagesEl.appendChild(msg);
      this.currentAssistantNode = msg;
    }
    this.currentAssistantNode.textContent += chunk;
    this.scrollToBottom();
  }

  private setTyping(typing: boolean): void {
    this.typingEl.style.display = typing ? "block" : "none";
    if (!typing && this.currentAssistantNode) {
      this.currentAssistantNode = null;  // next chunk starts a new bubble
    }
  }

  private scrollToBottom(): void {
    this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
  }

  private render(): [HTMLElement, HTMLElement, HTMLInputElement, HTMLButtonElement, HTMLElement] {
    const panel = document.createElement("div");
    panel.className = "gv-chat-panel";
    panel.setAttribute("role", "complementary");
    panel.setAttribute("aria-label", "AI assistant");

    const header = document.createElement("div");
    header.className = "gv-chat-header";
    header.innerHTML = `<span class="gv-chat-title">🤖 Groq Assistant</span>`;

    const messages = document.createElement("div");
    messages.className = "gv-chat-messages";
    messages.setAttribute("role", "log");

    const typing = document.createElement("div");
    typing.className = "gv-chat-typing";
    typing.textContent = "Assistant is typing…";
    typing.style.display = "none";

    const inputRow = document.createElement("div");
    inputRow.className = "gv-chat-input-row";
    const input = document.createElement("input");
    input.type = "text";
    input.className = "gv-chat-input";
    input.placeholder = "Type a command…";
    input.setAttribute("aria-label", "Message");
    const send = document.createElement("button");
    send.type = "button";
    send.className = "gv-chat-send";
    send.textContent = "Send";

    inputRow.appendChild(input);
    inputRow.appendChild(send);
    panel.appendChild(header);
    panel.appendChild(messages);
    panel.appendChild(typing);
    panel.appendChild(inputRow);
    return [panel, messages, input, send, typing];
  }

  destroy(): void {
    this.el.remove();
  }
}
