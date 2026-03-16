import { Shell } from "@/components/shell";
import { WorkspaceCardList } from "@/components/workspace-card";
import { runs } from "@/lib/console-fixtures";

export default function RunsPage() {
  return (
    <Shell eyebrow="Execution surface" title="Runs">
      <WorkspaceCardList cards={runs} />
    </Shell>
  );
}
