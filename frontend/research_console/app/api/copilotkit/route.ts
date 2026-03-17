import {
  CopilotRuntime,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import {
  AbstractAgent,
  EventType,
  type BaseEvent,
  type Message,
  type RunAgentInput,
} from "@ag-ui/client";
import { Observable } from "rxjs";

import { getHoundForwardApiBase } from "@/lib/hound-forward-api";

type ConsoleResponsePayload = {
  message?: string;
  thread?: Array<{ role: string; content: string }>;
};

function flattenMessageContent(content: Message["content"]): string {
  if (typeof content === "string") {
    return content;
  }

  if (!Array.isArray(content)) {
    return "";
  }

  return content
    .map((part) => {
      if (part && typeof part === "object" && "type" in part && part.type === "text" && "text" in part) {
        return typeof part.text === "string" ? part.text : "";
      }
      return "";
    })
    .filter(Boolean)
    .join("\n");
}

function getLatestUserMessage(messages: Message[]): string {
  const latest = [...messages]
    .reverse()
    .find((message) => message.role === "user");

  return flattenMessageContent(latest?.content).trim();
}

function getAssistantReply(payload: ConsoleResponsePayload): string {
  if (payload.message?.trim()) {
    return payload.message.trim();
  }

  const assistantMessage = [...(payload.thread ?? [])]
    .reverse()
    .find((message) => message.role === "assistant" && message.content.trim());

  return assistantMessage?.content?.trim() || "No response.";
}

class HoundForwardAgent extends AbstractAgent {
  run(input: RunAgentInput): Observable<BaseEvent> {
    return new Observable<BaseEvent>((subscriber) => {
      const threadId = input.threadId || this.threadId || crypto.randomUUID();
      const runId = input.runId || crypto.randomUUID();
      const messageId = crypto.randomUUID();
      const userMessage = getLatestUserMessage(input.messages);

      subscriber.next({
        type: EventType.RUN_STARTED,
        threadId,
        runId,
      });

      void (async () => {
        try {
          const response = await fetch(`${getHoundForwardApiBase()}/agent/console/respond`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              session_id: threadId,
              message: userMessage,
              display_preferences: [],
            }),
            cache: "no-store",
          });

          if (!response.ok) {
            throw new Error(`Hound Forward responded with ${response.status}.`);
          }

          const payload = (await response.json()) as ConsoleResponsePayload;
          const reply = getAssistantReply(payload);

          subscriber.next({
            type: EventType.TEXT_MESSAGE_START,
            messageId,
            role: "assistant",
          });
          subscriber.next({
            type: EventType.TEXT_MESSAGE_CONTENT,
            messageId,
            delta: reply,
          });
          subscriber.next({
            type: EventType.TEXT_MESSAGE_END,
            messageId,
          });
          subscriber.next({
            type: EventType.RUN_FINISHED,
            threadId,
            runId,
          });
          subscriber.complete();
        } catch (error) {
          subscriber.next({
            type: EventType.RUN_ERROR,
            message: error instanceof Error ? error.message : "The agent is currently unavailable.",
          });
          subscriber.error(error instanceof Error ? error : new Error("The agent is currently unavailable."));
        }
      })();

      return () => undefined;
    });
  }
}

const runtime = new CopilotRuntime({
  agents: {
    default: new HoundForwardAgent(),
  },
});
const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
  endpoint: "/api/copilotkit",
  runtime,
});

export const POST = handleRequest;
export const OPTIONS = handleRequest;
