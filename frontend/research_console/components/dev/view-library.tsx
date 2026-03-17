"use client";

import { useEffect, useMemo, useState } from "react";
import { ModuleRenderer } from "@/components/console/module-renderer";
import { ToolExampleRenderer } from "@/components/dev/tool-example-renderer";
import {
  getViewLibraryEntries,
  ModuleLibraryEntry,
  ViewLibraryEntry,
  ViewLibrarySection,
  viewLibrarySections,
} from "@/lib/view-library";
import { ViewLibraryMetaList, ViewLibrarySectionHeader, ViewLibraryTagList } from "./view-library-primitives";

function normalizeValue(value: string) {
  return value.trim().toLowerCase();
}

function matchesQuery(entry: ViewLibraryEntry, query: string) {
  if (!query) {
    return true;
  }

  const haystack = [entry.title, entry.summary, entry.category, entry.status, ...entry.tags].join(" ").toLowerCase();
  return haystack.includes(query.toLowerCase());
}

function ModuleExampleRenderer({ entry }: { entry: ModuleLibraryEntry }) {
  return (
    <div className="view-library-detail-stack">
      <ViewLibrarySectionHeader
        eyebrow="Visual Module"
        title={entry.title}
        summary={entry.summary}
        action={<span className="module-pill">{entry.status}</span>}
      />

      <section className="agent-panel">
        <div className="view-library-overview">
          <div className="ui-stable-fill">
            <p className="agent-kicker">Category</p>
            <p className="view-library-value">{entry.category}</p>
          </div>
          <div className="ui-stable-fill">
            <p className="agent-kicker">Tags</p>
            <ViewLibraryTagList tags={entry.tags} />
          </div>
        </div>
      </section>

      <section className="agent-panel">
        <p className="agent-kicker">Rendering contract</p>
        <ViewLibraryMetaList
          items={[
            { label: "Module type", value: entry.example.type },
            { label: "Default view mode", value: entry.defaultViewMode },
            { label: "Display title", value: entry.example.title },
          ]}
        />
      </section>

      <ModuleRenderer module={entry.example} />
    </div>
  );
}

export function DevViewLibrary() {
  const [section, setSection] = useState<ViewLibrarySection>("modules");
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");
  const [tag, setTag] = useState("all");
  const [selectedId, setSelectedId] = useState("");

  const entries = useMemo(() => getViewLibraryEntries(section), [section]);

  const categories = useMemo(() => {
    return ["all", ...new Set(entries.map((entry) => entry.category))];
  }, [entries]);

  const tags = useMemo(() => {
    return ["all", ...new Set(entries.flatMap((entry) => entry.tags))];
  }, [entries]);

  const filteredEntries = useMemo(() => {
    return entries.filter((entry) => {
      const matchesCategory = category === "all" || normalizeValue(entry.category) === normalizeValue(category);
      const matchesTag = tag === "all" || entry.tags.some((entryTag) => normalizeValue(entryTag) === normalizeValue(tag));
      return matchesCategory && matchesTag && matchesQuery(entry, query);
    });
  }, [category, entries, query, tag]);

  const selectedEntry = filteredEntries.find((entry) => entry.id === selectedId) ?? filteredEntries[0] ?? null;

  useEffect(() => {
    setCategory("all");
    setTag("all");
    setQuery("");
  }, [section]);

  useEffect(() => {
    if (!filteredEntries.length) {
      setSelectedId("");
      return;
    }

    if (!filteredEntries.some((entry) => entry.id === selectedId)) {
      setSelectedId(filteredEntries[0].id);
    }
  }, [filteredEntries, selectedId]);

  return (
    <main className="agent-shell">
      <section className="agent-frame view-library-frame">
        <header className="agent-header">
          <div className="ui-stable-fill">
            <p className="agent-kicker">Developer</p>
            <h1 className="agent-title">View library</h1>
            <p className="agent-subtitle view-library-page-copy">
              Internal reference for the controlled frontend modules and executor-backed tool contracts.
            </p>
          </div>
          <div className="agent-status-card">
            <span className="agent-status-dot" />
            <p>Hidden route</p>
          </div>
        </header>

        <section className="view-library-layout">
          <aside className="view-library-sidebar">
            <section className="agent-panel view-library-sidebar-panel">
              <div className="view-library-segmented">
                {viewLibrarySections.map((option) => (
                  <button
                    key={option.id}
                    type="button"
                    className={section === option.id ? "view-library-segment view-library-segment-active" : "view-library-segment"}
                    onClick={() => setSection(option.id)}
                  >
                    <span>{option.label}</span>
                    <small>{option.description}</small>
                  </button>
                ))}
              </div>

              <div className="view-library-filter-stack">
                <label className="view-library-field">
                  <span className="agent-kicker">Search</span>
                  <input
                    className="view-library-input"
                    type="search"
                    placeholder="Search entries"
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                  />
                </label>

                <label className="view-library-field">
                  <span className="agent-kicker">Category</span>
                  <select className="view-library-select" value={category} onChange={(event) => setCategory(event.target.value)}>
                    {categories.map((option) => (
                      <option key={option} value={option}>
                        {option === "all" ? "All categories" : option}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="view-library-field">
                  <span className="agent-kicker">Tag</span>
                  <select className="view-library-select" value={tag} onChange={(event) => setTag(event.target.value)}>
                    {tags.map((option) => (
                      <option key={option} value={option}>
                        {option === "all" ? "All tags" : option}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            </section>

            <section className="agent-panel view-library-sidebar-panel view-library-list-panel">
              <div className="view-library-list">
                {filteredEntries.length ? (
                  filteredEntries.map((entry) => (
                    <button
                      key={entry.id}
                      type="button"
                      className={selectedEntry?.id === entry.id ? "view-library-list-item view-library-list-item-active" : "view-library-list-item"}
                      onClick={() => setSelectedId(entry.id)}
                    >
                      <div className="view-library-list-copy">
                        <p className="view-library-list-title">{entry.title}</p>
                        <p className="view-library-list-summary">{entry.summary}</p>
                      </div>
                      <div className="view-library-list-meta">
                        <span className="module-pill">{entry.category}</span>
                        <span className="view-library-list-status">{entry.status}</span>
                      </div>
                    </button>
                  ))
                ) : (
                  <div className="agent-empty">
                    <p className="agent-kicker">No matches</p>
                    <p className="module-copy">Adjust the search, category, or tag filters.</p>
                  </div>
                )}
              </div>
            </section>
          </aside>

          <section className="view-library-detail">
            {selectedEntry ? (
              selectedEntry.kind === "module" ? (
                <ModuleExampleRenderer entry={selectedEntry} />
              ) : (
                <ToolExampleRenderer entry={selectedEntry} />
              )
            ) : (
              <div className="agent-empty">
                <p className="agent-kicker">Empty library</p>
                <p className="module-copy">No examples are available for the current section.</p>
              </div>
            )}
          </section>
        </section>
      </section>
    </main>
  );
}
