"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";

const navigation = [
  { href: "/agent-lab", label: "Research Console" },
  { href: "/experiments", label: "Experiments" },
  { href: "/runs", label: "Runs" },
  { href: "/metrics", label: "Metrics" },
  { href: "/datasets", label: "Datasets" },
];

function Navigation() {
  const pathname = usePathname();

  return (
    <aside className="ui-sidebar">
      <div>
        <p className="ui-eyebrow">Hound Forward</p>
        <h1 className="text-2xl font-semibold tracking-tight text-white">Research Console</h1>
        <p className="mt-3 text-sm leading-6 text-slate-300">
          Chat-first orchestration with controlled visual modules, runtime tools, and evidence-aware review.
        </p>
      </div>

      <nav className="mt-8 space-y-2">
        {navigation.map((item) => (
          <Link key={item.href} href={item.href} className={pathname === item.href ? "ui-sidebar-link ui-sidebar-link-active" : "ui-sidebar-link"}>
            {item.label}
          </Link>
        ))}
      </nav>

      <div className="mt-auto rounded-[1.25rem] border border-white/10 bg-white/5 p-4">
        <p className="ui-micro text-slate-300">Mode</p>
        <p className="mt-2 text-sm text-white">Placeholder-aware research workspace</p>
      </div>
    </aside>
  );
}

export function Shell({
  title,
  eyebrow,
  description,
  children,
}: {
  title: string;
  eyebrow: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <main className="min-h-screen bg-[var(--background)] px-4 py-4 md:px-6">
      <div className="mx-auto grid max-w-[1600px] gap-4 lg:grid-cols-[18rem_minmax(0,1fr)]">
        <Navigation />
        <div className="min-w-0">
          <header className="ui-topbar">
            <div>
              <p className="ui-eyebrow">{eyebrow}</p>
              <h1 className="ui-page-title">{title}</h1>
            </div>
            <div className="max-w-2xl">
              <p className="ui-copy">
                {description ??
                  "Agent-centric orchestration with predefined visual modules, evidence-aware rendering, and stable operational surfaces."}
              </p>
            </div>
          </header>
          <div className="mt-4 min-w-0">{children}</div>
        </div>
      </div>
    </main>
  );
}
