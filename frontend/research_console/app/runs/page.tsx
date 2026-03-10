import { Shell } from "@/components/shell";
import { runCards } from "@/lib/mock-data";

export default function RunsPage() {
  return (
    <Shell eyebrow="Execution" title="Runs">
      <div className="rounded-[1.5rem] border border-white/60 bg-white/80 p-6">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-slate-500">
              <th className="pb-3">Run ID</th>
              <th className="pb-3">Status</th>
              <th className="pb-3">Focus</th>
            </tr>
          </thead>
          <tbody>
            {runCards.map((run) => (
              <tr key={run.id} className="border-t border-slate-200/70">
                <td className="py-3 font-medium">{run.id}</td>
                <td className="py-3">{run.status}</td>
                <td className="py-3">{run.focus}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Shell>
  );
}
