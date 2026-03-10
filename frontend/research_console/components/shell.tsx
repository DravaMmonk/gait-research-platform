import Link from "next/link";
import { ReactNode } from "react";

const navigation = [
  { href: "/experiments", label: "Experiments" },
  { href: "/runs", label: "Runs" },
  { href: "/metrics", label: "Metrics" },
  { href: "/datasets", label: "Datasets" },
  { href: "/agent-lab", label: "Agent Lab" },
];

export function Shell({ title, eyebrow, children }: { title: string; eyebrow: string; children: ReactNode }) {
  return (
    <main className="min-h-screen px-6 py-8 md:px-12">
      <div className="mx-auto max-w-6xl">
        <header className="mb-8 rounded-[2rem] border border-white/50 bg-[var(--card)] p-6 backdrop-blur">
          <p className="mb-2 text-xs uppercase tracking-[0.3em] text-slate-500">{eyebrow}</p>
          <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
            <div>
              <h1 className="m-0 text-4xl font-semibold">{title}</h1>
              <p className="mb-0 mt-3 max-w-2xl text-sm text-slate-600">
                Azure-aligned research platform scaffold for canine movement experiments, metrics, and agent-led iteration.
              </p>
            </div>
            <nav className="flex flex-wrap gap-2">
              {navigation.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="rounded-full border border-slate-300/70 px-4 py-2 text-sm transition hover:border-[var(--accent)] hover:bg-[var(--accent-soft)]"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        {children}
      </div>
    </main>
  );
}
