import { Shell } from "@/components/shell";

export default function AgentLabPage() {
  return (
    <Shell eyebrow="LangGraph" title="Agent Lab">
      <section className="grid gap-4 md:grid-cols-[1.2fr_0.8fr]">
        <article className="rounded-[1.5rem] border border-white/60 bg-white/80 p-6">
          <h2 className="mt-0 text-2xl">Research Loop</h2>
          <p className="rounded-full bg-[var(--accent-soft)] px-3 py-1 text-xs uppercase tracking-[0.2em] text-[var(--accent)] inline-block">
            Runtime Validation Mode
          </p>
          <ol className="space-y-3 pl-5 text-sm text-slate-700">
            <li>Plan a manifest for one uploaded video asset.</li>
            <li>Create and enqueue a run via typed tools.</li>
            <li>Wait for the placeholder local worker bridge to complete the dummy pipeline.</li>
            <li>Read fake metrics and recommend the next runtime validation step.</li>
          </ol>
        </article>
        <article className="rounded-[1.5rem] border border-white/60 bg-white/80 p-6">
          <h2 className="mt-0 text-2xl">Tool Boundary</h2>
          <p className="mb-0 text-sm text-slate-600">
            Agents do not touch the filesystem, database, or queue directly. All execution flows through the platform tools API, and all current outputs are explicitly dummy, fake, or placeholder.
          </p>
        </article>
      </section>
    </Shell>
  );
}
