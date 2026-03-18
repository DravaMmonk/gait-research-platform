import {
  type ConsoleAttachment,
  type ConsoleAttachmentListResponse,
  type ConsoleAttachmentUploadResponse,
} from "@/lib/console-attachment-types";

export async function fetchConsoleAttachments(sessionId: string): Promise<ConsoleAttachmentListResponse> {
  const response = await fetch(`/api/console/session/${sessionId}/attachments`, {
    method: "GET",
    cache: "no-store",
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { error?: string } | null;
    throw new Error(payload?.error || "Unable to load attachments.");
  }

  return (await response.json()) as ConsoleAttachmentListResponse;
}

export async function uploadConsoleAttachment(sessionId: string, file: File): Promise<ConsoleAttachmentUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`/api/console/session/${sessionId}/attachments`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { error?: string } | null;
    throw new Error(payload?.error || "Unable to upload attachment.");
  }

  return (await response.json()) as ConsoleAttachmentUploadResponse;
}

export function getAttachmentDisplayName(attachment: ConsoleAttachment): string {
  const original = attachment.metadata?.original_file_name;
  if (typeof original === "string" && original.length > 0) {
    return original;
  }

  const fileName = attachment.metadata?.file_name;
  if (typeof fileName === "string" && fileName.length > 0) {
    return fileName;
  }

  const pathPart = attachment.blob_path.split("/").pop() || "attachment";
  return pathPart.replace(/^[0-9a-f-]{36}-/, "");
}
