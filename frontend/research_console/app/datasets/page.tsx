import { Shell } from "@/components/shell";
import { WorkspaceCardList } from "@/components/workspace-card";
import { datasets } from "@/lib/console-fixtures";

export default function DatasetsPage() {
  return (
    <Shell eyebrow="Data engine" title="Datasets">
      <WorkspaceCardList cards={datasets} />
    </Shell>
  );
}
