export interface WordTiming {
  text: string;
  startMs: number;
  endMs: number;
}

export interface TimelineStep {
  startMs: number;
  endMs: number;
  durationMs: number;
  label: string;
}

export function getStepProgress(
  currentFrame: number,
  fps: number,
  stepStartMs: number,
  stepEndMs: number,
  sceneStartFrame: number,
): number {
  const currentMs = ((currentFrame - sceneStartFrame) / fps) * 1000;
  if (currentMs < stepStartMs) return 0;
  if (currentMs >= stepEndMs) return 1;
  return (currentMs - stepStartMs) / (stepEndMs - stepStartMs);
}

export function buildTimelineFromWords(
  words: WordTiming[],
  wordsPerStep: number = 5,
): TimelineStep[] {
  const steps: TimelineStep[] = [];
  for (let i = 0; i < words.length; i += wordsPerStep) {
    const chunk = words.slice(i, i + wordsPerStep);
    const startMs = chunk[0].startMs;
    const endMs = chunk[chunk.length - 1].endMs;
    steps.push({
      startMs,
      endMs,
      durationMs: endMs - startMs,
      label: chunk.map((w) => w.text).join(" "),
    });
  }
  return steps;
}

export function getActiveStepIndex(
  currentFrame: number,
  fps: number,
  steps: TimelineStep[],
  sceneStartFrame: number,
): number {
  const currentMs = ((currentFrame - sceneStartFrame) / fps) * 1000;
  for (let i = steps.length - 1; i >= 0; i--) {
    if (currentMs >= steps[i].startMs) return i;
  }
  return -1;
}
