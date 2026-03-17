import { ReactNode } from "react";

export function ViewLibrarySectionHeader({
  eyebrow,
  title,
  summary,
  action,
}: {
  eyebrow: string;
  title: string;
  summary: string;
  action?: ReactNode;
}) {
  return (
    <header className="agent-panel view-library-detail-header">
      <div className="ui-stable-fill">
        <p className="agent-kicker">{eyebrow}</p>
        <h2 className="agent-panel-title">{title}</h2>
        <p className="module-copy view-library-summary">{summary}</p>
      </div>
      {action ? <div className="view-library-header-action">{action}</div> : null}
    </header>
  );
}

export function ViewLibraryTagList({ tags }: { tags: string[] }) {
  return (
    <div className="view-library-tag-list">
      {tags.map((tag) => (
        <span key={tag} className="module-pill">
          {tag}
        </span>
      ))}
    </div>
  );
}

export function ViewLibraryMetaList({ items }: { items: Array<{ label: string; value: ReactNode }> }) {
  return (
    <dl className="view-library-meta-list">
      {items.map((item) => (
        <div key={item.label} className="view-library-meta-item">
          <dt>{item.label}</dt>
          <dd>{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}

export function ViewLibraryCodeBlock({ title, value }: { title: string; value: unknown }) {
  return (
    <section className="agent-panel ui-stable-panel">
      <p className="agent-kicker">{title}</p>
      <pre className="module-code view-library-code">{JSON.stringify(value, null, 2)}</pre>
    </section>
  );
}
