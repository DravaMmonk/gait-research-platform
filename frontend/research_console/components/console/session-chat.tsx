"use client";

import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";

import { SessionAttachmentInput } from "@/components/console/session-attachment-input";
import type { ChatResponsePayload, ConsoleUIMessage } from "@/lib/console-types";

const starterPrompts = [
  { title: "Summarize", message: "Summarize this session." },
  { title: "Videos", message: "List the uploaded video assets in the current session." },
  { title: "Evidence", message: "Explain the evidence supporting the latest findings." },
];

function getMessageText(message: ConsoleUIMessage): string {
  return message.parts
    .filter((part): part is Extract<ConsoleUIMessage["parts"][number], { type: "text" }> => part.type === "text")
    .map((part) => part.text)
    .join("");
}

function getProgressMessages(message: ConsoleUIMessage): string[] {
  return message.parts
    .filter((part): part is Extract<ConsoleUIMessage["parts"][number], { type: "data-progress" }> => part.type === "data-progress")
    .map((part) => part.data.message)
    .filter(Boolean);
}

function getResultPayload(message: ConsoleUIMessage): ChatResponsePayload | null {
  return (
    message.parts.find(
      (part): part is Extract<ConsoleUIMessage["parts"][number], { type: "data-result" }> => part.type === "data-result",
    )?.data ?? null
  );
}

function ChatSuggestions({
  disabled,
  onSelect,
}: {
  disabled: boolean;
  onSelect: (message: string) => void;
}) {
  return (
    <div className="sessionChatSuggestions">
      {starterPrompts.map((prompt) => (
        <button
          key={prompt.title}
          type="button"
          onClick={() => onSelect(prompt.message)}
          disabled={disabled}
        >
          {prompt.title}
        </button>
      ))}
    </div>
  );
}

export function SessionChat({ threadId }: { threadId: string }) {
  const { messages, sendMessage, status, stop, error } = useChat<ConsoleUIMessage>({
    id: threadId,
    transport: new DefaultChatTransport({
      api: "/api/chat",
    }),
  });

  const inProgress = status === "submitted" || status === "streaming";
  const chatReady = !inProgress;
  const showEmptyState = messages.length === 0;

  async function handleSend(text: string) {
    await sendMessage(
      { text },
      {
        body: {
          threadId,
        },
      },
    );
  }

  return (
    <div className="research-chat">
      <div className="sessionChatMessages">
        <div className="sessionChatMessagesContainer">
          {showEmptyState ? (
            <section className="sessionChatEmptyState">
              <p className="sessionChatEyebrow">Research Assistant</p>
              <h2>Ask a question about the current session.</h2>
              <p>Ask about evidence, videos, metrics, or the latest run.</p>
              <ChatSuggestions disabled={inProgress} onSelect={(message) => void handleSend(message)} />
            </section>
          ) : null}

          {messages.map((message) => {
            const text = getMessageText(message);
            const progressMessages = getProgressMessages(message);
            const result = getResultPayload(message);

            return (
              <article
                key={message.id}
                className={`sessionChatMessage ${message.role === "user" ? "sessionChatUserMessage" : "sessionChatAssistantMessage"}`}
              >
                {message.role === "assistant" && progressMessages.length > 0 ? (
                  <div className="sessionChatProgressList">
                    {progressMessages.map((progress, index) => (
                      <div key={`${message.id}-progress-${index}`} className="sessionChatProgressItem">
                        {progress}
                      </div>
                    ))}
                  </div>
                ) : null}

                {text ? <div className="sessionChatMessageText">{text}</div> : null}

                {message.role === "assistant" && !text && inProgress ? (
                  <div className="sessionChatTyping">Working on your request...</div>
                ) : null}

                {message.role === "assistant" && result?.run_id ? (
                  <div className="sessionChatMeta">Run {result.run_id.slice(0, 8)}</div>
                ) : null}
              </article>
            );
          })}

          {error ? (
            <div className="sessionChatError">
              Something went wrong while contacting the assistant.
            </div>
          ) : null}
        </div>
      </div>

      {!showEmptyState ? (
        <div className="sessionChatMessagesFooter">
          <p className="sessionChatFooterLabel">Quick prompts</p>
          <ChatSuggestions disabled={inProgress} onSelect={(message) => void handleSend(message)} />
        </div>
      ) : null}

      <SessionAttachmentInput
        chatReady={chatReady}
        inProgress={inProgress}
        onSend={handleSend}
        onStop={stop}
        threadId={threadId}
      />
    </div>
  );
}
