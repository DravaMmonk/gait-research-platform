import { WorkspaceCardItem } from "@/components/workspace-card";

export const datasets: WorkspaceCardItem[] = [
  {
    id: "dataset-session-baseline",
    eyebrow: "Dataset registry",
    title: "Session baseline cohort",
    summary: "Normalized intake dataset used for early stride and mobility comparisons across repeat sessions.",
    status: "stable",
    metrics: [
      { label: "Dogs", value: "28" },
      { label: "Sessions", value: "164" },
      { label: "Coverage", value: "92%" },
    ],
  },
  {
    id: "dataset-video-index",
    eyebrow: "Evidence corpus",
    title: "Video evidence index",
    summary: "Catalog of timestamped video clips aligned to runs, reports, and evidence references.",
    status: "core",
    metrics: [
      { label: "Assets", value: "413" },
      { label: "Tagged", value: "388" },
      { label: "Linked runs", value: "121" },
    ],
  },
];

export const experiments: WorkspaceCardItem[] = [
  {
    id: "experiment-mobility-v2",
    eyebrow: "Experiment lane",
    title: "Mobility index v2 rollout",
    summary: "Controlled program validating formula revisions against review-backed session evidence and historical drift.",
    status: "active",
    metrics: [
      { label: "Runs", value: "36" },
      { label: "Pass rate", value: "81%" },
      { label: "Reviewer notes", value: "14" },
    ],
  },
  {
    id: "experiment-video-triage",
    eyebrow: "Operator review",
    title: "Video triage workflow",
    summary: "Pilot workflow for surfacing abnormal clips into the evidence-first review queue.",
    status: "preview",
    metrics: [
      { label: "Queued clips", value: "52" },
      { label: "Reviewed", value: "31" },
      { label: "Escalations", value: "6" },
    ],
  },
];

export const metrics: WorkspaceCardItem[] = [
  {
    id: "metric-mobility",
    eyebrow: "Derived metric",
    title: "mobility_index_v2",
    summary: "Primary locomotion score derived from stride-length normalization and asymmetry drift signals.",
    status: "reviewed",
    metrics: [
      { label: "Formula", value: "v2" },
      { label: "Confidence", value: "Moderate" },
      { label: "Alerts", value: "3" },
    ],
  },
  {
    id: "metric-asymmetry",
    eyebrow: "Reference metric",
    title: "asymmetry_index",
    summary: "Support metric used to anchor evidence panels and video review windows during session comparisons.",
    status: "stable",
    metrics: [
      { label: "Signals", value: "4" },
      { label: "Variance", value: "0.07" },
      { label: "Missingness", value: "Low" },
    ],
  },
];

export const runs: WorkspaceCardItem[] = [
  {
    id: "run-queue-health",
    eyebrow: "Execution queue",
    title: "Queued research runs",
    summary: "Operational view over staged runs waiting for decode, pose extraction, and metric evaluation.",
    status: "healthy",
    metrics: [
      { label: "Queued", value: "9" },
      { label: "Running", value: "4" },
      { label: "Blocked", value: "1" },
    ],
  },
  {
    id: "run-reporting",
    eyebrow: "Report generation",
    title: "Recent analytical outputs",
    summary: "Latest completed runs with evidence-ready reports linked back to sessions and assets.",
    status: "core",
    metrics: [
      { label: "Completed", value: "48" },
      { label: "Reports", value: "48" },
      { label: "Failures", value: "0" },
    ],
  },
];
