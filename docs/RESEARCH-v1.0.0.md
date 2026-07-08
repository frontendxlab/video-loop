# 🎬 VideoForge — Complete Research & Architecture Compendium

**Version:** 1.0.0  
**Date:** 2026-07-08  
**Status:** Research Complete, Ready for Build  
**Project:** `/home/rashid/projects/videoforge/`  
**Dependency:** `/home/rashid/projects/pocket-tts-mcp/` (Pocket TTS MCP Server)

---

## TABLE OF CONTENTS

1. [Devil's Advocate Iteration Chain](#1-devils-advocate-iteration-chain)
2. [Foundations: Loop Engineering Patterns](#2-foundations-loop-engineering-patterns)
3. [Pocket TTS MCP Server (Completed)](#3-pocket-tts-mcp-server-completed)
4. [Remotion Core Technical Reference](#4-remotion-core-technical-reference)
5. [Remotion Skills Ecosystem (42 Skills)](#5-remotion-skills-ecosystem-42-skills)
6. [Animotion (Reveal.js) Deep Dive](#6-animotion-revealjs-deep-dive)
7. [Manim vs Remotion: Head-to-Head](#7-manim-vs-remotion-head-to-head)
8. [Diagram Animation: The Middle Subagent](#8-diagram-animation-the-middle-subagent)
9. [Full skills.sh Inventory (50+ Skills)](#9-full-skillssh-inventory-50-skills)
10. [Competitive Landscape & Gap Analysis](#10-competitive-landscape--gap-analysis)
11. [System Architecture (v10 Final)](#11-system-architecture-v10-final)
12. [The 16 Agents: Phase-by-Phase](#12-the-16-agents-phase-by-phase)
13. [GitHub Integration Architecture](#13-github-integration-architecture)
14. [Audio Pipeline: Critical Path](#14-audio-pipeline-critical-path)
15. [Risk Matrix & Mitigations](#15-risk-matrix--mitigations)

---

## 1. Devil's Advocate Iteration Chain

### Methodology

Each iteration applies ruthless self-critique to the previous design. The goal: 10 iterations, each improving the architecture 10x. This ensures no assumption goes unchallenged.

---

### Iteration v1: The Naive "Just Add Agents" Design

**Initial instinct:** Create a monolithic MCP server with 30+ agents, each doing one tiny task.

```
Content → TTS → Remotion → Video
         ↓
   10 agents per step
```

**Critique:** "Pocket TTS has a hard limit of 50 tokens per chunk. Long scripts fail silently. There's no text segmentation strategy. Audio breaks before it starts."

**Resolution:** Sentence-level TTS segmentation with crossfade stitching. Detect sentence boundaries via punctuation, group into ≤50-token chunks, generate per-chunk audio, stitch with overlap crossfade.

**Impact:** 🔴 Critical — audio pipeline would be non-functional without this.

---

### Iteration v2: The Timing Estimation Fallacy

**Refined design:** Added sentence segmentation. Estimated frame timing from word count.

**Critique:** "Word-count-based frame timing is wildly inaccurate. At 24kHz 16-bit, even 5% error causes perceptible desync within seconds. A 50-word sentence could take 8-15 seconds depending on pacing. No fixed formula works."

**Resolution:** Implement word-level timestamp extraction. Use Whisper.cpp forced-alignment on the generated audio to get per-word `startMs`/`endMs` timestamps. Pass these to Remotion's `createTikTokStyleCaptions()` for frame-perfect word highlighting. Fall back to `edge-tts` word boundaries when Whisper isn't available.

**Impact:** 🔴 Critical — naive timing would produce unwatchable desynced videos.

---

### Iteration v3: Agent Bloat

**Refined design:** Started adding specialists — "Audio Analyzer", "Frame Counter", "Color Matcher", "Duration Estimator", "Caption Aligner"...

**Critique:** "30+ agents doing 1-5% of the work each creates 5x management overhead. Most pipeline calls would be routing between agents that each add 200ms+ latency. Token costs explode."

**Resolution:** Collapse to 16 focused agents, each owning a complete Phase:
- Phase 1 (3 agents): INGEST
- Phase 2 (2 agents): RESEARCH
- Phase 3 (2 agents): SCRIPT
- Phase 4 (2 agents): SCENE PLAN
- Phase 5 (3 agents): ASSET GEN
- Phase 6 (2 agents): COMPOSE + RENDER
- Phase 7 (2 agents): REVIEW + PUBLISH

Each agent produces a structured JSON output that the next consumes.

**Impact:** 🟡 High — 30 agents would be manageable but wasteful. 16 is tight.

---

### Iteration v4: Visual Assets Void

**Refined design:** Pipeline generates text and audio. Video has blank backgrounds with text overlays.

**Critique:** "Blank slides look embarrassing. Users expect professional production quality. Where do images, B-roll, backgrounds, animations come from? AI image generation adds latency and cost. Stock images have no semantic match to code content."

**Resolution:** 3-tier asset system, automatically selected based on content type:
1. **AI-Generated** (Stable Diffusion / FLUX via API): For custom diagrams, conceptual illustrations, hero images
2. **Stock** (Pexels/Pixabay API queries): For backgrounds, tech imagery, abstract visuals
3. **Code-Only** (Shiki syntax highlighter + Monaco editor screenshots): For code walkthroughs, diffs, architecture diagrams

Each scene type has a default visual strategy. If asset generation fails at any tier, cascade down.

**Impact:** 🟡 High — visual quality is a core product differentiator.

---

### Iteration v5: Animotion — False Promise

**Research finding:** Animotion (`@animotion/core`) uses Reveal.js. It runs in a browser. It has no headless rendering API. The `Recorder` component uses `navigator.mediaDevices.getDisplayMedia()` which requires user interaction.

**Critique:** "Animotion is architecturally incompatible with video production. Reveal.js requires a live browser DOM. There is no frame-by-frame rendering, no programmatic export, no server-side render path. Keeping it in the stack adds complexity for zero video benefit."

**Resolution:** ❌ **Drop Animotion entirely for rendering.** Salvage only the `<Code>` component concept (Shiki + shiki-magic-move for animated code diffs) and reimplement in Remotion using `@remotion/captions` + custom code components.

**Impact:** 🔴 Critical — would have wasted weeks integrating an incompatible tool.

---

### Iteration v6: Manim Dependency Trap

**Research finding:** Manim (ManimCommunity/manim) requires Python + Cairo/OpenGL + LaTeX. Linux rendering pipeline often breaks due to dependency version conflicts.

**Critique:** "Adding Manim as a hard dependency breaks the CI/CD dream. GitHub Actions runners don't have Cairo/OpenGL reliably. The pipeline becomes 'works on my machine' — exactly what we're trying to avoid."

**Resolution:** Gate Manim behind a content classifier flag. Only invoke it for scenes tagged as `type: "math"` or `type: "scientific"`. For everything else, use Remotion-native rendering. Export Manim scenes as PNG sequences (with `--transparent` for alpha), then import into Remotion as `<Img src={`manim_frames/frame_${i}.png`} />` sequence.

```typescript
// Remotion imports Manim-rendered PNG sequence
import { useCurrentFrame, Img } from "remotion";

export const ManimScene: React.FC<{ frameCount: number }> = ({ frameCount }) => {
  const frame = useCurrentFrame();
  if (frame >= frameCount) return null;
  const padded = String(frame).padStart(5, "0");
  return <Img src={`manim_frames/frame_${padded}.png`} />;
};
```

**Impact:** 🟡 Medium — Manim is a powerful option but must be optional.

---

### Iteration v7: Rendering Environment Unknowns

**Refined design:** Assume `npx remotion render` works everywhere.

**Critique:** "Remotion rendering depends on:
1. Headless Chromium (Puppeteer) — requires specific Linux libs
2. FFmpeg — must be >= 4.0 with specific codecs
3. `@remotion/bundler` — Webpack build step adds overhead
4. Node.js >= 16

Without explicit documentation and a health check, first-time setup will fail silently for most users."

**Resolution:** Create:
1. Pre-flight health check tool: `videoforge doctor` — checks Node, FFmpeg, Chromium deps
2. Dockerfile for consistent environment
3. Explicit documentation of Linux dependencies (libnss3, libnspr4, libatk-bridge, etc.)
4. CI pipeline that renders a test video on every PR to validate the environment

**Impact:** 🟡 Medium — documented env requirements prevent most issues.

---

### Iteration v8: The Latency Wall

**Refined design:** GitHub webhook → full video pipeline → wait for result → post comment.

**Critique:** "A GitHub webhook fires with a 10-second timeout limit. The full video pipeline (research + script + TTS + image gen + Remotion render) takes 2-10 minutes. The webhook will timeout. The user sees a broken integration."

**Resolution:** Fully async architecture:
1. Webhook handler accepts immediately (HTTP 200), pushes job to queue
2. Queue processor runs pipeline in background
3. Pipeline writes intermediate progress to STATE.md
4. On completion, `gh pr comment` posts the video URL
5. User can poll pipeline status via MCP tool `pipeline_status(job_id)`

```
Time 0:   Webhook received → 200 OK
Time 1s:  Pipeline starts → STATE.md: "rendering"
Time 120s: Pipeline done → STATE.md: "complete"
Time 121s: gh pr comment "🎬 Video generated: [link]"
```

**Impact:** 🔴 Critical — synchronous pipeline would break GitHub integration.

---

### Iteration v9: MCP Protocol Limits

**Refined design:** Return audio as base64-encoded WAV through MCP response.

**Critique:** "A 30-second WAV at 24kHz 16-bit = ~1.4MB. Base64 wraps to ~1.9MB. MCP tools shouldn't transfer multi-megabyte payloads — it kills protocol efficiency, causes truncated responses, and bloats chat tokens. This is the wrong transport for binary data."

**Resolution:** Audio pipeline uses `generate_speech_to_file` (writes WAV to disk), not `generate_speech` (returns base64). The MCP tool returns only paths:

```json
{
  "audio_path": "/tmp/videoforge/scene_03.wav",
  "duration_seconds": 2.64,
  "sample_rate": 24000,
  "word_timestamps_path": "/tmp/videoforge/scene_03_words.json"
}
```

The Remotion project consumes these files from disk using `staticFile()`.

**Impact:** 🟡 High — base64 would work for short clips but fail at scale.

---

### Iteration v10: The Existential Question

**Final critique:** "What's the actual value of this MCP server? An LLM can already write a Remotion video with one prompt: 'Make a video about X using Remotion.' Why not just do that?"

**Resolution analyzed — The MCP Advantage (5 dimensions):**

| Dimension | Direct LLM Prompt | MCP Server Pipeline |
|-----------|------------------|-------------------|
| **Statefulness** | Each call re-explains context | TTS model loaded once (438MB cached) |
| **Tool contract** | Fuzzy — LLM guesses Remotion API | Precise Zod-validated JSON contracts |
| **Cross-platform** | Tied to one LLM | Works with Claude, Codex, Cursor, Copilot |
| **Reproducibility** | Different output every time | Deterministic pipeline, versioned |
| **GitHub integration** | Manual copy-paste | Automated webhook → PR comment |

**Strategic niche:** VideoForge is not a video editor. It is an **automation gateway** that connects GitHub events → structured video pipeline → published output. The MCP server is the API contract that any agent can call.

**Impact:** 🟢 Strategic — this is the core product insight.

---

## 2. Foundations: Loop Engineering Patterns

**Source:** Fully analyzed repo at `/home/rashid/projects/loop-engineering/`

### Core Philosophy

- You design **systems that prompt agents**, not prompts for agents
- A "loop" is a recursive goal with memory, skills, sub-agents, and a kill switch
- Maker/checker split: implementer never verifies its own work

### The 7 Canonical Patterns and Our Adaptation

| Pattern | Cadence | Original Purpose | Our Adaptation |
|---------|---------|------------------|---------------|
| **Daily Triage** | 1d-2h | Scan repo, find issues, update STATE.md | Daily video pipeline health: disk space, model cache, render queue |
| **PR Babysitter** | 5-15m | Watch open PRs, flag issues | PR opened → trigger video generation webhook |
| **CI Sweeper** | 5-15m | Fix failing CI | Video render failure → auto-retry with diagnostic mode |
| **Post-Merge Cleanup** | 1d-6h | Scan merged diffs for TODOs | PR merged → generate changelog video segment |
| **Changelog Drafter** | 1d | Generate changelog from merged PRs | Monthly "Top PRs" compilation video |
| **Issue Triage** | 2h-1d | Classify and label issues | Issue opened → generate video explainer |
| **Dependency Sweeper** | 6h-1d | Audit and patch dependencies | Video dependency updates → regenerate affected videos |

### L1→L2→L3 Maturity for Our Pipeline

| Level | Behavior | When |
|-------|----------|------|
| **L1** | Report-only: log what would be done, no actual render | Week 1-2 calibration |
| **L2** | Assisted: render video, but human must review before posting | Week 2-4 validation |
| **L3** | Unattended: auto-render and auto-post to PR on safe paths | Week 4+ (after review accuracy > 95%) |

### STATE.md Format (Our Adaptation)

```markdown
# VideoForge State

## High Priority
- [ ] job-20260708-001 — PR #12 "Add auth middleware" — WAITING_FOR_ASSETS (audio: ready, images: generating)
- [ ] job-20260708-002 — Issue #45 "Bug in data pipeline" — QUEUED

## Watch List
- job-20260707-015 — PASSED (posted as comment to PR #10)

## Recent Failures
- job-20260707-016 — FAILED (TTS model load timeout — retried 3x, escalated)

## Budget
- Tokens today: 245,000 / 1,000,000
- Renders today: 4 / 20
- Pending jobs: 2

---

Last run: 2026-07-08 14:30 UTC | Findings: 2 new jobs, 1 completed, 0 escalation
```

---

## 3. Pocket TTS MCP Server (Completed)

**Location:** `/home/rashid/projects/pocket-tts-mcp/`  
**Files:** `pocket_tts_mcp_server.py`, `start.sh`

### Verified Status

| Check | Status |
|-------|--------|
| Initialize (handshake) | ✅ |
| List 13 tools | ✅ |
| List 3 resources | ✅ |
| 26 predefined voices | ✅ |
| 12 language variants | ✅ |
| Voice clone from audio | ✅ |
| Save voice as .safetensors | ✅ |
| Load voice from .safetensors | ✅ |
| Generate speech (base64 WAV) | ✅ |
| Generate speech to file | ✅ |
| Batch generation | ✅ |
| Lazy model load (438MB) | ✅ |
| Verified audio (24kHz 16-bit mono WAV) | ✅ |
| 0.47x real-time factor (CPU) | ✅ |

### Critical API for VideoForge

```python
# Primary interface — returns file path, not base64
generate_speech_to_file(
    text="This is the script for scene one.",
    output_path="/tmp/videoforge/scene_01.wav",
    voice="alba",
)

# Voice cloning for custom narration
clone_voice(
    audio_path="/path/to/narrator_sample.wav",
    name="custom_narrator",
)
```

### Architectural Note

The TTS model stays loaded in memory (438MB). The MCP server should be a long-running daemon that the video pipeline calls via `npx videoforge` CLI → local JSON-RPC → MCP tool. Avoid loading the model per-job.

---

## 4. Remotion Core Technical Reference

### Package Stack

| Package | Download/Week | Purpose |
|---------|---------------|---------|
| `remotion` | 4.8M | Core: Composition, useCurrentFrame, interpolate, spring, Sequence |
| `@remotion/renderer` | 3.6M | renderMedia(), selectComposition() for Node.js SSR |
| `@remotion/bundler` | 3.5M | Webpack bundling for headless render |
| `@remotion/transitions` | 214K | TransitionSeries + 6 transitions |
| `@remotion/media` | — | `<Audio>`, `<Video>` components |
| `@remotion/media-utils` | — | useAudioData(), visualizeAudio(), getAudioData() |
| `@remotion/captions` | — | createTikTokStyleCaptions(), word-level captions |
| `@remotion/effects` | — | 55+ visual effects (WebGL2 + 2D) |
| `@remotion/google-fonts` | 1.2M | Programmatic font loading |
| `@remotion/lambda` | — | AWS Lambda serverless rendering |

### Core Animation Primitives

```tsx
const frame = useCurrentFrame(); // 0, 1, 2, ..., durationInFrames-1
const { width, height, fps, durationInFrames } = useVideoConfig();

// Linear interpolation (primary animation driver)
const opacity = interpolate(frame, [0, 30], [0, 1], {
  extrapolateRight: "clamp",
  extrapolateLeft: "clamp",
});

// Spring physics (for bouncy animations)
const scale = spring({ frame, fps, config: { damping: 10, stiffness: 100 } });

// Color interpolation
const bgColor = interpolateColors(frame, [0, 60], ["#0000ff", "#ff0000"]);

// Easing
import { Easing } from "remotion";
const eased = interpolate(frame, [0, 60], [0, 1], {
  easing: Easing.bezier(0.16, 1, 0.3, 1),
});
```

### Headless Rendering

```typescript
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";

async function renderVideo(inputProps: object, outputPath: string) {
  const serveUrl = await bundle({
    entryPoint: "./src/index.ts",
    webpackOverride: (config) => config,
  });

  const composition = await selectComposition({
    serveUrl,
    id: "GeneratedVideo",
    inputProps,
  });

  await renderMedia({
    composition,
    serveUrl,
    codec: "h264",
    outputLocation: outputPath,
    inputProps,
    concurrency: null, // auto-detect CPU cores
    onProgress: ({ progress }) => console.log(`${Math.round(progress * 100)}%`),
  });
}
```

### CLI

```bash
npx remotion render GeneratedVideo out/video.mp4 --props='{"title":"Hello"}'
npx remotion render GeneratedVideo out/video.mp4 --props="./input-props.json"
npx remotion render --codec=mp3 GeneratedVideo out/audio.mp3  # Audio-only
```

### TransitionSeries

```tsx
import { TransitionSeries, linearTiming, springTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { wipe } from "@remotion/transitions/wipe";
import { flip } from "@remotion/transitions/flip";

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={60}>
    <SceneA />
  </TransitionSeries.Sequence>
  <TransitionSeries.Transition
    presentation={slide({ direction: "from-left" })}
    timing={springTiming({ config: { damping: 200 } })}
  />
  <TransitionSeries.Sequence durationInFrames={90}>
    <SceneB />
  </TransitionSeries.Sequence>
</TransitionSeries>
```

---

## 5. Remotion Skills Ecosystem (42 Skills)

### Source 1: `remotion-dev/skills` (standalone, 4 skills, 414.2K installs)

```bash
npx skills add remotion-dev/skills
```

| Skill | Installs | What It Teaches |
|-------|----------|-----------------|
| **remotion-best-practices** | 414.2K | 30+ rule files: animations, audio, assets, 3D, text, transitions, captions, FFmpeg |
| mediabunny | 0 | Media inspection (duration, dimensions, frame extraction) |
| remotion | 0 | Meta-index of Remotion domain knowledge |
| 3d | 0 | Three.js / React Three Fiber integration |

### Source 2: `remotion-dev/remotion` (in-repo, 36 skills, 15.7K installs)

```bash
npx skills add https://github.com/remotion-dev/remotion --skill <name>
```

**Key skills for our pipeline:**

| Skill | Installs | Purpose |
|-------|----------|---------|
| video-report | 1.6K | Debug broken video renders (download → create NewVideo → render verbose) |
| homepage-video-assets | 3 | ProRes 4444 master rendering + codec conversion |
| add-effect | 314 | Author visual effects for @remotion/effects |
| add-sfx | 1.4K | Add sound effects to @remotion/sfx |
| visual-mode | 318 | Visual sequence editing in Remotion Studio |

### The 30+ Rule Files (loaded on demand by remotion-best-practices)

These are the actual domain knowledge files an agent reads when building a Remotion video:

**Animation rules:**
- `timing.md` — interpolate(), Bezier easing, springs, timing strategies
- `text-animations.md` — Typography animation patterns
- `transitions.md` — Scene transition patterns
- `effects.md` — 55+ visual effects (chromaticAberration, blur, glow, pixelate, wave...)

**Audio rules:**
- `audio.md` — Audio trimming, volume, speed, pitch
- `audio-visualization.md` — Spectrum bars, waveforms, bass-reactive effects
- `voiceover.md` — AI voiceover using ElevenLabs TTS
- `sfx.md` — Sound effects integration
- `silence-detection.md` — FFmpeg silence detection and trimming
- `ffmpeg.md` — FFmpeg operations for video processing

**Captions rules:**
- `subtitles.md` — Caption/subtitle overlay
- `display-captions.md` — Caption display patterns
- `import-srt-captions.md` — SRT file import
- `transcribe-captions.md` — Audio transcription to captions

**Composition rules:**
- `compositions.md` — Stills, folders, default props, nested compositions
- `sequencing.md` — Delay, trim, duration limit
- `parameters.md` — Zod schemas for parametrizable compositions
- `calculate-metadata.md` — Dynamic duration, dimensions, props

**Asset rules:**
- `images.md` — Image sizing, positioning, dynamic paths
- `gifs.md` — GIF display synchronized to timeline
- `lottie.md` — Lottie animation embedding
- `google-fonts.md` — Font loading
- `measuring-text.md` — Text dimension measurement

**Media rules:**
- `get-audio-duration.md` — Audio duration via Mediabunny
- `get-video-dimensions.md` — Video dimensions via Mediabunny
- `get-video-duration.md` — Video duration via Mediabunny

**3D/Maps rules:**
- `3d.md` — Three.js / R3F
- `maplibre.md` — Animated routes/flyovers
- `mapbox.md` — Mapbox integration

**Styling:**
- `tailwind.md` — TailwindCSS in Remotion

---

## 6. Animotion (Reveal.js) Deep Dive

**Repo analyzed:** `/home/rashid/projects/animotion/` — fully read

### Architecture Summary

| Layer | Technology | Role |
|-------|------------|------|
| Framework | Svelte 5 (runes) | All components |
| Slide engine | Reveal.js 6.0.1 | Navigation, fragments, auto-animate, transitions |
| Styling | Tailwind CSS 4 | Layout |
| Syntax highlight | Shiki 4 + shiki-magic-move 1.3 | Code animation |
| Custom animation | @animotion/motion 2 | Tween library |
| View transitions | View Transitions API | Cross-element morphing |

### All Components

| Component | Purpose | Key Props |
|-----------|---------|-----------|
| `Presentation` | Top-level deck init | `options` (RevealConfig) |
| `Slide` | Single `<section>` | `transition`, `animate`, `background`, `gradient`, `image` |
| `Slides` | File-based route loader | `center` |
| `Transition` | Fragment animation + View Transitions | `do`, `undo`, `order`, `name`, `entry`, `exit` |
| `Action` | Headless imperative trigger | `do`, `undo`, `order`, `actions` |
| `Code` | Animated Shiki code display | `code`, `codes`, `lang`, `theme`, `options` |
| `Embed` | Nested Reveal instance | `options` |
| `Notes` | Speaker notes | — |
| `Recorder` | Screen recording | `codec`, `fps`, `bitrate`, `systemAudio`, `useMicrophone` |

### The Code Component (700 lines — most complex)

This is the only component worth porting to Remotion.

**Exported API:**
```typescript
code.update`function hello() { ... }`     // Replace all code
code.append`  console.log('new line')`     // Append lines
code.insert`5:2 console.log('inserted')`   // Insert at line 5, indent 2
code.replace("old", "new")                 // Find and replace
code.selectLines`1-3`                      // Highlight lines 1-3
code.select`function`                      // Highlight token "function"
code.select`2 function:0`                  // First "function" on line 2
code.selectAdd`count`                      // Add to selection
code.scrollToLine`25`                      // Scroll to line 25
code.remove`2-4`                           // Remove lines 2-4
```

**Two rendering modes:**
- Single `code` prop → static highlighted code
- `codes={["state1", "state2"]}` → auto-chained Actions stepping through states

### ❌ Why Animotion is Rejected for Video

| Animotion Feature | Video Requirement | Gap |
|------------------|-------------------|-----|
| Reveal.js slide navigation | Linear frame-by-frame timeline | No frame-based API |
| Fragment steps via user click | Automated programmatic advance | No automation API |
| `Recorder` component | Headless server-side render | Requires user interaction |
| View Transitions API | Deterministic per-frame output | Not frame-capturable |
| Browser DOM required | Server/CLI environment | Cannot headless render |

**Salvage only:** The `<Code>` component's shiki-magic-move patterns. Rewrite as a Remotion `<AnimatedCode>` component.

---

## 7. Manim vs Remotion: Head-to-Head

### Decision Matrix

| Criterion | Manim (ManimCE) | Remotion | Winner |
|-----------|----------------|----------|--------|
| LaTeX math | Native `MathTex()`, full LaTeX | No built-in | **MANIM** |
| Vector precision | Cairo: true vectors at any zoom | Canvas: pixel-based | **MANIM** |
| Geometric transforms | Built-in morph, rotate, scale | Manual CSS transforms | **MANIM** |
| 3D rendering | OpenGL: spheres, cubes, camera rotation | Three.js via @remotion/three | **MANIM** |
| Code highlighting | Manual (no highlighter) | Shiki, Prism, Highlight.js | **REMOTION** |
| Rich text layout | Manual coordinate math | CSS Flexbox/Grid | **REMOTION** |
| Audio sync | None (manual `self.wait()`) | `<Audio>` + visualizeAudio() | **REMOTION** |
| Branding/design | Manual theme propagation | React component reuse | **REMOTION** |
| Cloud rendering | AWS/GCP (manual setup) | @remotion/lambda (turnkey) | **REMOTION** |
| Rendering speed | Cairo CPU-bound | GPU-accelerated, parallel | **REMOTION** |
| Community templates | Few (academic) | 35+ production templates | **REMOTION** |

### Integration Strategy

```
IF scene_type == "math" OR scene_type == "scientific":
    → Manim pipeline:
        manim -qh scene.py MathScene → math_clip.mp4
        → Import into Remotion as <OffthreadVideo src="math_clip.mp4" />
ELSE:
    → Remotion-native rendering
```

### Output Formats from Manim for Remotion Import

```bash
# MP4 with solid background (default)
manim -qh scene.py SceneName

# PNG sequence with transparency (for overlay)
manim scene.py SceneName --format=png --transparent
# Output: media/images/SceneName/frame_000000.png, frame_000001.png, ...

# Single frame (for thumbnail generation)
manim -s scene.py SceneName
```

### Bridge Projects Found

| Project | Stars | Architecture |
|---------|-------|-------------|
| `wilwaldon/Claude-Code-Video-Toolkit` | 61 | Manim + Remotion + screen recording + FFmpeg |
| `nafeu/educational-video-pipeline` | 0 | Audio → Whisper → Manim → Remotion compose |
| `iart-ai/motion-skills` | 256 | 51 agent skills for Manim, Remotion, WebGL |
| `bassimeledath/manimate` | 0 | Prompt → Manim Python code → render → MP4 |

---

## 8. Diagram Animation: The Middle Subagent

### Problem Statement

A "middle subagent" that turns a **static diagram** (Mermaid, D2, Excalidraw, Archify JSON IR) into **multiple animated frames**, each precisely synced to voice-over via word-level timestamps.

### Requirements

1. Input: structured diagram description (nodes, edges, labels, positions)
2. Output: animated frame sequence or Remotion component
3. Animation: step-by-step reveal (element by element), not just a fade-in
4. Sync: each reveal aligns with specific words in the audio track
5. Resolution: 1920x1080, 30fps

### Tool Rankings

#### #1 Motion Canvas (18.8k stars) — RECOMMENDED

**Why it fits:**
- Purpose-built for "vector animation + voice-over sync" (per docs)
- `waitUntil('eventName')` puts draggable pills on a timeline that you align to audio waveform
- JSX scene graph: `<Rect>`, `<Txt>`, `<Circle>`, `<Arrow>`, `<Layout>`
- Generator-based animation: `yield * myNode().opacity(1, 0.3)`
- Full step-by-step build:
  ```typescript
  yield * waitUntil('show-user');
  yield * all(userBox().opacity(1, 0.3), userLabel().opacity(1, 0.3));
  yield * waitUntil('show-api');
  yield * all(apiBox().opacity(1, 0.3), apiLabel().opacity(1, 0.3));
  ```
- Render: `npm run render` → PNG image sequence → `ffmpeg -i %05d.png -i audio.wav output.mp4`
- **License:** MIT

**Limitation:** Requires manual timeline adjustment in browser UI. Not fully automated for CI.

#### #2 `shetty4l/diagrams` (npm) — BEST FOR FULL AUTOMATION

**Why it fits:**
- **Remotion-native** — renders directly via `npx remotion render`
- Declarative JSON config (no manual editor needed)
- Timeline system: `fillBox`, `drawLine`, `dim`, `reveal`, `hold`, `parallel`
- Grid-based layout — no coordinate math
- 18 built-in icons, 2 theme presets

```tsx
const config: DiagramConfig = {
  grid: { rows: 1, cols: 3 },
  nodes: [
    { id: "client", label: "Client", icon: "user", position: { row: 0, col: 0 } },
    { id: "api", label: "API Server", icon: "server", position: { row: 0, col: 1 } },
    { id: "db", label: "Database", icon: "database", position: { row: 0, col: 2 } },
  ],
  connections: [
    { from: "client", to: "api", label: "REST" },
    { from: "api", to: "db", label: "SQL" },
  ],
  timeline: [
    { type: "hold", duration: 1 },
    { type: "sequence", steps: [
      { action: "fillBox", target: "client", step: { num: 1, text: "User sends request" } },
      { action: "drawLine", target: "client->api" },
      { action: "fillBox", target: "api", step: { num: 2, text: "API processes" } },
    ]},
  ],
};
```

**Limitation:** Only architecture-style diagrams (grid layout). No tree, sequence, or ER support.

#### #3 `Limitless2023/animated-diagrams` — MERMAID TO REMOTION

**Why it fits:**
- Natural language → Mermaid → dagre auto-layout → Remotion animation → MP4
- 9 pre-built compositions
- Multiple visual skins (CRT green, amber, ice blue)
- CRT filter (scanlines, vignette, flicker) for tech aesthetic
- Title cards with typewriter + cursor, subtitle tracks

**Limitation:** More opinionated (designed for a specific brand). Less flexible for custom layouts.

#### #4 `aiflow-motion` — BROWSER-BASED EXPORT TO MP4

**Why it fits:**
- 7 edge animation types, 6 node animation types
- Direct MP4/WebM/GIF export
- 6,100+ brand logos from SimpleIcons

**Limitation:** Browser-based editing, not fully programmable.

#### #5 Archify (3.1k stars) — TRACE ANIMATION IN HTML

**Why it fits:**
- JSON IR → typed renderers → self-contained HTML with trace animation
- Opt-in `meta.animation: "trace"` for animated arrow flow
- Dual-theme SVG export

**Limitation:** HTML/SVG output, not video. Would need headless browser capture → import into Remotion.

### Diagram Generation Skills (for Input)

| Tool | Stars | Diagram Types | Output | Overlap Prevention |
|------|-------|---------------|--------|-------------------|
| **baoyu-diagram** | 23.3k | 9 types: architecture, flowchart, sequence, structural, mind map, timeline, illustrative, state machine, data flow | Raw SVG | Explicit rules: 40px vertical gap, 30px horizontal, 10px arrow clearance, 20px padding |
| **Archify** | 3.1k | 5 types: architecture, workflow, sequence, data flow, lifecycle | JSON IR → HTML/SVG/PNG | Schema validation, route-crossing guard, same-lane orthogonal routing |

### Recommended Diagram Pipeline

```
INPUT:
  baoyu-diagram / Archify / Mermaid / D2
         ↓
     (parse nodes + edges + positions)
         ↓
[shetty4l/diagrams JSON config]   [Motion Canvas TSX]   [DIY Remotion <DiagramScene>]
         ↓                                ↓                          ↓
  npx remotion render           User aligns in editor         Custom component
         ↓                                ↓                          ↓
     MP4 frame                        PNG sequence               MP4 frame
```

For **fully automated CI/CD**, use `shetty4l/diagrams` (no manual step).  
For **human-supervised quality**, use Motion Canvas (best sync).  

---

## 9. Full skills.sh Inventory (50+ Skills)

### Group A: HyperFrames — Complete Video Production (20 skills, 33.7K stars)

```bash
npx skills add heygen-com/hyperframes
```

| # | Skill | Installs | Purpose |
|---|-------|----------|---------|
| 1 | **hyperframes** | 178.1K | Router — reads first, dispatches all video requests |
| 2 | **pr-to-video** | 78.6K | **GitHub PR → changelog/feature video** (via `gh` CLI) |
| 3 | **website-to-hyperframes** | 89.7K | Website → video tour/portfolio (7 steps) |
| 4 | **faceless-explainer** | 79.7K | Topic explainer from text (no product) |
| 5 | **product-launch-video** | — | Marketing video from URL/brief/script |
| 6 | **general-video** | 80.0K | Fallback: brand reels, title cards, freeform |
| 7 | **motion-graphics** | 80.3K | Short motion graphics (<10s) |
| 8 | **slideshow** | — | Deck with fragments, branching, presenter mode |
| 9 | **talking-head-recut** | — | Talking head with overlays, lower-thirds, PiP |
| 10 | **embedded-captions** | — | Caption/subtitle embedding |
| 11 | **music-to-video** | — | Beat-synced lyric slideshow/promo |
| 12 | **remotion-to-hyperframes** | 151.7K | One-way migration Remotion → HyperFrames |
| 13 | **hyperframes-core** | 80.5K | Technical contract (data-* attributes, tracks) |
| 14 | **hyperframes-animation** | 81.1K | All animation (GSAP/Lottie/Three.js/Anime.js/CSS) |
| 15 | **hyperframes-keyframes** | — | Keyframe authoring (GSAP, CSS, Anime.js, WAAPI) |
| 16 | **hyperframes-creative** | 80.1K | Creative direction: palettes, typography, narration |
| 17 | **media-use** | — | Media OS: TTS, music, images, SFX, icons |
| 18 | **hyperframes-cli** | 173.7K | CLI: init/lint/validate/inspect/preview/render/publish |
| 19 | **hyperframes-registry** | 169.4K | Component registry install and author |
| 20 | **figma** | — | Figma import → motion |
| — | gsap | 92.4K | GSAP reference (timelines, easing, transforms) |
| — | hyperframes-media | 141.9K | TTS (54 voices), Whisper transcription |

### Group B: Emil Kowalski — Design & Animation Quality

| # | Skill | Installs | Purpose |
|---|-------|----------|---------|
| 21 | **emil-design-eng** | 121.2K | Framer Motion design engineering (taste-trained, reverse-engineering animations) |
| 22 | **review-animations** | 20.3K | Animation review: 10 non-negotiable standards (justified motion, frequency-appropriate, easing, performance, a11y) |

**review-animations Standards:**
1. **Justified motion** — Every animation must answer "why?" (spatial consistency / state indication / feedback / explanation / prevent jarring)
2. **Frequency-appropriate** — Keyboard-initiated 100+/day: NO animation. Tens/day: reduced. Occasional: standard. Rare/first-time: delight.
3. Appropriate easing curves
4. Duration tables per animation type
5. Spring config guidelines
6. Gesture standards
7. Clip-path animation rules
8. Performance budget
9. a11y reduced-motion

### Group C: Anthropic — Official Design Skills

| # | Skill | Installs | Purpose |
|---|-------|----------|---------|
| 23 | **canvas-design** | 83.7K | Museum-quality visual art/design artifacts |
| 24 | **frontend-design** | 637.8K | Frontend design patterns and visual polish |
| 25 | **pptx** | 170.0K | PowerPoint presentation creation |
| 26 | **pdf** | 151.7K | PDF manipulation |

### Group D: Paul Bakaus — Impeccable Quality Pack

| # | Skill | Installs | Purpose |
|---|-------|----------|---------|
| 27 | **delight** | 81.0K | Micro-interactions, unexpected joy, sound design |
| 28 | **polish** | 86.4K | Visual polish and refinement |
| 29 | **critique** | 83.8K | Critical design review |
| 30 | **audit** | 83.0K | Design quality auditing |
| 31 | **distill** | 80.6K | Design concept distillation |

### Group E: Design Taste & Visual Design

| # | Skill | Installs | Purpose |
|---|-------|----------|---------|
| 32 | **design-taste-frontend** | 232.3K | Frontend design taste training |
| 33 | **high-end-visual-design** | 183.5K | High-end visual design patterns |
| 34 | **imagegen-frontend-web** | 135.3K | Image generation for web frontends |
| 35 | **brandkit** | 138.0K | Brand identity systems |
| 36 | **image-to-code** | 136.3K | Design images → code |

### Group F: Vercel — UI Infrastructure

| # | Skill | Installs | Purpose |
|---|-------|----------|---------|
| 37 | **web-design-guidelines** | 446.3K | Spacing, typography, interaction, accessibility |
| 38 | **vercel-react-best-practices** | 533.7K | React best practices |
| 39 | **vercel-composition-patterns** | 240.6K | React composition patterns |
| 40 | **agent-browser** | 522.4K | Browser automation |
| 41 | **deploy-to-vercel** | 87.2K | Vercel deployment |

### Group G: Writing & Marketing

| # | Skill | Installs | Purpose |
|---|-------|----------|---------|
| 42 | **copywriting** | 145.5K | Marketing copywriting |
| 43 | **marketing-psychology** | 107.1K | Marketing psychology |
| 44 | **content-strategy** | 102.5K | Content strategy |
| 45 | **seo-audit** | 155.5K | SEO auditing |

### Group H: Browser Automation

| # | Skill | Installs | Purpose |
|---|-------|----------|---------|
| 46 | **browser-act** | 84.3K | Browser interaction |
| 47 | **browser-use** | 83.1K | Browser automation |

---

## 10. Competitive Landscape & Gap Analysis

### All Repos Analyzed (Top 30+)

| Repo | Stars | Focus | Our Differentiator |
|------|-------|-------|-------------------|
| OpenMontage | 35.3K | Full video production studio, Python agent pipelines | MCP-native, agent-agnostic, lightweight |
| animated-diagrams | — | Mermaid → Remotion pipeline | We add full pipeline before diagrams |
| brainrot.js | 955 | TikTok-style shorts | Professional dev content |
| podcast-maker | 693 | Newsletter → video | Git-to-video instead |
| claude-code-video-toolkit | 1.7K | Claude Code video skills | MCP server, any agent |
| editor-pro-max | 203 | Claude Code editor | Agent-agnostic |
| motion-skills | 256 | Remotion/Manim agent skills | Full runtime server |
| devvideostudio | — | Browser video studio | CLI-first, CI/CD native |
| clip-js | 748 | Browser video editor | Automated pipeline |
| ProductVideoCreator | 36 | Product demo videos | Code/content focused |
| shetty4l/diagrams | — | Animated diagram component | Pipeline orchestrator |
| archify | 3.1K | JSON IR → diagram | Animated frame integration |

### The 5 Critical Gaps We Fill

| # | Gap | Evidence | Market |
|----|-----|----------|--------|
| **1** | **MCP-native video generation server** | zero results: "remotion mcp server" or "mcp video generator" | Greenfield |
| **2** | **GitHub PR/Issue → Video** | zero results: "github pr video generator", "pull request video" | Empty niche |
| **3** | **Agent-agnostic video pipeline** | Every existing tool is Claude Code-specific (or Codex-specific) | Clear gap |
| **4** | **Automated code walkthrough from repo** | Code Hike does manual; no automated "repo → tutorial video" | Untapped |
| **5** | **Lightweight headless API-first generator** | OpenMontage: 12 pipelines. Others: SaaS. Nothing lightweight. | Unique position |

### Positioning

```
                    Complexity →
                    Low                  High
Git                ┌──────────────────────┐
awareness   No     │    OURS ☝️           │  brainrot.js
                    │    (MCP + GitHub)    │  podcast-maker
                    │                      │
            Yes     │                      │  OpenMontage
                    │                      │  motion-skills
                    └──────────────────────┘
```

We sit at the intersection of **git-aware + lightweight** — a niche no one occupies.

---

## 11. System Architecture (v10 Final)

### High-Level Flow

```
GitHub Webhook / CLI / MCP Tool Call
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                   VIDEOFORGE MCP SERVER                          │
│                        (Python / FastMCP)                        │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ INGEST   │→ │ RESEARCH │→ │  SCRIPT  │→ │  SCENE PLAN    │  │
│  │ (3 agts) │  │ (2 agts) │  │ (2 agts) │  │  (2 agts)      │  │
│  └──────────┘  └──────────┘  └──────────┘  └───────┬────────┘  │
│                                                      │           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────▼────────┐  │
│  │ DELIVER  │← │  REVIEW  │← │  RENDER  │← │  ASSET GEN     │  │
│  │ (2 agts) │  │ (2 agts) │  │ (1 agt)  │  │  (3 agts)      │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              INTEGRATED SERVICES                            │  │
│  │  ┌──────────────┐  ┌────────────┐  ┌──────────────────┐   │  │
│  │  │ Pocket TTS   │  │ GitHub API │  │ Remotion CLI     │   │  │
│  │  │ (MCP)        │  │ (gh)       │  │ (npx remotion)   │   │  │
│  │  └──────────────┘  └────────────┘  └──────────────────┘   │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
/home/rashid/projects/videoforge/
├── docs/
│   └── RESEARCH-v1.0.0.md          # THIS FILE
├── skills/                          # Agent skill markdown files
│   ├── video-ingest.skill.md
│   ├── video-research.skill.md
│   ├── video-script.skill.md
│   ├── video-scene-plan.skill.md
│   ├── video-assets.skill.md
│   ├── video-compose.skill.md
│   ├── video-render.skill.md
│   └── video-review.skill.md
├── templates/                       # Pipeline input/output templates
│   ├── script-template.json
│   ├── scene-plan-template.json
│   └── input-props-schema.json
├── videoforge_mcp_server.py         # MCP server (orchestrator)
├── config.yaml                      # Global configuration
├── STATE.md                         # Loop state (from loop-engineering)
├── start.sh                         # Launch script
└── remotion-project/                # Remotion video template
    ├── package.json
    ├── remotion.config.ts
    ├── tsconfig.json
    ├── src/
    │   ├── index.ts                 # registerRoot
    │   ├── Root.tsx                  # Composition definitions + Zod schemas
    │   ├── types.ts                  # Shared types
    │   ├── design-tokens.ts          # Colors, fonts, spacing
    │   ├── compositions/
    │   │   ├── CodeWalkthrough.tsx    # For PR walkthroughs
    │   │   ├── PRSummary.tsx          # For PR summaries
    │   │   ├── IssueExplainer.tsx     # For issue explanations
    │   │   ├── ChangelogVideo.tsx     # For changelogs
    │   │   └── ExplainVideo.tsx       # General explainer
    │   ├── scenes/
    │   │   ├── TitleScene.tsx         # Opening title with animation
    │   │   ├── CodeScene.tsx          # Animated code block (Shiki)
    │   │   ├── DiffScene.tsx          # Side-by-side diff view
    │   │   ├── BulletScene.tsx        # Animated bullet points
    │   │   ├── DiagramScene.tsx       # Animated architecture diagram
    │   │   ├── ImageScene.tsx         # Image with Ken Burns effect
    │   │   ├── ComparisonScene.tsx    # Before/after comparison
    │   │   └── OutroScene.tsx         # End screen with CTA
    │   ├── transitions/
    │   │   ├── index.ts               # Transition registry
    │   │   ├── WipeTransition.tsx     # Custom wipe
    │   │   ├── GlitchTransition.tsx   # Glitch effect
    │   │   └── MorphTransition.tsx    # SVG morph
    │   └── components/
    │       ├── AnimatedText.tsx       # Typewriter, word-by-word, fade-in
    │       ├── CodeBlock.tsx          # Shiki code block with line focus
    │       ├── DiffView.tsx           # Code diff renderer
    │       ├── ProgressBar.tsx        # Timeline progress indicator
    │       ├── Captions.tsx           # @remotion/captions word highlighting
    │       └── AudioVisualizer.tsx    # Waveform visualization
    ├── public/                       # Generated assets
    │   ├── audio/
    │   └── images/
    └── output/                       # Rendered videos
```

---

## 12. The 16 Agents: Phase-by-Phase

### Phase 1: INGEST (3 agents)

| # | Agent | MCP Tool | Input | Output |
|---|-------|----------|-------|--------|
| 1 | **ContentFetcher** | `fetch_content` | GitHub URL / prompt / text | Raw content (markdown, code, diff) |
| 2 | **ContentClassifier** | `classify_content` | Raw content | Video type: `PR_WALKTHROUGH`, `ISSUE_EXPLAIN`, `REPO_TOUR`, `CHANGELOG`, `CUSTOM` |
| 3 | **ContentExtractor** | `extract_key_points` | Raw content + type | Structured: key points, code blocks, diffs, metadata |

### Phase 2: RESEARCH (2 agents)

| # | Agent | MCP Tool | Input | Output |
|---|-------|----------|-------|--------|
| 4 | **TopicResearcher** | `research_topic` | Key points + type | Background context, related concepts, domain knowledge |
| 5 | **AudienceAnalyzer** | `analyze_audience` | Content + repo metadata | Target audience, technical level, tone recommendation |

### Phase 3: SCRIPT (2 agents)

| # | Agent | MCP Tool | Input | Output |
|---|-------|----------|-------|--------|
| 6 | **ScriptWriter** | `write_script` | Key points + research + audience | Structured script with timing (intro, body, outro) |
| 7 | **ScriptAnalyst** | `analyze_script` | Draft script | Pacing review, complexity flag, suggested edits |

### Phase 4: SCENE PLAN (2 agents)

| # | Agent | MCP Tool | Input | Output |
|---|-------|----------|-------|--------|
| 8 | **ScenePlanner** | `plan_scenes` | Final script | Scene list: type, text, duration, visuals, transition |
| 9 | **SceneReviewer** | `review_scenes` | Scene plan | Pacing check, visual variety score, coherence score |

### Phase 5: ASSET GEN (3 agents)

| # | Agent | MCP Tool | Input | Output |
|---|-------|----------|-------|--------|
| 10 | **TTSCoordinator** | `generate_audio` | Script segments | WAV files per scene + word timestamps JSON |
| 11 | **ImageGenerator** | `generate_images` | Scene plan | Images saved to `public/images/` |
| 12 | **AssetValidator** | `validate_assets` | All assets | Pass/Fail: resolution, format, duration match |

### Phase 6: COMPOSE + RENDER (2 agents)

| # | Agent | MCP Tool | Input | Output |
|---|-------|----------|-------|--------|
| 13 | **CompositionBuilder** | `build_composition` | Scene plan + assets | Remotion `inputProps` JSON (Zod-validated) |
| 14 | **RenderExecutor** | `render_video` | inputProps + composition ID | Output MP4 path |

### Phase 7: REVIEW + PUBLISH (2 agents)

| # | Agent | MCP Tool | Input | Output |
|---|-------|----------|-------|--------|
| 15 | **QualityReviewer** | `review_video` | MP4 path + scene plan | Review report: audio sync, visual bugs, transitions |
| 16 | **FinalPublisher** | `publish_video` | MP4 path + target | Published: PR comment, file output, URL |

---

## 13. GitHub Integration Architecture

### Triggers

| Event | Action | Latency |
|-------|--------|---------|
| `pull_request.opened` | Generate PR walkthrough video | 2-5 min |
| `issues.opened` | Generate issue explainer | 1-3 min |
| `pull_request.closed` (merged) | Generate changelog segment | 1-2 min |
| Label `build-video` | Generate video for any issue/PR | 1-5 min |
| Cron (daily) | "Top PRs of the day" compilation | 10-15 min |

### Async Webhook Flow

```
GitHub Webhook POST /webhook
         │
         ├── Validate signature (HMAC-SHA256)
         │
         ├── Respond immediately: 200 OK, { job_id: "job-xxx" }
         │
         └── Enqueue job:
               │
               ├── Write to STATE.md: "job-xxx — QUEUED"
               │
               ├── fetch_content()         ← Agent 1
               ├── classify_content()      ← Agent 2
               ├── extract_key_points()    ← Agent 3
               ├── research_topic()        ← Agent 4
               ├── analyze_audience()      ← Agent 5
               ├── write_script()          ← Agent 6
               ├── analyze_script()        ← Agent 7
               ├── plan_scenes()           ← Agent 8
               ├── review_scenes()         ← Agent 9
               ├── generate_audio()        ← Agent 10 (calls Pocket TTS MCP)
               ├── generate_images()       ← Agent 11
               ├── validate_assets()       ← Agent 12
               ├── build_composition()     ← Agent 13
               ├── render_video()          ← Agent 14 (calls npx remotion render)
               ├── review_video()          ← Agent 15
               │
               └── publish_video()         ← Agent 16
                        │
                        ├── gh pr comment JOB-XXX:
                        │     "🎬 Generated walkthrough video: [URL]"
                        │
                        └── Update STATE.md: "job-xxx — COMPLETE"
```

### GitHub Actions Workflow

```yaml
name: VideoForge
on:
  pull_request:
    types: [opened, labeled]
  issues:
    types: [opened, labeled]

jobs:
  trigger-video:
    if: ${{ github.event.label.name == 'build-video' || github.event.action == 'opened' }}
    runs-on: ubuntu-latest
    steps:
      - name: Notify VideoForge MCP Server
        run: |
          curl -X POST ${{ secrets.VIDEOFORGE_URL }}/webhook \
            -H "Authorization: Bearer ${{ secrets.VIDEOFORGE_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{
              "event": "${{ github.event_name }}",
              "action": "${{ github.event.action }}",
              "url": "${{ github.event.issue.html_url || github.event.pull_request.html_url }}",
              "repo": "${{ github.repository }}"
            }'
```

---

## 14. Audio Pipeline: Critical Path

### Flow

```
Raw Script Text
    │
    ▼
1. Split text into sentences
   └─ Regex: /[.!?]\s+|(?:。|！|？)/ (multi-language)
    │
    ▼
2. Group sentences into TTS chunks (≤50 tokens each)
   └─ Pocket TTS max tokens per chunk: 50
   └─ Group by sliding window: add sentences until ≥50 tokens → start new chunk
    │
    ▼
3. For each chunk:
   ├─ Call: generate_speech_to_file(text=chunk, output_path=scene_N.wav, voice=voice)
   ├─ Save WAV to: public/audio/scene_%03d.wav
   └─ Track: chunk_index, text, wav_path
    │
    ▼
4. Stitch chunks into scene WAV files
   └─ Scene = 1+ consecutive TTS chunks
   └─ Use ffmpeg concat for crossfade stitching:
      ffmpeg -i chunk1.wav -i chunk2.wav -filter_complex
        "[0][1]acrossfade=d=0.1:c1=tri:c2=tri" scene_01.wav
    │
    ▼
5. Extract word timestamps (if Whisper available)
   └─ Whisper.cpp forced alignment → JSON:
      { words: [{ text: "Hello", startMs: 0, endMs: 300 }, ...] }
   └─ Fallback: estimate timing from character count ~ 15 chars/sec
    │
    ▼
6. Generate @remotion/captions-compatible captions JSON
   └─ createTikTokStyleCaptions({ captions, combineTokensWithinMilliseconds: 200 })
    │
    ▼
7. Pass to Remotion inputProps:
   {
     audioTracks: [{ src: "scene_01.wav", startFrame: 0, durationFrames: 120 }],
     captions: [...word-level entries...]
   }
    │
    ▼
8. In Remotion component:
   <Audio src={staticFile(audioTracks[0].src)} />
   <Captions captions={captions} />  // word-by-word highlight
```

### Key: Word-Level Sync

```tsx
// Captions.tsx — inside Remotion
import { useCurrentFrame } from "remotion";
import { Captions as CaptionComponent } from "@remotion/captions";

export const Captions: React.FC<{ captions: CaptionWord[]; startFrame: number }> = ({
  captions,
  startFrame,
}) => {
  const frame = useCurrentFrame();
  const currentTimeMs = ((frame - startFrame) / 30) * 1000; // 30fps

  return (
    <div style={{ position: "absolute", bottom: 80, width: "100%", textAlign: "center" }}>
      {captions.map((word, i) => (
        <span
          key={i}
          style={{
            color: currentTimeMs >= word.startMs && currentTimeMs <= word.endMs
              ? "#ffeb3b" : "#ffffff",
            transition: "color 0.05s",
          }}
        >
          {word.text}{" "}
        </span>
      ))}
    </div>
  );
};
```

---

## 15. Risk Matrix & Mitigations

| # | Risk | Severity | Probability | Mitigation |
|---|------|----------|------------|------------|
| 1 | TTS model load timeout (30s+) on first call | 🔴 High | Medium | Health-check endpoint pre-warms model; lazy-load once, keep in memory |
| 2 | Word timestamps inaccurate — audio desync | 🔴 High | Medium | Dual path: Whisper forced-alignment (preferred) + character-count estimation (fallback) |
| 3 | Remotion headless Chromium fails on Linux | 🔴 High | Low | Pre-test: documented Linux deps, Puppeteer `--no-sandbox`, Docker image |
| 4 | Memory exhaustion (438MB TTS + 500MB Chromium) | 🟡 Medium | Medium | Sequential rendering, clean frames after render, `--disable-dev-shm-usage` |
| 5 | GitHub webhook timeout (10s) | 🟡 Medium | High | Async: respond 200 immediately, enqueue background job |
| 6 | Long scripts produce long TTS durations | 🟡 Medium | Medium | Cap video at 5 minutes; for longer, split into parts |
| 7 | Generated images look low quality | 🟢 Low | Medium | 3-tier fallback: AI-gen → stock photo → code-only layout |
| 8 | GitHub API rate limiting | 🟡 Medium | Low | Conditional requests, caching fetched content, exponential backoff |
| 9 | Remotion rendering non-deterministic | 🟡 Medium | Low | Pin versions: `remotion` exact version, `@remotion/renderer` exact version |
| 10 | Pipeline takes too long for user expectations | 🟡 Medium | High | Progress streaming via MCP `resources/pipeline-status`; incremental output |

---

## Appendix A: Scene Type Specifications

### TitleScene
```
Props:
  title: string (required)
  subtitle?: string
  duration: number (in seconds, default 4)
  animation: "fadeIn" | "slideUp" | "typewriter"
  background: { color: string, gradient?: string, image?: string }

Implementation:
  - Large centered title text
  - Subtitle below (fades in 0.5s after title)
  - Background fills frame
  - Entry animation depends on prop
```

### CodeScene
```
Props:
  code: string (required)
  lang: string (required, passed to Shiki)
  theme: string (default: "poimandres")
  highlightLines?: number[] (lines to highlight)
  caption?: string (text below code)
  duration: number (default: varies by code length)
  focusMode: "line" | "token" | "none"

Implementation:
  - Uses @remotion/shiki for syntax highlighting
  - Line numbers on left gutter
  - Highlighted lines get yellow background
  - Optional typewriter effect for code entry
  - Caption fades in after code
```

### DiffScene
```
Props:
  oldCode: string (required)
  newCode: string (required)
  lang: string (required)
  duration: number (default: varies)

Implementation:
  - Side-by-side: old (red tint) | new (green tint)
  - Added lines: green background
  - Removed lines: red background
  - Modified lines: yellow highlight
  - Animated reveal: old side visible first, then new side slides in
```

### BulletScene
```
Props:
  points: string[] (required, 2-5 points)
  duration: number (default: varies, 3s per point)
  entry: "fadeIn" | "slideIn" | "scaleIn"

Implementation:
  - Vertical bullet list
  - Points appear one by one with stagger delay
  - Previous points dim slightly as new point appears
```

### DiagramScene
```
Props:
  nodes: Array<{ id, label, icon?, position: {row, col} }>
  connections: Array<{ from, to, label? }>
  grid: { rows: number, cols: number }
  timeline: Array<step specification>

Implementation:
  - Uses shetty4l/diagrams or custom grid layout
  - Step-by-step reveal: nodes appear, then connections animate
  - Optional overlay text per step
```

### ImageScene
```
Props:
  src: string (path to image)
  caption?: string
  duration: number (default: 4)
  effect: "kenBurns" | "fadeIn" | "zoomIn"

Implementation:
  - Full-screen image with overlay gradient
  - Ken Burns: slow zoom + pan using transform
  - Caption bar on bottom third
```

### ComparisonScene
```
Props:
  labelBefore: string
  labelAfter: string
  contentBefore: ReactNode
  contentAfter: ReactNode
  duration: number (default: 6)

Implementation:
  - Split screen: left = before, right = after
  - Animated divider line sweeps from left to right
  - Before side dims after reveal
  - Labels at top of each half
```

### OutroScene
```
Props:
  title: string
  subtitle?: string
  cta?: string
  links: Array<{ text, url }>
  duration: number (default: 5)
  showThumbnails: boolean

Implementation:
  - Centered text
  - Fade out from previous scene
  - Links animate in one by one
  - "Generated by VideoForge" footer
```

---

## Appendix B: Transition Specifications

| Transition | Duration | Parameters | Effect Description |
|------------|----------|------------|-------------------|
| `fade` | 0.5s | — | Crossfade between scenes |
| `slide-left` | 0.5s | — | Current scene slides left, next slides in from right |
| `slide-up` | 0.5s | — | Current slides up, next slides in from bottom |
| `wipe-left` | 0.4s | — | Vertical line wipes from left to right |
| `flip` | 0.6s | perspective: 1000 | 3D card flip |
| `crossZoom` | 0.5s | strength: 0.4 | Current zooms out blurry, next zooms in sharp |
| `clockWipe` | 0.6s | — | Circular sweep from center |
| `glitch` | 0.2s | intensity: 0.3 | Fast RGB split + displacement |
| `morph` | 0.8s | — | SVG path morphing (for diagram transitions) |
| `none` | 0s | — | Hard cut |
| `push-left` | 0.4s | — | Current pushes next to the left |
| `zoom-in` | 0.5s | — | Zoom into next scene from center |

---

## Appendix C: Key Design Decisions Log

| Decision | Date | Rationale | Reversed? |
|----------|------|-----------|-----------|
| Use Remotion over HyperFrames | 2026-07-08 | Remotion has native captions, captions, word-level timestamps, and better animation primitives for code content | — |
| 16 agents instead of 30+ | 2026-07-08 | Each agent owns a complete Phase; pipeline is 7 phases (not 30 micro-steps) | — |
| Audio post-render (not in-Composition) | 2026-07-08 | Audio mixed by FFmpeg after Remotion render; avoids Chromium audio quirks | — |
| Whisper forced-alignment for word timestamps | 2026-07-08 | Word-count estimation is too inaccurate; need per-word ms precision | — |
| Async webhook (not synchronous) | 2026-07-08 | GitHub timeout is 10s; video pipeline takes 2-10min | — |
| Use shetty4l/diagrams for automated diagram animation | 2026-07-08 | Motion Canvas requires manual editor; diagrams needs CI-compatible automation | — |
| Drop Animotion | 2026-07-08 | Reveal.js is not a video rendering engine; no headless API | ✅ |
| Gate Manim behind content flag | 2026-07-08 | Math-heavy content needs it; general content doesn't | — |
| 3-tier asset generation | 2026-07-08 | AI-gen → stock → code-only cascade prevents blank slides | — |
| MCP returns file paths, not base64 | 2026-07-08 | Base64 audio is ~1.9MB per 30s; protocol was never designed for binary payloads | — |

---

*End of RESEARCH-v1.0.0.md — VideoForce Complete Architecture Compendium*

*Next: Build Phase — MCP Server → Remotion Project → Agent Skills → GitHub Workflow → Docs*
