import { Shell } from "@/components/shell";

export default function AgentLabPage() {
  return (
    <Shell eyebrow="LangGraph" title="Agent Lab">
      <section className="grid gap-4 md:grid-cols-[1.2fr_0.8fr]">
        <article className="rounded-[1.5rem] border border-white/60 bg-white/80 p-6">
          <h2 className="mt-0 text-2xl">Research Loop</h2>
          <ol className="space-y-3 pl-5 text-sm text-slate-700">
            <li>Plan a manifest for a gait or emotion research goal.</li>
            <li>Create and enqueue a run via typed tools.</li>
            <li>Monitor completion and fetch structured metric results.</li>
            <li>Recommend the next metric or cohort experiment.</li>
          </ol>
        </article>
        <article className="rounded-[1.5rem] border border-white/60 bg-white/80 p-6">
          <h2 className="mt-0 text-2xl">Tool Boundary</h2>
          <p className="mb-0 text-sm text-slate-600">
            Agents do not touch the filesystem, database, or queue directly. All execution flows through the platform tools API.
          </p>
        </article>
      </section>
    </Shell>
  );
}
