import { Shell } from "@/components/shell";

export default function DatasetsPage() {
  return (
    <Shell eyebrow="Data Engine" title="Datasets">
      <section className="rounded-[1.5rem] border border-white/60 bg-white/80 p-6">
        <h2 className="mt-0 text-2xl">Dataset Explorer</h2>
        <p className="mb-0 text-sm text-slate-600">
          This scaffold reserves space for cohort search, breed filters, session browsing, and clinician-tagged review sets.
        </p>
      </section>
    </Shell>
  );
}
