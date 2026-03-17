"use client";

import { useEffect, useState } from "react";
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";

const starterPrompts = [
  { title: "Summarize", message: "Summarize this session." },
  { title: "Table", message: "Show the result as a table." },
  { title: "Evidence", message: "Explain the evidence." },
];

export function CopilotAgentConsole() {
  const [threadId, setThreadId] = useState("");
  const [status, setStatus] = useState("Connecting");

  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      try {
        const response = await fetch("/api/console/session", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });

        if (!response.ok) {
          throw new Error("Unable to start agent session.");
        }

        const payload = (await response.json()) as { session_id?: string };
        if (!payload.session_id) {
          throw new Error("Agent session response was incomplete.");
        }

        if (cancelled) {
          return;
        }

        setThreadId(payload.session_id);
        setStatus(`Connected ${payload.session_id.slice(0, 8)}`);
      } catch (error) {
        if (cancelled) {
          return;
        }

        setStatus(error instanceof Error ? error.message : "Unable to connect.");
      }
    }

    initialize();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="hound-shell">
      <section className="hound-frame">
        <header className="hound-header">
          <div className="ui-stable-fill">
            <p className="agent-kicker">Hound Forward</p>
            <h1 className="agent-title">Ask the agent</h1>
          </div>
          <div className="agent-status-card" aria-live="polite">
            <span className="agent-status-dot" />
            <p>{status}</p>
          </div>
        </header>

        <section className="hound-chat-card">
          {threadId ? (
            <CopilotKit runtimeUrl="/api/copilotkit" threadId={threadId} showDevConsole={false}>
              <CopilotChat
                className="hound-chat"
                labels={{
                  title: "Agent",
                  initial: "Ask a question.",
                }}
                suggestions={starterPrompts}
              />
            </CopilotKit>
          ) : (
            <section className="hound-loading-card">
              <p className="agent-kicker">Agent</p>
              <h2 className="agent-panel-title">Connecting</h2>
            </section>
          )}
        </section>
      </section>
    </main>
  );
}
