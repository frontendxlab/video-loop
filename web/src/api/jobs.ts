/* Jobs API client — grill prompt + create job + multi-turn grill */

import type { CreateOptions, GrillResult } from "@/contracts/create";
import { CreateJobRequestSchema, GrillResultSchema, GrillStartResponseSchema, GrillTurnResponseSchema } from "@/contracts/create";
import type { GrillStartResponse, GrillTurnResponse } from "@/contracts/create";

const BASE = "/api/jobs";

export interface CreateJobResponse {
  jobId: string;
  status: "queued" | "running";
  grillResult: GrillResult;
}

export async function grillPrompt(prompt: string, options: CreateOptions, recipeId?: string, templateIds?: string[]): Promise<GrillResult> {
  const body = CreateJobRequestSchema.parse({ prompt, options, recipeId, templateIds });
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

export async function startGrill(prompt: string, options: CreateOptions): Promise<GrillStartResponse> {
  const res = await fetch(`${BASE}/grill/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, options }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Start grill failed (${res.status}): ${text}`);
  }
  return GrillStartResponseSchema.parse(await res.json());
}

export async function submitGrillTurn(sessionId: string, answer: string, done?: boolean): Promise<GrillTurnResponse> {
  const res = await fetch(`${BASE}/grill/turn`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sessionId, answer, done: done ?? false }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Grill turn failed (${res.status}): ${text}`);
  }
  return GrillTurnResponseSchema.parse(await res.json());
}

export async function createJob(prompt: string, options: CreateOptions, recipeId?: string, templateIds?: string[], grillSessionId?: string): Promise<CreateJobResponse> {
  const body = CreateJobRequestSchema.parse({ prompt, options, recipeId, templateIds });
  const res = await fetch(BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...body, grillSessionId }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Create job failed (${res.status}): ${text}`);
  }
  return res.json();
}
