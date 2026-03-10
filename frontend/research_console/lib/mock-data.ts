export const runCards = [
  { id: "run-001", status: "completed", focus: "French bulldog gait baseline", metric: 0.83 },
  { id: "run-002", status: "queued", focus: "Emotion overlay metric trial", metric: 0.67 },
  { id: "run-003", status: "running", focus: "Clinician validation cohort", metric: 0.74 },
];

export const uploadedVideos = [
  { id: "video-001", name: "session-a.mp4", label: "Placeholder upload" },
  { id: "video-002", name: "session-b.mp4", label: "Runtime validation asset" },
];

export const runDetail = {
  runId: "run-001",
  status: "completed",
  inputVideo: "video-001",
  assets: ["keypoints.json", "metrics.json", "report.json"],
  metrics: [
    { name: "stride_length", value: 0.83 },
    { name: "asymmetry_index", value: 0.12 },
  ],
  recommendation: "Dummy runtime validation result: the fake metrics are stable enough to proceed to a real worker integration test.",
};
