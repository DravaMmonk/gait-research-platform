import { WorkspaceCard } from "@/lib/console-types";

export function WorkspaceCardList({ cards }: { cards: WorkspaceCard[] }) {
  return (
    <section className="ui-grid-cards">
      {cards.map((card) => (
        <article key={card.id} className="ui-panel">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="ui-eyebrow">{card.label}</p>
              <h2 className="ui-panel-title">{card.title}</h2>
            </div>
            <span className="ui-badge">{card.status}</span>
          </div>
          <p className="ui-copy mt-4">{card.description}</p>
          <dl className="mt-5 grid gap-3 sm:grid-cols-2">
            {card.metrics.map((metric) => (
              <div key={metric.label} className="ui-section">
                <dt className="ui-micro">{metric.label}</dt>
                <dd className="mt-2 text-lg font-semibold text-[var(--foreground)]">{metric.value}</dd>
              </div>
            ))}
          </dl>
        </article>
      ))}
    </section>
  );
}
