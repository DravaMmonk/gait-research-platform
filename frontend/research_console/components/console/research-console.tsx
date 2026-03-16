"use client";

import { startTransition, useState } from "react";

import { ModuleRenderer } from "@/components/console/module-renderer";
import { requestConsoleResponse } from "@/lib/console-client";
import { defaultConsoleResponse, defaultSessionId } from "@/lib/console-fixtures";
import { ConsoleAgentResponse, ConsoleViewMode, DisplayPreference, VisualModule } from "@/lib/console-types";

const allModes: ConsoleViewMode[] = ["summary", "chart", "table", "evidence", "video", "formula"];

function inferDisplayPreferences(message: string): DisplayPreference[] {
  const lowered = message.toLowerCase();
  const preferences: DisplayPreference[] = [];
  if (lowered.includes("table only") || lowered.includes("show as table")) {
    preferences.push("table_only");
  }
  if (lowered.includes("chart") || lowered.includes("plot")) {
    preferences.push("prefer_chart");
  }
  if (lowered.includes("video")) {
    preferences.push("prefer_video");
  }
  if (lowered.includes("raw values") || lowered.includes("show raw")) {
    preferences.push("raw_values_only");
  }
  if (lowered.includes("evidence")) {
    preferences.push("evidence_first");
  }
  return preferences;
}

function filterModules(modules: VisualModule[], mode: ConsoleViewMode): VisualModule[] {
  if (mode === "summary") {
    return modules.filter((module) => module.view_mode === "summary");
  }
  return modules.filter((module) => module.view_mode === mode);
}

export function ResearchConsole() {
  const [composer, setComposer] = useState(defaultConsoleResponse.thread[0]?.content ?? "");
  const [response, setResponse] = useState<ConsoleAgentResponse>(defaultConsoleResponse);
  const [activeMode, setActiveMode] = useState<ConsoleViewMode>(response.view_modes[0] ?? "summary");
  const [isPending, setIsPending] = useState(false);

  async function submitPrompt() {
    const nextMessage = composer.trim();
    if (!nextMessage) {
      return;
    }
    setIsPending(true);
    const nextResponse = await requestConsoleResponse({
      session_id: defaultSessionId,
      message: nextMessage,
      display_preferences: inferDisplayPreferences(nextMessage),
    });
    startTransition(() => {
      setResponse(nextResponse);
      setActiveMode(nextResponse.view_modes[0] ?? "summary");
      setIsPending(false);
    });
  }

  const visibleModules = filterModules(response.modules, activeMode);

  return (
    <div className="grid min-h-[calc(100vh-8rem)] gap-5 lg:grid-cols-[minmax(0,1.6fr)_22rem]">
      <section className="ui-panel flex min-h-0 flex-col">
        <div className="border-b border-[var(--border)] pb-5">
          <p className="ui-eyebrow">Research Console</p>
          <h2 className="ui-page-title">Chat-first research workspace</h2>
          <p className="ui-copy mt-3 max-w-3xl">
            The agent is the main entry point. It interprets user intent, selects controlled visual modules, and keeps evidence attached to every result.
          </p>
        </div>

        <div className="ui-scroll-y mt-5 flex-1 space-y-4 pr-2">
          {response.thread.map((item, index) => (
            <article key={`${item.role}-${index}-${item.created_at}`} className={item.role === "user" ? "ui-chat-user" : "ui-chat-assistant"}>
              <p className="ui-micro">{item.role}</p>
              <p className="mt-2 whitespace-pre-wrap text-sm leading-6">{item.content}</p>
            </article>
          ))}

          <article className="ui-section">
            <p className="ui-micro">Structured response</p>
            <p className="mt-2 text-sm leading-6">{response.message}</p>
          </article>

          <div className="flex flex-wrap gap-2">
            {(response.view_modes.length ? response.view_modes : allModes).map((mode) => (
              <button key={mode} type="button" className={mode === activeMode ? "ui-tab ui-tab-active" : "ui-tab"} onClick={() => setActiveMode(mode)}>
                {mode}
              </button>
            ))}
          </div>

          <div className="space-y-4">
            {visibleModules.map((module, index) => (
              <ModuleRenderer key={`${module.type}-${index}-${module.title}`} module={module} />
            ))}
          </div>
        </div>

        <div className="mt-5 border-t border-[var(--border)] pt-5">
          <div className="rounded-[1.4rem] border border-[var(--border-strong)] bg-[var(--muted)] p-4">
            <label htmlFor="console-composer" className="ui-micro">
              Prompt
            </label>
            <textarea
              id="console-composer"
              value={composer}
              onChange={(event) => setComposer(event.target.value)}
              className="mt-3 h-28 w-full resize-none border-0 bg-transparent text-sm leading-6 text-[var(--foreground)] outline-none"
              placeholder="Ask for a trend, table, evidence view, or supporting video."
            />
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap gap-2">
                {["Summary", "Chart", "Table", "Evidence", "Video", "Formula"].map((item) => (
                  <span key={item} className="ui-badge">
                    {item}
                  </span>
                ))}
              </div>
              <button type="button" className="ui-primary-button" onClick={submitPrompt} disabled={isPending}>
                {isPending ? "Assembling..." : "Send to agent"}
              </button>
            </div>
          </div>
        </div>
      </section>

      <aside className="space-y-5">
        <section className="ui-panel">
          <p className="ui-eyebrow">Evidence context</p>
          <h3 className="ui-panel-title">{response.evidence_context.metric_definition}</h3>
          <dl className="mt-5 space-y-4">
            <div>
              <dt className="ui-micro">Time range</dt>
              <dd className="ui-copy mt-2">{response.evidence_context.time_range}</dd>
            </div>
            <div>
              <dt className="ui-micro">Data quality</dt>
              <dd className="ui-copy mt-2">{response.evidence_context.data_quality}</dd>
            </div>
            <div>
              <dt className="ui-micro">Review status</dt>
              <dd className="ui-copy mt-2">{response.evidence_context.clinician_reviewed ? "Clinician reviewed" : "Not yet reviewed"}</dd>
            </div>
            <div>
              <dt className="ui-micro">Metric type</dt>
              <dd className="ui-copy mt-2">{response.evidence_context.derived_metric ? "Derived" : "Raw"}</dd>
            </div>
          </dl>
          <ul className="mt-5 space-y-2">
            {response.evidence_context.references.map((reference) => (
              <li key={reference} className="ui-section text-sm">
                {reference}
              </li>
            ))}
          </ul>
        </section>

        <section className="ui-panel">
          <p className="ui-eyebrow">Tool trace</p>
          <div className="mt-5 space-y-3">
            {response.tool_trace.map((trace) => (
              <article key={trace.tool_name} className="ui-section">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold">{trace.tool_name}</p>
                    <p className="ui-copy mt-2">{trace.purpose}</p>
                  </div>
                  <span className="ui-badge">{trace.status}</span>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="ui-panel">
          <p className="ui-eyebrow">Suggested follow-ups</p>
          <ul className="mt-5 space-y-2">
            {response.suggested_followups.map((item) => (
              <li key={item} className="ui-section text-sm">
                {item}
              </li>
            ))}
          </ul>
        </section>
      </aside>
    </div>
  );
}
