"use client";

import dynamic from "next/dynamic";

const CopilotAgentConsole = dynamic(
  () => import("@/components/console/copilot-agent-console").then((mod) => mod.CopilotAgentConsole),
  {
    ssr: false,
    loading: () => (
      <main className="hound-shell">
        <section className="hound-frame">
          <section className="hound-chat-card">
            <section className="hound-loading-card">
              <p className="agent-kicker">Agent</p>
              <h2 className="agent-panel-title">Loading console</h2>
            </section>
          </section>
        </section>
      </main>
    ),
  },
);

export function HomeConsoleShell() {
  return <CopilotAgentConsole />;
}
