import { Badge } from "@/components/ui/badge";
import { Panel } from "@/components/ui/panel";
import { ToolLibraryEntry } from "@/lib/view-library";
import { ViewLibraryCodeBlock, ViewLibraryMetaList, ViewLibrarySectionHeader, ViewLibraryTagList } from "./view-library-primitives";

export function ToolExampleRenderer({ entry }: { entry: ToolLibraryEntry }) {
  return (
    <div className="space-y-5">
      <ViewLibrarySectionHeader
        eyebrow="Agent Tool"
        title={entry.title}
        summary={entry.summary}
        action={<Badge variant="outline">{entry.status}</Badge>}
      />

      <Panel tone="default" padding="roomy">
        <div className="grid gap-4 lg:grid-cols-2">
          <div>
            <p className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Category</p>
            <p className="mt-2 text-lg font-semibold tracking-[-0.02em] text-foreground">{entry.category}</p>
          </div>
          <div>
            <p className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Tags</p>
            <ViewLibraryTagList tags={entry.tags} />
          </div>
        </div>
      </Panel>

      <Panel tone="default" padding="roomy">
        <p className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Contract</p>
        <ViewLibraryMetaList
          items={[
            { label: "Input kind", value: entry.contract.inputKind },
            { label: "Output kind", value: entry.contract.outputKind },
            { label: "Output artifact", value: entry.contract.outputArtifactName },
            { label: "Source", value: <code>{entry.contract.source}</code> },
          ]}
        />
      </Panel>

      <div className="grid gap-5 xl:grid-cols-2">
        <ViewLibraryCodeBlock title="Example input" value={entry.contract.exampleInput} />
        <ViewLibraryCodeBlock title="Example output" value={entry.contract.exampleOutput} />
      </div>
    </div>
  );
}
