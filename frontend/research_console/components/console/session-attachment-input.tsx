"use client";

import { useEffect, useRef, useState } from "react";
import { Paperclip, Send, Square, LoaderCircle, FileText, ImageIcon, Film } from "lucide-react";

import {
  fetchConsoleAttachments,
  getAttachmentDisplayName,
  uploadConsoleAttachment,
} from "@/lib/console-attachment-client";
import { ConsoleAttachment } from "@/lib/console-attachment-types";

const ATTACHMENT_ACCEPT = "video/*,image/*,text/*,.txt,.md,.csv,.json,.yaml,.yml,.log";

type SessionAttachmentInputProps = {
  chatReady?: boolean;
  inProgress: boolean;
  onSend: (text: string) => Promise<unknown>;
  onStop?: () => void;
  hideStopButton?: boolean;
  threadId: string;
};

function getAttachmentIcon(kind: string) {
  if (kind === "video") {
    return Film;
  }
  if (kind === "image") {
    return ImageIcon;
  }
  return FileText;
}

export function SessionAttachmentInput({
  chatReady = false,
  inProgress,
  onSend,
  onStop,
  hideStopButton = false,
  threadId,
}: SessionAttachmentInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [text, setText] = useState("");
  const [isComposing, setIsComposing] = useState(false);
  const [attachments, setAttachments] = useState<ConsoleAttachment[]>([]);
  const [pendingAttachmentIds, setPendingAttachmentIds] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadAttachments() {
      if (!threadId) {
        setAttachments([]);
        setUploadStatus("");
        return;
      }

      try {
        const payload = await fetchConsoleAttachments(threadId);
        if (cancelled) {
          return;
        }

        setAttachments(payload.attachments ?? []);
        setPendingAttachmentIds([]);
        setUploadStatus("");
      } catch (error) {
        if (!cancelled) {
          setUploadStatus(error instanceof Error ? error.message : "Unable to load attachments.");
        }
      }
    }

    void loadAttachments();

    return () => {
      cancelled = true;
    };
  }, [threadId]);

  async function handleSend() {
    const next = buildAttachmentAwareMessage(
      text,
      attachments.filter((attachment) => pendingAttachmentIds.includes(attachment.asset_id)),
    );
    if (!next || inProgress || !chatReady) {
      return;
    }

    await onSend(next);
    setText("");
    setPendingAttachmentIds([]);
    textareaRef.current?.focus();
  }

  async function handleUpload(files: FileList | null) {
    if (!files?.length || !threadId) {
      return;
    }

    setIsUploading(true);
    setUploadStatus(`Uploading ${files.length} attachment${files.length > 1 ? "s" : ""}...`);

    try {
      const uploaded = await Promise.all(Array.from(files).map((file) => uploadConsoleAttachment(threadId, file)));
      const nextAssets = uploaded
        .map((item) => item.asset)
        .filter((item): item is ConsoleAttachment => Boolean(item));

      setAttachments((current) => [...nextAssets, ...current]);
      setPendingAttachmentIds((current) => [...nextAssets.map((item) => item.asset_id), ...current]);
      setUploadStatus(`Attached ${nextAssets.length} file${nextAssets.length > 1 ? "s" : ""} to this session.`);
    } catch (error) {
      setUploadStatus(error instanceof Error ? error.message : "Unable to upload attachment.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }

  const canStop = inProgress && !hideStopButton;
  const canSend = chatReady && !inProgress && (text.trim().length > 0 || pendingAttachmentIds.length > 0);

  return (
    <div className="copilotKitInputContainer">
      <div className="copilotKitInput" onClick={(event) => {
        const target = event.target as HTMLElement;
        if (!target.closest("button")) {
          textareaRef.current?.focus();
        }
      }}>
        {attachments.length > 0 ? (
          <div className="sessionAttachmentTray">
            {attachments.slice(0, 6).map((attachment) => {
              const Icon = getAttachmentIcon(attachment.kind);
              return (
                <div key={attachment.asset_id} className="sessionAttachmentChip">
                  <Icon size={14} strokeWidth={1.8} />
                  <span title={getAttachmentDisplayName(attachment)}>{getAttachmentDisplayName(attachment)}</span>
                </div>
              );
            })}
            {attachments.length > 6 ? <div className="sessionAttachmentCount">+{attachments.length - 6} more</div> : null}
          </div>
        ) : null}

        <textarea
          ref={textareaRef}
          className="sessionAttachmentTextarea"
          placeholder="Ask about evidence, videos, metrics, or the latest run..."
          rows={1}
          value={text}
          onChange={(event) => setText(event.target.value)}
          onCompositionStart={() => setIsComposing(true)}
          onCompositionEnd={() => setIsComposing(false)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey && !isComposing) {
              event.preventDefault();
              void handleSend();
            }
          }}
        />

        <div className="sessionAttachmentFooter">
          <div className="sessionAttachmentMeta">
            <button
              type="button"
              className="copilotKitInputControlButton sessionAttachmentButton"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading || !threadId}
              aria-label="Attach files"
              title="Attach files"
            >
              {isUploading ? <LoaderCircle size={18} className="animate-spin" /> : <Paperclip size={18} />}
            </button>
            <span className="sessionAttachmentStatus">
              {uploadStatus || `${attachments.length} attachment${attachments.length === 1 ? "" : "s"} linked to this session`}
            </span>
          </div>

          <button
            type="button"
            className="copilotKitInputControlButton sessionSendButton"
            onClick={canStop ? onStop : () => void handleSend()}
            disabled={!canStop && !canSend}
            aria-label={canStop ? "Stop" : "Send"}
          >
            {canStop ? <Square size={18} fill="currentColor" /> : <Send size={18} />}
          </button>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ATTACHMENT_ACCEPT}
          className="hidden"
          onChange={(event) => void handleUpload(event.target.files)}
        />
      </div>
    </div>
  );
}

function buildAttachmentAwareMessage(text: string, attachments: ConsoleAttachment[]): string {
  const trimmed = text.trim();
  if (!attachments.length) {
    return trimmed;
  }

  const attachmentSummary = attachments
    .slice(0, 6)
    .map((attachment) => `- ${getAttachmentDisplayName(attachment)} (${attachment.kind}, asset ${attachment.asset_id})`)
    .join("\n");

  if (!trimmed) {
    return `I attached these files to the current session:\n${attachmentSummary}\nPlease use them in this conversation.`;
  }

  return `${trimmed}\n\nCurrent session attachments:\n${attachmentSummary}`;
}
