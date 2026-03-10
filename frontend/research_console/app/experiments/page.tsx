import { Shell } from "@/components/shell";
import { runCards } from "@/lib/mock-data";

export default function ExperimentsPage() {
  return (
    <Shell eyebrow="Research Console" title="Experiments">
      <section className="grid gap-4 md:grid-cols-3">
        {runCards.map((run) => (
          <article key={run.id} className="rounded-[1.5rem] border border-white/60 bg-white/80 p-5 shadow-sm">
            <p className="mb-2 text-xs uppercase tracking-[0.2em] text-slate-500">{run.status}</p>
            <h2 className="m-0 text-xl">{run.focus}</h2>
            <p className="mt-4 text-sm text-slate-600">Current research score: {run.metric}</p>
          </article>
        ))}
      </section>
    </Shell>
  );
}
