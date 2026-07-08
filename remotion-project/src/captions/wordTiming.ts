export interface WordTiming {
  text: string;
  startMs: number;
  endMs: number;
}

const DEFAULT_FPS = 30;

export function msToFrame(ms: number, fps: number = DEFAULT_FPS): number {
  return Math.round((ms / 1000) * fps);
}

export function frameToMs(frame: number, fps: number = DEFAULT_FPS): number {
  return (frame / fps) * 1000;
}

export function getCurrentWordIndex(
  words: WordTiming[],
  currentMs: number,
): number {
  for (let i = 0; i < words.length; i++) {
    if (currentMs >= words[i].startMs && currentMs <= words[i].endMs) {
      return i;
    }
  }
  return -1;
}

export function getCurrentWord(
  words: WordTiming[],
  currentMs: number,
): WordTiming | null {
  const idx = getCurrentWordIndex(words, currentMs);
  return idx >= 0 ? words[idx] : null;
}

export function getWordOpacity(
  index: number,
  currentWordIndex: number,
): number {
  if (index === currentWordIndex) return 1;
  if (index < currentWordIndex) return 0.5;
  return 1;
}
