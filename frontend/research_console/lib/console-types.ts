export type DisplayPreference =
  | "table_only"
  | "prefer_chart"
  | "prefer_video"
  | "raw_values_only"
  | "evidence_first";

export type ConsoleViewMode = "summary" | "chart" | "table" | "evidence" | "video" | "formula";

export type ActiveContext = {
  session_id?: string;
  run_id?: string;
  metric_name?: string;
  formula_definition_id?: string;
  asset_id?: string;
};

export type ConsoleThreadMessage = {
  role: "user" | "assistant";
  content: string;
  created_at: string;
};

export type ToolTraceItem = {
  tool_name: string;
  purpose: string;
  status: string;
  details: Record<string, unknown>;
};

export type EvidenceContext = {
  metric_definition: string;
  time_range: string;
  data_quality: string;
  clinician_reviewed: boolean;
  derived_metric: boolean;
  references: string[];
};

export type SummaryCardModule = {
  type: "summary_card";
  title: string;
  view_mode: "summary";
  payload: {
    title: string;
    summary: string;
    status: string;
    highlights: Array<{ label: string; value: string }>;
  };
};

export type TrendChartModule = {
  type: "trend_chart";
  title: string;
  view_mode: "chart";
  payload: {
    metric: string;
    unit: string;
    time_range: string;
    x_axis: string;
    y_axis: string;
    series: Array<{ label: string; value: number }>;
  };
};

export type MetricTableModule = {
  type: "metric_table";
  title: string;
  view_mode: "table";
  payload: {
    metric: string;
    columns: Array<{ key: string; label: string }>;
    rows: Array<{ values: Record<string, string | number | boolean | null>; raw: boolean; derived: boolean }>;
    sort?: string | null;
  };
};

export type EvidencePanelModule = {
  type: "evidence_panel";
  title: string;
  view_mode: "evidence";
  payload: {
    confidence: string;
    review_status: string;
    missingness: string;
    provenance: string;
    sources: Array<{ label: string; kind: string; reference: string }>;
  };
};

export type FormulaExplanationModule = {
  type: "formula_explanation_card";
  title: string;
  view_mode: "formula";
  payload: {
    formula_id: string;
    expression: string;
    interpretation: string;
    assumptions: string[];
  };
};

export type VideoPanelModule = {
  type: "video_panel";
  title: string;
  view_mode: "video";
  payload: {
    asset_id: string;
    title: string;
    timestamp_range: string;
    related_metrics: string[];
  };
};

export type ComparisonCardsModule = {
  type: "comparison_cards";
  title: string;
  view_mode: "summary";
  payload: {
    title: string;
    items: Array<{ label: string; value: string; delta?: string | null }>;
  };
};

export type VisualModule =
  | SummaryCardModule
  | TrendChartModule
  | MetricTableModule
  | EvidencePanelModule
  | FormulaExplanationModule
  | VideoPanelModule
  | ComparisonCardsModule;

export type ConsoleAgentRequest = {
  session_id: string;
  message: string;
  display_preferences: DisplayPreference[];
  active_context?: ActiveContext | null;
};

export type ConsoleAgentResponse = {
  thread: ConsoleThreadMessage[];
  message: string;
  modules: VisualModule[];
  view_modes: ConsoleViewMode[];
  tool_trace: ToolTraceItem[];
  evidence_context: EvidenceContext;
  warnings: string[];
  suggested_followups: string[];
};

export type WorkspaceCard = {
  id: string;
  label: string;
  title: string;
  status: string;
  description: string;
  metrics: Array<{ label: string; value: string }>;
};
