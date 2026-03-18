import { Shell } from "@/components/shell";
import { WorkspaceCardList } from "@/components/workspace-card";
import { experiments } from "@/lib/console-fixtures";

export default function ExperimentsPage() {
  return (
    <Shell eyebrow="Research programs" title="Experiments">
      <WorkspaceCardList cards={experiments} />
    </Shell>
  );
}
