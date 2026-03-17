import { ToolLibraryEntry } from "@/lib/view-library";
import { ViewLibraryCodeBlock, ViewLibraryMetaList, ViewLibrarySectionHeader, ViewLibraryTagList } from "./view-library-primitives";

export function ToolExampleRenderer({ entry }: { entry: ToolLibraryEntry }) {
  return (
    <div className="view-library-detail-stack">
      <ViewLibrarySectionHeader
        eyebrow="Agent Tool"
        title={entry.title}
        summary={entry.summary}
        action={<span className="module-pill">{entry.status}</span>}
      />

      <section className="agent-panel ui-ops-panel">
        <div className="view-library-overview">
          <div className="ui-stable-fill">
            <p className="agent-kicker">Category</p>
            <p className="view-library-value">{entry.category}</p>
          </div>
          <div className="ui-stable-fill">
            <p className="agent-kicker">Tags</p>
            <ViewLibraryTagList tags={entry.tags} />
          </div>
        </div>
      </section>

      <section className="agent-panel ui-ops-panel">
        <p className="agent-kicker">Contract</p>
        <ViewLibraryMetaList
          items={[
            { label: "Input kind", value: entry.contract.inputKind },
            { label: "Output kind", value: entry.contract.outputKind },
            { label: "Output artifact", value: entry.contract.outputArtifactName },
            { label: "Source", value: <code>{entry.contract.source}</code> },
          ]}
        />
      </section>

      <div className="view-library-code-grid">
        <ViewLibraryCodeBlock title="Example input" value={entry.contract.exampleInput} />
        <ViewLibraryCodeBlock title="Example output" value={entry.contract.exampleOutput} />
      </div>
    </div>
  );
}
