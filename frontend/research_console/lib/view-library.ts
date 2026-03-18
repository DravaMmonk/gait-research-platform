import { ConsoleViewMode, VisualModule } from "@/lib/console-types";

export type ViewLibrarySection = "modules" | "tools";
export type ViewLibraryEntryKind = "module" | "tool";
export type ViewLibraryStatus = "core" | "stable" | "preview";

type ViewLibraryEntryBase = {
  id: string;
  kind: ViewLibraryEntryKind;
  title: string;
  summary: string;
  category: string;
  tags: string[];
  status: ViewLibraryStatus;
};

export type ModuleLibraryEntry = ViewLibraryEntryBase & {
  kind: "module";
  defaultViewMode: ConsoleViewMode;
  example: VisualModule;
};

export type ToolContractExample = {
  inputKind: string;
  outputKind: string;
  outputArtifactName: string;
  exampleInput: Record<string, unknown>;
  exampleOutput: Record<string, unknown>;
  source: string;
};

export type ToolLibraryEntry = ViewLibraryEntryBase & {
  kind: "tool";
  contract: ToolContractExample;
};

export type ViewLibraryEntry = ModuleLibraryEntry | ToolLibraryEntry;

export const moduleLibraryEntries: ModuleLibraryEntry[] = [
  {
    id: "module-summary-card",
    kind: "module",
    title: "Summary Card",
    summary: "Headline synthesis with stable highlights for the agent's first-pass answer.",
    category: "Summaries",
    tags: ["summary", "status", "highlights"],
    status: "core",
    defaultViewMode: "summary",
    example: {
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
  },
  {
    id: "module-comparison-cards",
    kind: "module",
    title: "Comparison Cards",
    summary: "Compact side-by-side deltas for ranking or before-versus-after explanation.",
    category: "Summaries",
    tags: ["comparison", "delta", "summary"],
    status: "stable",
    defaultViewMode: "summary",
    example: {
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
  },
  {
    id: "module-trend-chart",
    kind: "module",
    title: "Trend Chart",
    summary: "Time-series chart for controlled metric review inside the shared panel shell.",
    category: "Charts",
    tags: ["trend", "time-series", "chart"],
    status: "core",
    defaultViewMode: "chart",
    example: {
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
  },
  {
    id: "module-metric-table",
    kind: "module",
    title: "Metric Table",
    summary: "Width-safe table for raw or derived rows with explicit sort context.",
    category: "Tables",
    tags: ["table", "metrics", "raw-values"],
    status: "core",
    defaultViewMode: "table",
    example: {
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
  },
  {
    id: "module-evidence-panel",
    kind: "module",
    title: "Evidence Panel",
    summary: "Evidence-aware context with provenance, review state, and supporting sources.",
    category: "Evidence",
    tags: ["evidence", "provenance", "review"],
    status: "core",
    defaultViewMode: "evidence",
    example: {
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
  },
  {
    id: "module-video-panel",
    kind: "module",
    title: "Video Panel",
    summary: "Reference slot for linked clip review without leaving the controlled agent surface.",
    category: "Media",
    tags: ["video", "review", "clip"],
    status: "stable",
    defaultViewMode: "video",
    example: {
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
  },
  {
    id: "module-formula-card",
    kind: "module",
    title: "Formula Explanation",
    summary: "Structured formula context that stays readable for longer expressions and assumptions.",
    category: "Evidence",
    tags: ["formula", "interpretation", "assumptions"],
    status: "stable",
    defaultViewMode: "formula",
    example: {
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
  },
];

export const toolLibraryEntries: ToolLibraryEntry[] = [
  {
    id: "tool-decode-video",
    kind: "tool",
    title: "decode_video",
    summary: "Probe uploaded video metadata before downstream analysis.",
    category: "Video Intake",
    tags: ["video", "metadata", "report"],
    status: "core",
    contract: {
      inputKind: "video",
      outputKind: "report",
      outputArtifactName: "decoded_video.json",
      source: "hound_forward/agent_tools/video.py",
      exampleInput: {
        asset_id: "asset-video-001",
        blob_path: "runs/run-001/input/source.mp4",
        config: {
          sample_stride: 24,
        },
      },
      exampleOutput: {
        frames: 938,
        fps: 30,
        duration_seconds: 31.3,
        width: 1920,
        height: 1080,
      },
    },
  },
  {
    id: "tool-extract-keypoints",
    kind: "tool",
    title: "extract_keypoints",
    summary: "Generate keypoint-like motion frames from a video asset.",
    category: "Pose",
    tags: ["video", "pose", "keypoints"],
    status: "core",
    contract: {
      inputKind: "video",
      outputKind: "keypoints",
      outputArtifactName: "keypoints.json",
      source: "hound_forward/agent_tools/pose.py",
      exampleInput: {
        asset_id: "asset-video-001",
        blob_path: "runs/run-001/input/source.mp4",
        config: {
          frame_stride: 2,
        },
      },
      exampleOutput: {
        frame_count: 468,
        joints: ["nose", "left_front_paw", "right_front_paw", "left_hind_paw", "right_hind_paw"],
        confidence_threshold: 0.5,
      },
    },
  },
  {
    id: "tool-compute-gait-metrics",
    kind: "tool",
    title: "compute_gait_metrics",
    summary: "Compute gait metrics from extracted keypoint frames.",
    category: "Metrics",
    tags: ["keypoints", "metrics", "signals"],
    status: "core",
    contract: {
      inputKind: "keypoints",
      outputKind: "metric_result",
      outputArtifactName: "metrics.json",
      source: "hound_forward/agent_tools/metrics.py",
      exampleInput: {
        asset_id: "asset-keypoints-001",
        blob_path: "runs/run-001/artifacts/keypoints.json",
        config: {
          metrics: ["stride_length", "asymmetry_index", "mobility_index_v2"],
        },
      },
      exampleOutput: {
        metric_count: 3,
        metrics: {
          stride_length: 0.83,
          asymmetry_index: 0.12,
          mobility_index_v2: 0.74,
        },
      },
    },
  },
  {
    id: "tool-generate-report",
    kind: "tool",
    title: "generate_report",
    summary: "Assemble a report from metric outputs.",
    category: "Reporting",
    tags: ["report", "metrics", "summary"],
    status: "core",
    contract: {
      inputKind: "metric_result",
      outputKind: "report",
      outputArtifactName: "report.json",
      source: "hound_forward/agent_tools/reports.py",
      exampleInput: {
        asset_id: "asset-metric-result-001",
        blob_path: "runs/run-001/artifacts/metrics.json",
        config: {
          include_recommendations: true,
        },
      },
      exampleOutput: {
        sections: ["summary", "metrics", "review_notes"],
        summary: "Mobility fell in March and partially recovered in April.",
        warning_count: 1,
      },
    },
  },
  {
    id: "tool-get-run-logs",
    kind: "tool",
    title: "get_run_logs",
    summary: "Read execution events, job states, and inline report previews for a run.",
    category: "Debugging",
    tags: ["run", "logs", "report", "debug"],
    status: "stable",
    contract: {
      inputKind: "run_id",
      outputKind: "run_execution_log",
      outputArtifactName: "inline_response",
      source: "hound_forward/application/services.py",
      exampleInput: {
        run_id: "run-001",
      },
      exampleOutput: {
        run: {
          run_id: "run-001",
          status: "failed",
        },
        events: [
          { status: "queued", message: "Run queued." },
          { status: "running", message: "Run started." },
          { status: "failed", message: "Run failed." },
        ],
        jobs: [
          { job_type: "run_execution", status: "failed" },
        ],
        report_assets: [
          {
            kind: "report",
            blob_path: "runs/run-001/report.json",
            preview: {
              available: true,
              format: "json",
              content: {
                summary: {
                  status: "failed",
                },
              },
            },
          },
        ],
        latest_error: {
          type: "ValueError",
          message: "Keypoint extraction returned no frames.",
        },
      },
    },
  },
  {
    id: "tool-visualize-pysr-manifest",
    kind: "tool",
    title: "visualize_pysr_manifest",
    summary: "Summarize a symbolic manifest for review and governance.",
    category: "Symbolic",
    tags: ["manifest", "pysr", "governance"],
    status: "stable",
    contract: {
      inputKind: "manifest",
      outputKind: "report",
      outputArtifactName: "manifest_review.json",
      source: "hound_forward/agent_tools/symbolic.py",
      exampleInput: {
        asset_id: "asset-manifest-001",
        blob_path: "manifests/gait_pain_discovery_v1.yaml",
        config: {
          include_formula_overview: true,
        },
      },
      exampleOutput: {
        formula_count: 4,
        flagged_terms: ["body_length", "hind_stance_ratio"],
        reviewer_note: "Requires formula provenance review before promotion.",
      },
    },
  },
];

export const viewLibrarySections: Array<{ id: ViewLibrarySection; label: string; description: string }> = [
  {
    id: "modules",
    label: "Visual Modules",
    description: "Frontend rendering contracts for structured agent output.",
  },
  {
    id: "tools",
    label: "Agent Tools",
    description: "Static previews of executor-backed tool contracts and artifacts.",
  },
];

export function getViewLibraryEntries(section: ViewLibrarySection): ViewLibraryEntry[] {
  return section === "modules" ? moduleLibraryEntries : toolLibraryEntries;
}
