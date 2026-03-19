"use client";

import { CopilotKitInspector, useCopilotKit } from "@copilotkitnext/react";

export function ExplicitCopilotInspector() {
  const { copilotkit } = useCopilotKit();

  return <CopilotKitInspector core={copilotkit ?? undefined} />;
}
