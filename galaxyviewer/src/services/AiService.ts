/**
 * AiService — Groq LLM integration with tool-calling.
 *
 * Mirrors the original GalaxyViewer's Groq chatbot:
 *   - Uses Groq's free OpenAI-compatible endpoint
 *   - Default model: llama-3.1-8b-instant (free, fast)
 *   - Tool calling: the agent has a `goToMarker(markerId)` tool that flies
 *     the viewport to any POI. When the user says "Zoom to Mystic Mountain",
 *     the agent calls goToMarker, the viewport flies there, and the agent
 *     confirms the action.
 *
 * When no API key is configured, the service falls back to demo mode: it
 * pattern-matches the user's message against POI names and calls goToMarker
 * directly, so the feature is always demonstrable.
 *
 * Architecture
 * ------------
 * The service never touches the DOM or the OpenSeadragon instance. It:
 *   1. Builds the system prompt with the list of available POIs
 *   2. Calls the Groq API with the goToMarker tool definition
 *   3. If the model returns a tool_call, dispatches a `PoiFlyTo` event
 *      (the Viewer subscribes and performs the actual fly-to) and sends
 *      the tool result back to the model for a final confirmation
 *   4. Streams the final response to the chat panel via `AiMessageChunk`
 */

import { EventBus, ViewerEvents } from "../core/Events";
import type { AiConfig } from "../core/Config";
import { AiError } from "../core/Errors";
import type { Logger } from "../core/Logger";
import type { PoiService, Poi } from "./PoiService";

export interface AiMessage {
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  tool_calls?: GroqToolCall[];
  tool_call_id?: string;
  name?: string;
}

export interface GroqToolCall {
  id: string;
  type: "function";
  function: { name: string; arguments: string };
}

export interface GroqResponse {
  choices: { message: AiMessage }[];
}

export class AiService {
  private typing = false;
  private readonly history: AiMessage[] = [];

  constructor(
    private readonly bus: EventBus,
    private readonly log: Logger,
    private readonly config: AiConfig,
    private readonly pois: PoiService,
  ) {}

  // ------------------------------------------------------------------
  // Public API
  // ------------------------------------------------------------------
  isConfigured(): boolean {
    return this.config.enabled && Boolean(this.config.apiKey);
  }

  isTyping(): boolean {
    return this.typing;
  }

  getHistory(): AiMessage[] {
    return [...this.history];
  }

  /**
   * Send a user message to Groq and stream the response. Returns the final
   * assistant text.
   */
  async ask(question: string): Promise<string> {
    if (!this.config.enabled) {
      throw new AiError("AI features are disabled in config.");
    }

    const userMessage: AiMessage = { role: "user", content: question };
    this.history.push(userMessage);
    this.bus.emit<AiMessage>(ViewerEvents.AiMessageStart, userMessage);

    this.setTyping(true);
    try {
      const answer = this.isConfigured()
        ? await this.callGroq(question)
        : await this.demoResponse(question);

      const assistantMessage: AiMessage = { role: "assistant", content: answer };
      this.history.push(assistantMessage);
      this.bus.emit<AiMessage>(ViewerEvents.AiMessageComplete, assistantMessage);
      return answer;
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      this.log.error("AI request failed", { error: msg });
      this.bus.emit<string>(ViewerEvents.AiError, msg);
      throw new AiError(msg);
    } finally {
      this.setTyping(false);
    }
  }

  clearHistory(): void {
    this.history.length = 0;
  }

  // ------------------------------------------------------------------
  // Internals — Groq API call with tool-calling
  // ------------------------------------------------------------------
  private async callGroq(question: string): Promise<string> {
    // Build the system prompt with the current POI list
    const systemPrompt = this.buildSystemPrompt();
    const messages: AiMessage[] = [
      { role: "system", content: systemPrompt },
      ...this.history.slice(-10),
    ];

    const payload: Record<string, unknown> = {
      model: this.config.model,
      messages,
      temperature: this.config.temperature,
      max_tokens: this.config.maxTokens,
    };
    if (this.config.enableTools) {
      payload.tools = this.buildTools();
      payload.tool_choice = "auto";
    }

    const res = await fetch(this.config.endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.config.apiKey}`,
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new AiError(`Groq API returned HTTP ${res.status}: ${text}`,
        { status: res.status, body: text });
    }

    const data = (await res.json()) as GroqResponse;
    const message = data.choices?.[0]?.message;
    if (!message) {
      throw new AiError("Groq API returned an empty response.");
    }

    // Case 1: model wants to call a tool
    if (message.tool_calls && message.tool_calls.length > 0) {
      this.history.push(message);  // record assistant's tool-call message

      for (const call of message.tool_calls) {
        const result = await this.executeToolCall(call);
        this.history.push({
          role: "tool",
          tool_call_id: call.id,
          name: call.function.name,
          content: result,
        });
      }

      // Send the tool results back to Groq for a final confirmation
      const followUp = await this.callGroqFollowUp();
      // Stream the final answer in chunks for the typing effect
      this.emitInChunks(followUp);
      return followUp;
    }

    // Case 2: plain assistant message
    const content = message.content ?? "";
    this.emitInChunks(content);
    return content;
  }

  private async callGroqFollowUp(): Promise<string> {
    const payload = {
      model: this.config.model,
      messages: [
        { role: "system", content: this.buildSystemPrompt() },
        ...this.history.slice(-12),
      ],
      temperature: this.config.temperature,
      max_tokens: this.config.maxTokens,
    };
    const res = await fetch(this.config.endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.config.apiKey}`,
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new AiError(`Groq follow-up returned HTTP ${res.status}`);
    }
    const data = (await res.json()) as GroqResponse;
    return data.choices?.[0]?.message?.content ?? "Done.";
  }

  private async executeToolCall(call: GroqToolCall): Promise<string> {
    const name = call.function.name;
    let args: Record<string, unknown>;
    try {
      args = JSON.parse(call.function.arguments);
    } catch {
      args = {};
    }

    this.bus.emit<GroqToolCall>(ViewerEvents.AiToolCall, call);

    if (name === "goToMarker") {
      const markerId = String(args.markerId ?? "");
      // Dispatch the fly-to via the PoiService (which emits PoiFlyTo)
      const result = this.pois.flyTo(markerId);
      this.log.info(`Tool goToMarker("${markerId}") → ${result}`);
      return result;
    }

    return `Error: unknown tool "${name}".`;
  }

  // ------------------------------------------------------------------
  // Internals — demo mode (no API key)
  // ------------------------------------------------------------------
  private async demoResponse(question: string): Promise<string> {
    this.log.info("AI in demo mode (no Groq API key) — pattern-matching POI names.");
    await new Promise((r) => setTimeout(r, 300));

    const lower = question.toLowerCase();
    const poi = this.pois.list().find((p) => {
      const name = p.name.toLowerCase();
      const title = p.title.toLowerCase();
      const id = p.id.toLowerCase();
      return lower.includes(name) || lower.includes(title) || lower.includes(id);
    });

    if (poi) {
      const result = this.pois.flyTo(poi.id);
      const answer =
        `[Demo mode] ${result} (Set ViewerConfig.ai.apiKey to enable real Groq LLM responses.)`;
      this.emitInChunks(answer);
      return answer;
    }

    const available = this.pois.list().map((p) => `• ${p.title} (id: '${p.id}')`).join("\n");
    const answer =
      `[Demo mode] I can navigate to these named objects:\n${available}\n\n` +
      `Try saying "Zoom to Mystic Mountain" or "Show me Eta Carinae".\n` +
      `Set ViewerConfig.ai.apiKey to enable real Groq LLM responses.`;
    this.emitInChunks(answer);
    return answer;
  }

  // ------------------------------------------------------------------
  // Internals — system prompt + tool definitions
  // ------------------------------------------------------------------
  private buildSystemPrompt(): string {
    const markers = this.pois.list().map((p) => `${p.title} (id: '${p.id}')`).join(", ");
    return [
      this.config.systemPrompt,
      "",
      `Available markers: ${markers}.`,
    ].join("\n");
  }

  private buildTools() {
    const markerIdDescription =
      "The unique identifier for the marker. One of: " +
      this.pois.list().map((s) => `'${s.id}' for ${s.title}`).join(", ") + ".";
    return [
      {
        type: "function",
        function: {
          name: "goToMarker",
          description:
            "Pans and zooms the viewport to a specific named marker on the deep zoom image.",
          parameters: {
            type: "object",
            properties: {
              markerId: { type: "string", description: markerIdDescription },
            },
            required: ["markerId"],
          },
        },
      },
    ];
  }

  private emitInChunks(text: string): void {
    const words = text.split(/(\s+)/);
    for (const w of words) {
      this.bus.emit<string>(ViewerEvents.AiMessageChunk, w);
    }
  }

  private setTyping(value: boolean): void {
    this.typing = value;
    this.bus.emit<boolean>(ViewerEvents.AiTypingChange, value);
  }
}
