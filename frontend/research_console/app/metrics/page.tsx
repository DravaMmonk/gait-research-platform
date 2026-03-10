import { Shell } from "@/components/shell";

const metrics = [
  { name: "gait_stability", version: "v1", value: 0.83 },
  { name: "asymmetry_index", version: "v1", value: 0.58 },
];

export default function MetricsPage() {
  return (
    <Shell eyebrow="Metric Engine" title="Metrics">
      <div className="grid gap-4 md:grid-cols-2">
        {metrics.map((metric) => (
          <article key={metric.name} className="rounded-[1.5rem] border border-white/60 bg-white/80 p-6">
            <p className="mb-2 text-xs uppercase tracking-[0.2em] text-slate-500">{metric.version}</p>
            <h2 className="m-0 text-2xl">{metric.name}</h2>
            <p className="mt-4 text-4xl font-semibold text-[var(--accent)]">{metric.value}</p>
          </article>
        ))}
      </div>
    </Shell>
  );
}
