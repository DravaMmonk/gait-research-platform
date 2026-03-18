export type ConsoleAttachment = {
  asset_id: string;
  session_id?: string | null;
  kind: "video" | "image" | "text";
  blob_path: string;
  checksum: string;
  mime_type: string;
  created_at: string;
  metadata?: Record<string, unknown>;
};

export type ConsoleAttachmentListResponse = {
  session_id: string;
  attachments?: ConsoleAttachment[];
};

export type ConsoleAttachmentUploadResponse = {
  session_id: string;
  asset: ConsoleAttachment;
  placeholder_flags?: Record<string, boolean>;
};
