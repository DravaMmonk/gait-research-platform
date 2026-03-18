"use client";

import type { ComponentProps } from "react";
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";

import { ExplicitCopilotInspector } from "@/components/console/explicit-copilot-inspector";
import { SessionAttachmentInput } from "@/components/console/session-attachment-input";

const starterPrompts = [
  { title: "Summarize", message: "Summarize this session." },
  { title: "Videos", message: "List the uploaded video assets in the current session." },
  { title: "Evidence", message: "Explain the evidence supporting the latest findings." },
];

export function CopilotSessionChat({ threadId }: { threadId: string }) {
  function ChatInput(props: {
    chatReady?: boolean;
    inProgress: boolean;
    onSend: (text: string) => Promise<unknown>;
    onStop?: () => void;
    hideStopButton?: boolean;
  }) {
    return <SessionAttachmentInput {...props} threadId={threadId} />;
  }

  return (
    <CopilotKit key={threadId} runtimeUrl="/api/copilotkit" threadId={threadId}>
      <>
        <ExplicitCopilotInspector />
        <CopilotChat
          className="research-chat"
          Input={ChatInput as ComponentProps<typeof CopilotChat>["Input"]}
          labels={{
            title: "Research Assistant",
            initial: "Ask a question about the current session.",
            placeholder: "Ask about evidence, videos, metrics, or the latest run...",
          }}
          suggestions={starterPrompts}
        />
      </>
    </CopilotKit>
  );
}
