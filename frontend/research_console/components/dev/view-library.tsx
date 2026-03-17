"use client";

import { useDeferredValue, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Panel } from "@/components/ui/panel";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
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
    <div className="space-y-5">
      <ViewLibrarySectionHeader
        eyebrow="Visual Module"
        title={entry.title}
        summary={entry.summary}
        action={<Badge variant="outline">{entry.status}</Badge>}
      />

      <Panel tone="default" padding="roomy">
        <div className="grid gap-4 lg:grid-cols-2">
          <div>
            <p className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Category</p>
            <p className="mt-2 text-lg font-semibold tracking-[-0.02em] text-foreground">{entry.category}</p>
          </div>
          <div>
            <p className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Tags</p>
            <ViewLibraryTagList tags={entry.tags} />
          </div>
        </div>
      </Panel>

      <Panel tone="default" padding="roomy">
        <p className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Rendering contract</p>
        <ViewLibraryMetaList
          items={[
            { label: "Module type", value: entry.example.type },
            { label: "Default view mode", value: entry.defaultViewMode },
            { label: "Display title", value: entry.example.title },
          ]}
        />
      </Panel>

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
  const deferredQuery = useDeferredValue(query);

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
      return matchesCategory && matchesTag && matchesQuery(entry, deferredQuery);
    });
  }, [category, deferredQuery, entries, tag]);

  const resolvedSelectedId = filteredEntries.some((entry) => entry.id === selectedId) ? selectedId : (filteredEntries[0]?.id ?? "");
  const selectedEntry = filteredEntries.find((entry) => entry.id === resolvedSelectedId) ?? null;

  function handleSectionChange(nextSection: ViewLibrarySection) {
    setSection(nextSection);
    setQuery("");
    setCategory("all");
    setTag("all");
    setSelectedId("");
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,hsl(var(--primary)/0.08),transparent_24rem),linear-gradient(180deg,hsl(40_22%_98%)_0%,hsl(42_22%_95%)_48%,hsl(40_14%_92%)_100%)] px-4 py-6 sm:px-6">
      <section className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-[1400px] flex-col gap-5">
        <Panel tone="elevated" padding="roomy" className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0">
            <p className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Developer</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-foreground">View library</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">
              Internal reference for the shared visual module contracts and executor-backed agent tools.
            </p>
          </div>
          <Badge variant="default" className="w-fit rounded-full px-3 py-1 text-[0.68rem] tracking-[0.14em]">
            Hidden route
          </Badge>
        </Panel>

        <section className="grid min-h-0 flex-1 gap-5 lg:grid-cols-[22rem_minmax(0,1fr)]">
          <aside className="grid min-h-0 gap-5">
            <Panel tone="default" padding="roomy" className="space-y-5">
              <div className="grid gap-2">
                {viewLibrarySections.map((option) => (
                  <Button
                    key={option.id}
                    type="button"
                    variant={section === option.id ? "secondary" : "ghost"}
                    className="h-auto w-full justify-start rounded-[0.95rem] px-4 py-3 text-left"
                    onClick={() => handleSectionChange(option.id)}
                  >
                    <span className="flex flex-col items-start gap-1">
                      <span>{option.label}</span>
                      <small className="text-xs font-medium text-muted-foreground">{option.description}</small>
                    </span>
                  </Button>
                ))}
              </div>

              <Separator />

              <div className="grid gap-4">
                <label className="grid gap-2">
                  <span className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Search</span>
                  <Input
                    type="search"
                    placeholder="Search entries"
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                  />
                </label>

                <label className="grid gap-2">
                  <span className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Category</span>
                  <Select value={category} onValueChange={setCategory}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a category" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map((option) => (
                        <SelectItem key={option} value={option}>
                          {option === "all" ? "All categories" : option}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </label>

                <label className="grid gap-2">
                  <span className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Tag</span>
                  <Select value={tag} onValueChange={setTag}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a tag" />
                    </SelectTrigger>
                    <SelectContent>
                      {tags.map((option) => (
                        <SelectItem key={option} value={option}>
                          {option === "all" ? "All tags" : option}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </label>
              </div>
            </Panel>

            <Panel tone="default" padding="none" className="grid min-h-0 grid-rows-[auto_minmax(0,1fr)] overflow-hidden">
              <div className="flex items-center justify-between gap-3 border-b border-[hsl(var(--border)/0.68)] px-5 py-4">
                <p className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Entries</p>
                <Badge variant="muted">{filteredEntries.length}</Badge>
              </div>
              <ScrollArea className="min-h-0">
                <div className="grid gap-2 p-3">
                  {filteredEntries.length ? (
                    filteredEntries.map((entry) => (
                      <button
                        key={entry.id}
                        type="button"
                        className={
                          selectedEntry?.id === entry.id
                            ? "rounded-[calc(var(--radius)+1px)] border border-[hsl(var(--primary)/0.3)] bg-[linear-gradient(180deg,hsl(var(--card))_0%,hsl(var(--primary)/0.08)_100%)] px-4 py-3 text-left shadow-panel"
                            : "rounded-[calc(var(--radius)+1px)] border border-[hsl(var(--border)/0.68)] bg-[var(--panel-subtle)] px-4 py-3 text-left transition-colors hover:bg-accent hover:text-accent-foreground"
                        }
                        onClick={() => setSelectedId(entry.id)}
                      >
                        <div className="space-y-3">
                          <div>
                            <p className="text-sm font-semibold tracking-[-0.02em] text-foreground">{entry.title}</p>
                            <p className="mt-1 text-sm leading-6 text-muted-foreground">{entry.summary}</p>
                          </div>
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge variant="outline">{entry.category}</Badge>
                            <Badge variant="muted">{entry.status}</Badge>
                          </div>
                        </div>
                      </button>
                    ))
                  ) : (
                    <div className="px-4 py-5">
                      <p className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">No matches</p>
                      <p className="mt-2 text-sm leading-6 text-muted-foreground">Adjust the search, category, or tag filters.</p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </Panel>
          </aside>

          <section className="min-h-0">
            {selectedEntry ? (
              selectedEntry.kind === "module" ? (
                <ModuleExampleRenderer entry={selectedEntry} />
              ) : (
                <ToolExampleRenderer entry={selectedEntry} />
              )
            ) : (
              <Panel tone="default" padding="roomy">
                <p className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Empty library</p>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">No examples are available for the current section.</p>
              </Panel>
            )}
          </section>
        </section>
      </section>
    </main>
  );
}
