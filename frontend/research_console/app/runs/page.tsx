import { Shell } from "@/components/shell";
import { runCards, runDetail, uploadedVideos } from "@/lib/mock-data";

export default function RunsPage() {
  return (
    <Shell eyebrow="Execution" title="Runs">
      <section className="grid gap-4 md:grid-cols-[0.95fr_1.05fr]">
        <article className="rounded-[1.5rem] border border-white/60 bg-white/80 p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="m-0 text-2xl">Run Explorer</h2>
            <span className="rounded-full bg-[var(--accent-soft)] px-3 py-1 text-xs uppercase tracking-[0.2em] text-[var(--accent)]">
              Placeholder UI
            </span>
          </div>
          <div className="mb-6 rounded-2xl border border-dashed border-slate-300 px-4 py-5 text-sm text-slate-600">
            Upload video
            <div className="mt-2 text-xs text-slate-500">Runtime validation mode: upload, create one run, inspect fake outputs.</div>
          </div>
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
        </article>
        <article className="rounded-[1.5rem] border border-white/60 bg-white/80 p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="m-0 text-2xl">Run Detail</h2>
            <span className="rounded-full border border-slate-300 px-3 py-1 text-xs uppercase tracking-[0.2em] text-slate-500">
              Dummy / Fake / Placeholder
            </span>
          </div>
          <p className="mt-0 text-sm text-slate-600">Input video asset: {runDetail.inputVideo}</p>
          <div className="mb-5 flex flex-wrap gap-2">
            {uploadedVideos.map((video) => (
              <span key={video.id} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600">
                {video.name} · {video.label}
              </span>
            ))}
          </div>
          <div className="mb-5">
            <h3 className="mb-2 mt-0 text-sm uppercase tracking-[0.2em] text-slate-500">Outputs</h3>
            <ul className="m-0 space-y-2 p-0 text-sm text-slate-700">
              {runDetail.assets.map((asset) => (
                <li key={asset} className="list-none rounded-xl bg-slate-50 px-3 py-2">
                  {asset}
                </li>
              ))}
            </ul>
          </div>
          <div className="mb-5">
            <h3 className="mb-2 mt-0 text-sm uppercase tracking-[0.2em] text-slate-500">Fake Metrics</h3>
            <ul className="m-0 space-y-2 p-0 text-sm text-slate-700">
              {runDetail.metrics.map((metric) => (
                <li key={metric.name} className="list-none rounded-xl bg-slate-50 px-3 py-2">
                  {metric.name}: {metric.value}
                </li>
              ))}
            </ul>
          </div>
          <p className="mb-0 text-sm text-slate-600">{runDetail.recommendation}</p>
        </article>
      </section>
    </Shell>
  );
}
