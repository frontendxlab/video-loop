/* Jobs API client — grill prompt + create job */

import type { CreateOptions, GrillResult } from "@/contracts/create";
import { CreateJobRequestSchema, GrillResultSchema } from "@/contracts/create";

const BASE = "/api/jobs";

export interface CreateJobResponse {
  jobId: string;
  status: "queued" | "running";
  grillResult: GrillResult;
}

export async function grillPrompt(prompt: string, options: CreateOptions, recipeId?: string): Promise<GrillResult> {
  const body = CreateJobRequestSchema.parse({ prompt, options, recipeId });
  const res = await fetch(`${BASE}/grill`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Grill failed (${res.status}): ${text}`);
  }
  const data = await res.json();
  return GrillResultSchema.parse(data);
}

export async function createJob(prompt: string, options: CreateOptions, recipeId?: string): Promise<CreateJobResponse> {
  const body = CreateJobRequestSchema.parse({ prompt, options, recipeId });
  const res = await fetch(BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Create job failed (${res.status}): ${text}`);
  }
  return res.json();
}
