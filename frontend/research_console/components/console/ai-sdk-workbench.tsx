"use client";

import { experimental_useObject as useObject, useChat, useCompletion } from "@ai-sdk/react";
import { DefaultChatTransport, isTextUIPart, isToolUIPart, type UIMessage } from "ai";
import { useEffect, useMemo, useState } from "react";

import { defaultGaitInsightInput, devChatStarterPrompts, devCompletionPrompts, gaitInsightSchema } from "@/lib/ai-sdk-playground";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Panel } from "@/components/ui/panel";
import { ScrollArea } from "@/components/ui/scroll-area";

type RuntimeStatus = {
  configured: boolean;
  mode: "live" | "mock";
  provider: "google-vertex" | "openai" | "mock";
  model: string;
  reason: string;
};

type WorkbenchMode = "tool-chat" | "completion" | "object";

function formatJson(value: unknown) {
  return JSON.stringify(value, null, 2);
}

function StreamingIndicator({ label }: { label: string }) {
  return (
    <div className="inline-flex items-center gap-2 text-xs text-muted-foreground">
      <span className="h-2 w-2 animate-pulse rounded-full bg-[hsl(var(--primary))]" />
      <span>{label}</span>
    </div>
  );
}

function ToolChatPane() {
  const [input, setInput] = useState("");
  const { messages, sendMessage, status, stop, error } = useChat<UIMessage>({
    id: "main-interface-ai-sdk-chat",
    transport: new DefaultChatTransport({
      api: "/api/ai-sdk/chat",
    }),
  });

  const inProgress = status === "submitted" || status === "streaming";

  async function handleSend(text: string) {
    if (!text.trim()) {
      return;
    }

    setInput("");
    await sendMessage({ text: text.trim() });
  }

  return (
    <div className="grid min-h-0 grid-rows-[auto_minmax(0,1fr)_auto] gap-3">
      <div className="flex flex-wrap gap-2">
        {devChatStarterPrompts.map((prompt) => (
          <Button
            key={prompt}
            type="button"
            variant="ghost"
            className="h-auto rounded-full px-3 py-1.5 text-xs"
            disabled={inProgress}
            onClick={() => void handleSend(prompt)}
          >
            {prompt}
          </Button>
        ))}
      </div>

      <ScrollArea className="min-h-0 rounded-[1rem] border border-[hsl(var(--border)/0.68)] bg-[var(--panel-subtle)]">
        <div className="space-y-3 p-3">
          {messages.length === 0 ? (
            <p className="text-sm leading-6 text-muted-foreground">Ask for gait metrics, runtime status, or a tool-enabled explanation.</p>
          ) : null}

          {messages.map((message) => {
            const textParts = message.parts.filter(isTextUIPart);
            const toolParts = message.parts.filter(isToolUIPart);

            return (
              <article
                key={message.id}
                className={`space-y-2 rounded-[1rem] border px-3 py-3 ${
                  message.role === "user"
                    ? "border-[hsl(var(--primary)/0.24)] bg-[hsl(var(--primary)/0.08)]"
                    : "border-[hsl(var(--border)/0.68)] bg-background"
                }`}
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">{message.role}</p>
                  {message.role === "assistant" && toolParts.length > 0 ? <Badge variant="outline">{toolParts.length} tools</Badge> : null}
                </div>

                {textParts.map((part, index) => (
                  <p key={`${message.id}-text-${index}`} className="text-sm leading-6 text-foreground">
                    {part.text}
                  </p>
                ))}

                {toolParts.map((part) => (
                  <div key={part.toolCallId} className="rounded-[0.9rem] border border-[hsl(var(--border)/0.68)] bg-[var(--panel-subtle)] p-3">
                    <div className="flex items-center justify-between gap-3">
                      <code className="text-xs font-semibold">{part.type.replace(/^tool-/, "")}</code>
                      <Badge variant="muted">{part.state}</Badge>
                    </div>
                    {"input" in part && part.input !== undefined ? (
                      <pre className="mt-2 overflow-x-auto text-xs leading-5 text-muted-foreground">{formatJson(part.input)}</pre>
                    ) : null}
                    {"output" in part && part.output !== undefined ? (
                      <pre className="mt-2 overflow-x-auto text-xs leading-5 text-foreground">{formatJson(part.output)}</pre>
                    ) : null}
                  </div>
                ))}
              </article>
            );
          })}

          {inProgress ? <StreamingIndicator label="Streaming tool-enabled response..." /> : null}
        </div>
      </ScrollArea>

      <div className="space-y-2">
        <Input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask the tool chat to inspect metrics or runtime state..."
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              void handleSend(input);
            }
          }}
        />
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs text-muted-foreground">{error ? "Chat route failed." : "Uses streamText + tool() behind a dedicated main-interface route."}</p>
          <div className="flex gap-2">
            <Button type="button" variant="ghost" onClick={stop} disabled={!inProgress}>
              Stop
            </Button>
            <Button type="button" onClick={() => void handleSend(input)} disabled={inProgress || !input.trim()}>
              Send
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function CompletionPane() {
  const [draft, setDraft] = useState<string>(devCompletionPrompts[0]);
  const { completion, complete, isLoading, stop, setCompletion, error } = useCompletion({
    api: "/api/ai-sdk/completion",
  });

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {devCompletionPrompts.map((prompt) => (
          <Button
            key={prompt}
            type="button"
            variant="ghost"
            className="h-auto rounded-full px-3 py-1.5 text-xs"
            disabled={isLoading}
            onClick={() => {
              setDraft(prompt);
              void complete(prompt);
            }}
          >
            {prompt}
          </Button>
        ))}
      </div>

      <Input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Enter a single-turn prompt..." />

      <div className="flex justify-end gap-2">
        <Button type="button" variant="ghost" onClick={() => setCompletion("")} disabled={isLoading && !completion}>
          Clear
        </Button>
        <Button type="button" variant="ghost" onClick={stop} disabled={!isLoading}>
          Stop
        </Button>
        <Button type="button" onClick={() => void complete(draft)} disabled={isLoading || !draft.trim()}>
          Generate
        </Button>
      </div>

      <ScrollArea className="h-56 rounded-[1rem] border border-[hsl(var(--border)/0.68)] bg-[var(--panel-subtle)]">
        <div className="p-3">
          <pre className="whitespace-pre-wrap text-sm leading-6 text-foreground">{completion || "Completion output will stream here."}</pre>
        </div>
      </ScrollArea>

      {isLoading ? <StreamingIndicator label="Receiving streamed completion tokens..." /> : null}
      <p className="text-xs text-muted-foreground">{error ? "Completion route failed." : "Uses useCompletion for single-turn streamed copy generation."}</p>
    </div>
  );
}

function ObjectPane() {
  const [form, setForm] = useState(defaultGaitInsightInput);
  const { object, submit, isLoading, clear, stop, error } = useObject({
    api: "/api/ai-sdk/object",
    schema: gaitInsightSchema,
  });

  const prettyObject = useMemo(() => (object ? formatJson(object) : "Structured object output will stream here."), [object]);

  return (
    <div className="space-y-3">
      <div className="grid gap-3">
        <Input
          value={form.subject}
          onChange={(event) => setForm((current) => ({ ...current, subject: event.target.value }))}
          placeholder="Subject"
        />
        <Input
          value={form.videoLabel}
          onChange={(event) => setForm((current) => ({ ...current, videoLabel: event.target.value }))}
          placeholder="Video label"
        />
        <Input
          value={form.concern}
          onChange={(event) => setForm((current) => ({ ...current, concern: event.target.value }))}
          placeholder="Concern"
        />
      </div>

      <div className="flex justify-end gap-2">
        <Button type="button" variant="ghost" onClick={clear} disabled={isLoading && !object}>
          Clear
        </Button>
        <Button type="button" variant="ghost" onClick={stop} disabled={!isLoading}>
          Stop
        </Button>
        <Button type="button" onClick={() => submit(form)} disabled={isLoading}>
          Stream Object
        </Button>
      </div>

      <ScrollArea className="h-64 rounded-[1rem] border border-[hsl(var(--border)/0.68)] bg-[var(--panel-subtle)]">
        <div className="p-3">
          <pre className="whitespace-pre-wrap text-xs leading-6 text-foreground">{prettyObject}</pre>
        </div>
      </ScrollArea>

      {isLoading ? <StreamingIndicator label="Growing structured object from streamed JSON..." /> : null}
      <p className="text-xs text-muted-foreground">{error ? "Object route failed." : "Uses useObject + streamObject for schema-bound JSON streaming."}</p>
    </div>
  );
}

export function AiSdkWorkbench() {
  const [mode, setMode] = useState<WorkbenchMode>("tool-chat");
  const [runtime, setRuntime] = useState<RuntimeStatus | null>(null);

  useEffect(() => {
    let active = true;

    async function loadRuntime() {
      const response = await fetch("/api/ai-sdk/status", { cache: "no-store" });
      if (!response.ok) {
        return;
      }

      const payload = (await response.json()) as RuntimeStatus;
      if (active) {
        setRuntime(payload);
      }
    }

    void loadRuntime();

    return () => {
      active = false;
    };
  }, []);

  return (
    <section className="grid h-full min-h-0 min-w-0 overflow-hidden px-4 pb-4 sm:px-6 sm:pb-6 xl:pl-0">
      <Panel
        tone="elevated"
        padding="roomy"
        className="grid h-full min-h-0 min-w-0 grid-rows-[auto_auto_minmax(0,1fr)] gap-4 rounded-[1.4rem]"
      >
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">AI SDK</p>
            <Badge variant={runtime?.mode === "live" ? "default" : "muted"}>{runtime?.mode ?? "loading"}</Badge>
            <Badge variant="outline">{runtime?.model ?? "Resolving runtime"}</Badge>
          </div>
          <h2 className="text-2xl font-semibold tracking-[-0.03em] text-foreground">Main Interface Workbench</h2>
          <p className="text-sm leading-6 text-muted-foreground">
            Streamed tool chat, single-turn completion, and structured object generation are available directly beside the main session console.
          </p>
          {runtime ? <p className="text-xs leading-5 text-muted-foreground">{runtime.reason}</p> : null}
        </div>

        <div className="flex flex-wrap gap-2">
          <Button type="button" variant={mode === "tool-chat" ? "secondary" : "ghost"} onClick={() => setMode("tool-chat")}>
            Tool Chat
          </Button>
          <Button type="button" variant={mode === "completion" ? "secondary" : "ghost"} onClick={() => setMode("completion")}>
            Completion
          </Button>
          <Button type="button" variant={mode === "object" ? "secondary" : "ghost"} onClick={() => setMode("object")}>
            Object
          </Button>
        </div>

        <div className="min-h-0 min-w-0 overflow-hidden">
          {mode === "tool-chat" ? <ToolChatPane /> : null}
          {mode === "completion" ? <CompletionPane /> : null}
          {mode === "object" ? <ObjectPane /> : null}
        </div>
      </Panel>
    </section>
  );
}
