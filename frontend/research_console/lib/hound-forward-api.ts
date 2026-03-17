const DEFAULT_HOUND_FORWARD_API_URL = "http://127.0.0.1:8000";

export function getHoundForwardApiBase(): string {
  const configured =
    process.env.HOUND_FORWARD_API_URL ??
    process.env.NEXT_PUBLIC_HOUND_FORWARD_API_URL ??
    DEFAULT_HOUND_FORWARD_API_URL;

  return configured.replace(/\/$/, "");
}
