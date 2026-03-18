import { Shell } from "@/components/shell";
import { WorkspaceCardList } from "@/components/workspace-card";
import { metrics } from "@/lib/console-fixtures";

export default function MetricsPage() {
  return (
    <Shell eyebrow="Metric engine" title="Metrics">
      <WorkspaceCardList cards={metrics} />
    </Shell>
  );
}
