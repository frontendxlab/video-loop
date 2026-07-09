# VideoForge v2 — Review & Plan (Deterministic Multi-Engine Director)

> Review of current architecture against the goal (MCP-native, agent-agnostic,
> deterministic PR/issue/changelog → video), against the Remotion showcase ceiling
> (https://www.remotion.dev/prompts), and against the explicit requirement that
> an AI agent acts as a *quality gate* for non-deterministic surfaces (voice/timing
> mismatch, slide overlap, script design) while a strong **decision layer** delegates
> work between **Remotion**, **Manim**, and **Animotion** and uses Remotion to combine
> all outputs.

---

## 1. Honest review — where you are today

Reading the actual source (not just PLAN.json) shows a working but narrow pipeline,
distinctly smaller than the plan implies:

- **One renderer only.** `src/videoforge/engine/renderer.py` shells out to a single
  Remotion composition (`VideoComposition`) and concatenates clips with
  `ffmpeg -c copy`. **No Manim, no Animotion, no decision layer.** Nothing delegates
  anywhere. The multi-engine routing the target asks for does not exist.
- **8 plain React scenes** (Title/Code/Diff/Bullet/Image/Comparison/Diagram/Outro)
  + 2 animated components (`AnimatedCodeLines`, `AnimatedMindMap`). They're ~100 lines
  each — basic `interpolate`/`spring` on opacity + translateY.
- **Word-timing is fabricated.** `_estimate_timestamps` in `scripts/orchestrator.py`
  divides `duration / numWords` evenly. Pocket TTS returns no real word boundaries, so
  caption sync drifts systematically, and every `getStepProgress`-driven line/node reveal
  is driven off fake timestamps. **This is the single biggest accuracy bug.**
- **No syntax highlighting.** `CodeScene` renders raw `whiteSpace: "pre"` monospace text.
  No Prism, no Shiki, no language grammar. The "developer explainer" USP looks like a
  plain text box.
- **No real diagram engine.** `AnimatedMindMap` is hand-positioned React nodes with a
  fixed `NODE_WIDTH = 160`. It cannot lay out a real graph, flowchart, sequence diagram,
  system architecture, or chart.
- **Timeline is linear and fragile.** No `Sequence`/`Series` transition packing, no
  per-scene `durationInFrames` via `calculateMetadata`, manual `sceneStartFrame` offset
  math, hardcoded 30fps, hardcoded 1920×1080.
- **The "MCP-native, multi-agent, GitHub-webhook" architecture in PLAN.json is mostly
  aspirational.** `app.py`, `server.py`, `webhook/`, `fetcher/`, `github/` exist, but the
  working path is `scripts/orchestrator.py` → `engine/`. **Two parallel codepaths, neither
  complete.**
- **Frame reviewer is L1-only in practice.** `docs/LESSONS.md` confirms L2–L5 are "slow"
  and rarely run. **No AI quality gate anywhere.**
- **No decision layer at all** — the target explicitly asks for one (Remotion vs Animotion
  vs Manim) and there is zero code for it.

### 1.1 The Remotion showcase gap

From `remotion.dev/prompts`, the creative ceiling people reach with Remotion:

> Travel Route on Map with 3D landmarks · News article headline highlight · Product Demo
> for Presscut · Launch Video on X · Cinematic Tech Intro · Transparent Call-To-Action
> overlay · Rocket Launches Timeline · Real Estate Investing · Three.js "Top 20 Games
> Sold" Ranking · Promotion video for VVTerm · Music CD store promo · Bar + Line Chart
> (combined)

The current scenes can produce **none** of these. You're stuck in "slide with bullet
points + a monospace code box." The thing missing from every showcase piece is
**deterministic, content-driven generation** — they are all hand-authored. That is actually
your real differentiator if built correctly: *take unstructured content → produce a
showcase-grade video deterministically, with an AI gate.* Today you have neither the
showcase-grade visuals nor the AI gate.

---

## 2. Guiding principles (non-negotiable)

1. **Deterministic by default, AI as the gate.** Same input → byte-identical output. The AI
   never proposes frames, audio, or timing. It only *verifies* proposed deterministic
   artifacts.
2. **One source of truth timeline.** A typed scene graph (IR) is the contract. Every engine
   reads the same IR; the director picks which engine renders which node.
3. **Closed loop, not open loop.** Generate → gate → repair → re-generate. Every
   non-deterministic surface (voice/timing, script, layout) has an AI gate with a concrete
   pass/fail signal and an automatic repair loop with a **bounded retry budget**.

---

## 3. Architecture — strict 3 layers

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1 — DETERMINISTIC DIRECTOR  (Python, pure functions)  │
│  content IR → scene graph → per-engine work orders           │
│  timing source of truth (no LLM in the hot path)             │
└───────────────┬───────────────┬───────────────┬──────────────┘
                │               │               │
        ┌───────▼───┐   ┌───────▼───┐   ┌───────▼───┐
        │  REMOTION │   │   MANIM   │   │ ANIMOTION │   ← engines
        │  (TS)     │   │  (Python) │   │   (web)   │
        └───────┬───┘   └───────┬───┘   └───────┬───┘
                │               │               │
        ┌───────▼───────────────▼───────────────▼──────────┐
        │  LAYER 2 — ASSEMBLER (FFmpeg, deterministic)      │
        │  per-clip → common timebase → final MP4           │
        └───────────────────────┬──────────────────────────┘
                                │
        ┌───────────────────────▼──────────────────────────┐
        │  LAYER 3 — AI QUALITY GATES (LLM, offline, retry) │
        │  voice/word alignment · script design · layout    │
        │  cross-engine visual coherence · final review     │
        └───────────────────────────────────────────────────┘
```

### 3.1 Layer 1 — Deterministic Director (rewrite the orchestrator)

Replace the ad-hoc `scenes.json` + `orchestrator.py` with a typed intermediate
representation. Everything downstream is a pure consumer.

**Content IR (the contract):**

```python
@dataclass(frozen=True)
class SceneNode:
    id: str
    kind: Literal["title", "code", "diff", "bullets", "diagram",
                  "chart", "timeline", "map3d", "comparison", "quote", "outro"]
    payload: dict          # fully resolved, deterministic data
    engine_hint: Engine    # remotion | manim | animotion
    duration_frames: int
    narration: NarrationSpec   # text + authoritative word timings

@dataclass(frozen=True)
class NarrationSpec:
    text: str
    words: list[WordTiming]   # word, start_ms, end_ms — REAL, measured
    source: Literal["forced_align", "exact_synthesis"]
```

The IR is a **frozen dataclass with a canonical JSON serialization and a content hash.**
`hash(IR)` is the cache key. Same hash → same video, byte-identical. This is the
determinism guarantee, and it is enforceable in CI (golden-file test on the hash).

**The Decision Layer (explicit requirement) — a deterministic, auditable, rule-based router
(NOT an LLM):**

```python
def pick_engine(node: SceneNode) -> Engine:
    k = node.kind
    if k in ("code", "diff", "bullets", "title", "comparison", "quote", "outro"):
        return Engine.REMOTION        # text/UI/typography → React
    if k == "diagram" and node.payload.get("layout") == "math_graph":
        return Engine.MANIM            # true graph layout, math animations
    if k in ("chart", "timeline", "map3d", "ranking"):
        return Engine.MANIM            # programmatic geometry, data-driven
    if k == "diagram" and node.payload.get("interactive"):
        return Engine.ANIMOTION        # interactive-ish web animation
    return Engine.REMOTION             # safe default
```

Rules live in an **explicit override matrix** (a YAML table you can read and edit), plus a
per-engine capability manifest so the router is self-documenting:

| kind              | layout / shape       | engine    | reason                                  |
|-------------------|----------------------|-----------|-----------------------------------------|
| code / diff       | —                    | Remotion  | Shiki syntax highlighting, React type   |
| bullets/title/quote | —                  | Remotion  | flexbox layout, spring physics          |
| chart             | bar/line/stacked     | Manim     | `BarChart` / `NumberLine` primitives    |
| timeline          | horizontal           | Manim     | `MoveAlongPath`, deterministic tick math|
| diagram           | graph/flowchart      | Manim     | `Graph` with real layout (dot/spring)   |
| diagram           | mindmap / cluster   | Remotion  | `AnimatedMindMap` (improve it)          |
| map3d / ranking   | —                    | Manim / Animotion | 3D / data-viz heavy             |
| comparison        | side-by-side         | Remotion  | split-pane, animated divider            |

This is the "strong enough" decision layer: deterministic, table-driven, overrideable per
scene, and **trivially testable** (run the router over every kind×layout combo → assert
outputs). No AI anywhere in it. AI only reviews whether the *result* matched intent.

### 3.2 Layer 2 — Engines (real investment in visual quality)

This is where you go from "slide deck" to "showcase." Each engine gets the same `SceneNode`
and emits an MP4 clip at a **pinned common timebase** (e.g. 30fps, 1920×1080, H.264, AAC,
`-pix_fmt yuv420p`, `-r 30`). Pinned format = lossless concat works in `ffmpeg -c copy` and
stays deterministic.

**Remotion track (upgrade existing):**
- **Add Shiki** (`@shikijs/rehype` or `shiki` directly) for real syntax highlighting with
  token-level colors per language; render highlighted tokens, animate line-by-line against
  the REAL word timings. This single change makes CodeScene/DiffScene look 10× more
  professional.
- **DiffScene: real diff parsing** (use the `diff` npm lib) with aligned line matching,
  green/red gutters, word-level inline diff highlight, and per-hunk reveal synced to
  narration.
- **ChartScene (new)** via `@remotion/charts` (visx) — bar, line, stacked, animated against
  narration. Covers several showcase pieces.
- **TimelineScene (new)** — horizontal axis with milestones, `MoveAlongPath`-style
  progress, synced to narration.
- **Use `@remotion/google-fonts` properly** for Inter + JetBrains Mono (already a dep, not
  wired into `design-tokens.ts`).

**Manim track (new, Python):**
Manim is the right tool for anything math-y, graph-laid-out, or geometry-precise. Add a
`manim_engine/` package:
- `GraphScene` using `manim.Graph` with `layout="dot"` / `"spring"` — **real graph layout**
  so architecture/system diagrams render deterministically. The current `AnimatedMindMap`
  cannot do this.
- `ChartScene` (`BarChart`, `NumberLine`, `Axes`) for data-viz showcase pieces.
- `TimelineScene` (`NumberLine` + `MoveAlongPath`) for the "Rocket Launches Timeline"
  style.
- Output to MP4 at the pinned timebase; the assembler treats it identically to a Remotion
  clip.

**Animotion track (new, optional):**
For interactive-feeling web animations and Lottie-style motion where Remotion alone is
clumsy. Keep it optional; only wire kinds flagged `interactive`. If it complicates
determinism, defer until v2.1 — but keep the interface so the decision layer can route to
it.

### 3.3 Layer 3 — AI Quality Gates (where AI earns its place)

**Critical principle:** the AI never generates content that goes into the timeline
unchecked. It only (a) generates *candidate* text/slides which the deterministic layer
validates, and (b) *verifies* deterministic output. Every gate has: a binary signal, a
structured report, and an **auto-repair loop with a bounded retry budget (e.g. 3)**.

**Gate 3.1 — Voice/Timing Gate (fixes the #1 bug):**
- Drop fake-even word timing. Use **forced alignment** (`whisper` / `aeneas` /
  `montreal-forced-aligner`) to get real word boundaries from the synthesized WAV +
  transcript. If unavailable, fall back to a *phone-duration model* (`espeak-ng` phone
  timings summed to words) — still measurable, not fabricated.
- **AI gate:** feed (transcript, real word timings, audio) to an LLM with the audio and
  ask: "For each word, is the highlighted caption within ±120ms of the spoken word? List
  mismatches." Output: list of `(word_index, drift_ms, verdict)`.
- **Auto-repair:** if drift > threshold on >N words, re-run alignment with a different
  segmenter; if still failing, re-chunk TTS at sentence boundaries (≤50 tokens, per the
  existing chunker) and re-align. Bounded retries.

**Gate 3.2 — Slide-Overlap / Layout Gate (fixes L2 properly):**
- **Deterministic core:** export Remotion layer bounding boxes via `@remotion/renderer`'s
  `getImages` / frame metadata and run IoU overlap detection in Python (deterministic).
  This is the L2 that was written down but never made fast.
- **AI gate:** render mid-scene PNGs at 3 timestamps; send to a vision LLM: "Are any text
  elements clipped, overlapping label/box, or off-canvas? Return JSON list of issues with
  coordinates." Vision LLMs are excellent at "two cards overlap." This is the
  non-deterministic overlap detector — but it only runs on deterministic frames and never
  edits them.
- **Auto-repair:** on overlap, nudge layout via the IR (`payload.spacing`), re-render that
  scene. Bounded.

**Gate 3.3 — Script-Design Gate (the "story" gate):**
- **Deterministic skeleton:** the director enforces a 4-arc structure (context → problem →
  solution → impact) as a *rule* — scene kinds must include those roles. The LLM never
  decides structure; it writes *within* it.
- **AI gate:** review the script for 4-arc presence, pacing, and redundancy (the existing
  LogicChecker concept, but actually LLM-powered, not regex). Output: missing arc / weak
  transition / redundant claim.
- **Auto-repair:** re-prompt the LLM with the specific gap ("add a 1-sentence 'impact' line
  for scene 4"), regenerate ONLY the affected narration, re-align audio. Bounded.

**Gate 3.4 — Cross-Engine Visual-Coherence Gate (new, important):**
Since clips now mix Remotion + Manim, the biggest risk is visual whiplash (different fonts,
colors, easing across engines).
- **Deterministic core:** a shared `design-tokens.json` that ALL engines load (Manim reads
  it into `ManimConfig`, Remotion imports it, Animotion loads it). One palette, one font
  stack, one easing curve.
- **AI gate:** sample 1 frame from each clip → vision LLM: "Do these look like the same
  video? (font, color, weight, spacing). List per-clip deviations." Fail → re-render the
  offending clip from tokens. Bounded.

**Gate 3.5 — Final Whole-Video Review Gate:**
- Vision LLM watches the assembled MP4 (or sampled frames every 2s) for: caption mismatch,
  freeze, text overflow, off-brand color, broken transition. Produces the FrameReviewReport
  already spec'd, but actually. Bounded retries on the specific failed scene only.

**Gate summary table (every non-deterministic surface covered):**

| Surface             | Deterministic core          | AI gate signal          | Repair                         |
|---------------------|-----------------------------|-------------------------|--------------------------------|
| Word timing         | forced alignment            | ±120ms drift count      | re-align / re-chunk            |
| Layout overlap      | IoU on bounding boxes       | vision "overlap?"       | nudge spacing, re-render       |
| Script coherence    | 4-arc rule, rule-based      | LLM "arc present?"      | targeted re-prompt             |
| Cross-engine look   | shared design tokens        | vision "same video?"    | re-render from tokens          |
| Final video         | L1 FFmpeg integrity         | vision full review      | re-render failed scene         |

---

## 4. Execution plan (concrete, ordered)

### Phase 0 — Stop the bleeding (≈2 days)
1. Add a `golden_hash` CI test: `hash(IR)` must match a committed hash for a fixture
   PR → enforce determinism immediately.
2. Replace `_estimate_timestamps` with real forced alignment (start with `aeneas`: light,
   Python, deterministic-ish). This alone fixes captions and all `getStepProgress`-driven
   reveals.
3. Pin render format (`yuv420p`, `-r 30`, AAC) so concat is truly lossless and
   reproducible.

### Phase 1 — Director + IR (≈5 days)
4. Define the frozen `SceneNode` IR + JSON schema + content-hash.
5. Extract scene→engine routing table (the YAML above) + unit tests covering every cell.
6. Make the assembler engine-agnostic (it already mostly is — just insist on the pinned clip
   format).

### Phase 2 — Remotion upgrade (≈1 week)
7. Shiki syntax highlighting on CodeScene/DiffScene; real diff parsing on DiffScene.
8. Add ChartScene + TimelineScene; wire `@remotion/google-fonts` into tokens.
9. Make `AnimatedMindMap` use a real layout (`d3-hierarchy` tree) instead of fixed widths.

### Phase 3 — Manim track (≈1 week)
10. `manim_engine/` package: GraphScene (dot/spring layout), ChartScene, TimelineScene.
11. Shared `design-tokens.json` → `ManimConfig` mapping.
12. Route `diagram`/`chart`/`timeline` kinds to Manim; verify the decision layer actually
    delegates.

### Phase 4 — AI gates (≈1 week)
13. Voice / alignment gate.
14. Layout-overlap vision gate.
15. Script-coherence gate.
16. Cross-engine coherence gate.
17. Final review gate.
Each: structured report + bounded retry loop + cost/use log.

### Phase 5 — Showcase parity (ongoing)
18. Re-create 3 of the Remotion showcase pieces *deterministically* from content IR: a
    Rocket-Launches-style timeline, a "Top N ranking" chart, a route-on-map. These become
    the golden demos and the CI fixtures.

---

## 5. What to cut from the current plan

- **GitHub webhook + PR comment publisher (slice-011)** — premature; the value is the
  video, not the trigger. Make it a thin adapter in v2.1.
- **The parallel `app.py` / `server.py` / `webhook/` MCP surface** — pick one path (the
  `engine/` + `scripts/orchestrator.py` path) and delete the other. Two codepaths is why
  nothing feels done.
- **Custom voice cloning, YouTube upload, template marketplace** — already deferred; keep
  deferred.

---

## 6. The one-sentence upgrade

> Today VideoForge is "8 React scenes + fabricated timing + one renderer, no gates."
> v2 makes it *"a deterministic director that routes a typed scene graph to
> Remotion/Manim/Animotion, assembles a byte-reproducible MP4, and runs five bounded AI
> gates — voice, layout, script, cross-engine coherence, final review — each with
> auto-repair."* That is the 10,000×: the showcase visual ceiling (multi-engine), real
> caption sync (forced alignment), and the only place an LLM belongs (verifying, not
> generating the artifact).

**Recommended first move:** Phase 0 — forced alignment + determinism CI test + pinned
render format. Highest leverage, lowest risk, fixes the worst current bug in ~2 days.
