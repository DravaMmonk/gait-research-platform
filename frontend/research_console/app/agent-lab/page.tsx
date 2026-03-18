import { ResearchConsole } from "@/components/console/research-console";
import { Shell } from "@/components/shell";

export default function AgentLabPage() {
  return (
    <Shell
      eyebrow="Agent-first workspace"
      title="Research Console"
      description="Natural-language entry, controlled modules, and traceable evidence are combined into one operational research surface."
    >
      <ResearchConsole />
    </Shell>
  );
}
