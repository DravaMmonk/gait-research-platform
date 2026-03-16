import { ConsoleAgentResponse, WorkspaceCard } from "@/lib/console-types";

export const defaultSessionId = "session-console-001";

export const defaultConsoleResponse: ConsoleAgentResponse = {
  thread: [
    {
      role: "user",
      content: "Compare this dog's mobility over the last 6 months and show why March looks abnormal.",
      created_at: "2026-03-16T10:30:00Z",
    },
    {
      role: "assistant",
      content: "The console assembled a comparison-focused response using controlled cards, trend evidence, and a supporting metric table.",
      created_at: "2026-03-16T10:30:01Z",
    },
  ],
  message:
    "Mobility drops sharply in March, and the strongest supporting signal is a simultaneous rise in asymmetry. The evidence remains clinically reviewable because the formula and source sessions are attached below.",
  modules: [
    {
      type: "summary_card",
      title: "Research Summary",
      view_mode: "summary",
      payload: {
        title: "Mobility trend review",
        summary: "March shows the steepest month-level deterioration, aligned with reduced stride symmetry and weaker metadata completeness.",
        status: "attention_needed",
        highlights: [
          { label: "Primary metric", value: "mobility_index_v2" },
          { label: "Abnormal window", value: "March" },
          { label: "Clinical status", value: "reviewed" },
        ],
      },
    },
    {
      type: "comparison_cards",
      title: "Comparison Cards",
      view_mode: "summary",
      payload: {
        title: "Month-over-month comparison",
        items: [
          { label: "March vs February", value: "-0.19", delta: "-24%" },
          { label: "March asymmetry", value: "0.18", delta: "+0.07" },
        ],
      },
    },
    {
      type: "trend_chart",
      title: "Trend Chart",
      view_mode: "chart",
      payload: {
        metric: "mobility_index_v2",
        unit: "score",
        time_range: "6 months",
        x_axis: "Month",
        y_axis: "Mobility score",
        series: [
          { label: "Jan", value: 0.82 },
          { label: "Feb", value: 0.8 },
          { label: "Mar", value: 0.61 },
          { label: "Apr", value: 0.66 },
          { label: "May", value: 0.71 },
          { label: "Jun", value: 0.74 },
        ],
      },
    },
    {
      type: "metric_table",
      title: "Metric Table",
      view_mode: "table",
      payload: {
        metric: "mobility_index_v2",
        columns: [
          { key: "month", label: "Month" },
          { key: "value", label: "Value" },
          { key: "quality", label: "Quality" },
        ],
        rows: [
          { values: { month: "Jan", value: 0.82, quality: "complete" }, raw: false, derived: true },
          { values: { month: "Feb", value: 0.8, quality: "complete" }, raw: false, derived: true },
          { values: { month: "Mar", value: 0.61, quality: "missing metadata" }, raw: false, derived: true },
        ],
        sort: "month.asc",
      },
    },
    {
      type: "evidence_panel",
      title: "Evidence Panel",
      view_mode: "evidence",
      payload: {
        confidence: "moderate",
        review_status: "clinician_reviewed",
        missingness: "2 of 14 sessions contain incomplete metadata.",
        provenance: "Derived from stride_length / body_length with supporting asymmetry drift during March.",
        sources: [
          { label: "Run", kind: "run", reference: "run-001" },
          { label: "Formula", kind: "formula", reference: "mobility_index_v2" },
          { label: "Video", kind: "video", reference: "video-001" },
        ],
      },
    },
    {
      type: "video_panel",
      title: "Video Review",
      view_mode: "video",
      payload: {
        asset_id: "video-001",
        title: "March gait review clip",
        timestamp_range: "00:12-00:26",
        related_metrics: ["mobility_index_v2", "asymmetry_index"],
      },
    },
    {
      type: "formula_explanation_card",
      title: "Formula Explanation",
      view_mode: "formula",
      payload: {
        formula_id: "mobility_index_v2",
        expression: "stride_length / body_length",
        interpretation:
          "Normalizing stride length by body size enables locomotion efficiency comparison across dogs with different morphology.",
        assumptions: [
          "Body length normalization remains stable across the observation window.",
          "Stride extraction quality is sufficient for month-level comparison.",
        ],
      },
    },
  ],
  view_modes: ["summary", "chart", "table", "evidence", "video", "formula"],
  tool_trace: [
    {
      tool_name: "intent_parser",
      purpose: "Normalize user goal and display intent into console semantics.",
      status: "ok",
      details: { intent: "compare_mobility" },
    },
    {
      tool_name: "read_metrics",
      purpose: "Retrieve metric evidence for the selected session context.",
      status: "ok",
      details: { metric: "mobility_index_v2", time_range: "6 months" },
    },
    {
      tool_name: "render_modules",
      purpose: "Select controlled visual modules for frontend rendering.",
      status: "ok",
      details: { module_types: ["summary_card", "trend_chart", "metric_table", "evidence_panel"] },
    },
  ],
  evidence_context: {
    metric_definition: "mobility_index_v2",
    time_range: "Last 6 months",
    data_quality: "2 sessions contain incomplete metadata; trend review remains valid.",
    clinician_reviewed: true,
    derived_metric: true,
    references: ["run-001", "formula:mobility_index_v2", "video:video-001"],
  },
  warnings: [],
  suggested_followups: [
    "Show this as a table only.",
    "Open the supporting video and evidence trail.",
    "Compare this against the clinician validation cohort.",
  ],
};

export const experiments: WorkspaceCard[] = [
  {
    id: "exp-001",
    label: "Research track",
    title: "Mobility biomarker discovery",
    status: "active",
    description: "Symbolic regression and cohort review for interpretable mobility indicators.",
    metrics: [
      { label: "Open runs", value: "12" },
      { label: "Validated formulas", value: "3" },
    ],
  },
  {
    id: "exp-002",
    label: "Validation track",
    title: "Clinician review cohort",
    status: "review",
    description: "Evidence-first validation against clinician-tagged discomfort sessions.",
    metrics: [
      { label: "Reviewed sessions", value: "28" },
      { label: "Flags", value: "4" },
    ],
  },
];

export const runs: WorkspaceCard[] = [
  {
    id: "run-001",
    label: "Completed",
    title: "French bulldog gait baseline",
    status: "completed",
    description: "Dummy runtime validation result with metrics, report, and evidence bundle.",
    metrics: [
      { label: "Stride length", value: "0.83" },
      { label: "Asymmetry", value: "0.12" },
    ],
  },
  {
    id: "run-002",
    label: "Queued",
    title: "Mobility trend refresh",
    status: "queued",
    description: "Awaiting local worker bridge execution with the current manifest contract.",
    metrics: [
      { label: "Inputs", value: "1 video" },
      { label: "Runner", value: "local" },
    ],
  },
];

export const metrics: WorkspaceCard[] = [
  {
    id: "metric-001",
    label: "Derived metric",
    title: "mobility_index_v2",
    status: "reviewed",
    description: "Normalized stride metric used for time-series interpretation and comparison.",
    metrics: [
      { label: "Definition", value: "stride_length / body_length" },
      { label: "Confidence", value: "moderate" },
    ],
  },
  {
    id: "metric-002",
    label: "Signal metric",
    title: "asymmetry_index",
    status: "stable",
    description: "Primary supporting signal for March abnormality detection.",
    metrics: [
      { label: "Version", value: "v1" },
      { label: "Coverage", value: "14 sessions" },
    ],
  },
];

export const datasets: WorkspaceCard[] = [
  {
    id: "dataset-001",
    label: "Ready",
    title: "Orthopedic screening cohort",
    status: "ready",
    description: "Breed-diverse cohort with clinician labels and runtime validation assets.",
    metrics: [
      { label: "Sessions", value: "148" },
      { label: "Breeds", value: "11" },
    ],
  },
];
