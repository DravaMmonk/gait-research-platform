import { NextResponse } from "next/server";

import { getAiSdkRuntimeStatus } from "@/lib/ai-sdk-server";

export function GET() {
  return NextResponse.json(getAiSdkRuntimeStatus());
}
