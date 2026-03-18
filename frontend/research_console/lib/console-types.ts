import type { UIMessage } from "ai";

export type ConsoleViewMode = "summary" | "chart" | "table" | "evidence" | "video" | "formula";

export type ChatResponsePayload = {
  type: "text" | "run" | "error";
  message: string;
  run_id?: string;
  progress_messages?: string[];
  structured_data?: Record<string, unknown>;
};

export type ConsoleUIMessage = UIMessage<
  never,
  {
    progress: {
      message: string;
    };
    result: ChatResponsePayload;
  }
>;

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
