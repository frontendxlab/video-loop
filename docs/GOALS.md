# VideoForge — Goals & Milestones

## Project Vision

VideoForge is an MCP-native automated video generation pipeline that enables any coding agent — Claude Code, Cursor, Copilot, Codex — to produce developer-focused explainer videos directly from GitHub content (PRs, issues, changelogs). By chaining webhook ingestion, content research, scriptwriting, scene planning, local TTS audio generation, Remotion rendering, and automated publishing, VideoForge eliminates the manual video production workflow and delivers frame-accurate, captioned, diagram-rich explainer videos as a plug-and-play MCP tool.

## Strategic Goals

| # | Goal | Rationale | Success Metric |
|---|------|-----------|----------------|
| 1 | **MCP-native architecture** | No existing MCP server provides video generation. Agents must integrate seamlessly via stdio or SSE. | Server passes MCP interoperability test suite; 3+ distinct agents (Claude Code, Cursor, Codex) can call all tools without modification. |
| 2 | **Fully local pipeline** | Users must not depend on cloud APIs for TTS, rendering, or secrets. Privacy and air-gapped operation are requirements. | Pipeline runs end-to-end with zero external API calls (excluding GitHub fetch). Pocket TTS serves all audio locally. |
| 3 | **GitHub PR/Issue → Video in <5 min** | The core value proposition is instant video from developer workflows. Latency kills adoption. | End-to-end render of a PR with <500 lines changed completes in under 5 minutes on a modern laptop (M1 Mac or equivalent). |
| 4 | **Agent-agnostic design** | Every existing competitor is locked to a single agent (Claude Code-specific). VideoForge must work with any MCP-compatible host. | No agent-specific SDK imports in server code; all tool schemas are plain JSON-Schema; same tools work identically across Claude Code, Cursor, Copilot, and Codex. |
| 5 | **Production-quality output** | Videos must be watchable, captioned, and visually polished — not prototypes. Developer audience demands clarity. | Blind review: 4/5 developers rate video quality as "good" or "excellent" on a 5-point scale across clarity, pacing, captions, and diagrams. |

## Milestone Timeline

### M0 — Foundation (Week 1-2)

| Deliverable | Acceptance Criteria |
|-------------|---------------------|
| Project scaffold (Python package + Remotion subproject) | `pip install -e .` succeeds; `npx remotion compositions` lists 0 compositions |
| MCP server skeleton with FastMCP | `videoforge --help` prints usage; server starts and responds to `initialize` |
| TTS audio adapter wrapping Pocket TTS | Audio generation via Pocket TTS HTTP produces valid 24kHz 16-bit WAV |
| Remotion project with `inputProps` plumbing | `npx remotion still` renders a test frame from JSON input |
| `PLAN.json` + `docs/GOALS.md` | Both files exist and are reviewed |
| CI: lint + typecheck + unit test pass | `pytest` passes; `ruff` passes; `tsc --noEmit` passes |

### M1 — Core Assets (Week 3-4)

| Deliverable | Acceptance Criteria |
|-------------|---------------------|
| 8 scene components (Title, Code, Diff, Bullet, Image, Comparison, Diagram, Outro) | Each scene renders in Remotion with mock `inputProps`; visual review passes |
| Scene registry with dynamic composition | Compositions can mix any scene types in sequence |
| 4 composition types (CodeWalkthrough, PRSummary, IssueExplainer, ChangelogVideo) | Each composition accepts its specific `inputProps` schema; renders a complete sequence |
| Transition system (fade, slide, wipe, flip, crossfade) | Transitions render between any two scenes; timing is configurable |
| Word-level caption overlay | Captions render from word-timestamp JSON; current word highlights in sync |
| `@remotion/transitions` + `@remotion/captions` integration | Both packages resolve without peer-dependency warnings |

### M2 — Pipeline & Content (Week 5-6)

| Deliverable | Acceptance Criteria |
|-------------|---------------------|
| Content fetcher module | Fetches PR diff + metadata from GitHub; parses to structured AST-like representation |
| Script writer (LLM prompts for narration) | Generates narration script from PR content; outputs sentences with timing estimates |
| **Fact Checker** | Validates script claims against PR diff: function names exist, behavioral claims match code, terminology is correct. Runs in L1 (advisory) mode by default. |
| Scene planner (rule-based scene → timing mapping) | Maps script to scene sequence; assigns scene types based on content heuristics |
| **Logic Checker** | Validates scene plan narrative coherence: 4-arc structure present, cause/effect claims grounded in diff, scene ordering logical. Runs in L1 (advisory) mode by default. |
| TTS chunker + audio pipeline | Splits script into ≤50-token chunks; generates audio for each; stitches with FFmpeg crossfade; outputs single WAV |
| 5-Level Frame Reviewer | Per-frame analysis of rendered video: L1 integrity, L2 element bounds, L3 smoothness, L4 transitions, L5 temporal consistency. Catches jitter, overlap, frozen frames. |
| Render executor | Calls `npx remotion render` with composed `inputProps`; captures stdout/stderr; reports progress |
| E2E flow: fetch PR → **fact check** → script → **logic check** → scenes → audio → compose → render → **5-level frame review** | A single `videoforge render-pr 123` produces a valid MP4 that passes all 5 frame review levels |

### M3 — GitHub Integration (Week 7-8)

| Deliverable | Acceptance Criteria |
|-------------|---------------------|
| Webhook server (PR opened/updated) | Receives GitHub webhook payload; triggers pipeline for new/changed PRs |
| PR comment publisher | Uploads rendered video to PR as a comment; includes status link |
| `gh` CLI subprocess integration | `gh pr view`, `gh pr comment`, `gh api` all work via subprocess |
| Error handling + retry logic | Pipeline resumes from last successful phase on transient failure |
| Status tracking (`STATE.md`) | Pipeline state is persisted and queryable; partial renders can continue |
| `videoforge status` tool | Returns current pipeline phase, progress %, and any errors for a given job |

### M4 — Polish & Launch (Week 9-10)

| Deliverable | Acceptance Criteria |
|-------------|---------------------|
| Performance optimization | PR with 500 lines → video in <5 min; memory <4GB RSS |
| Installation documentation | `README.md` with quickstart in 5 steps; troubleshooting guide |
| Agent skill files (`skills/`) | Skills for Claude Code, Cursor, Copilot, Codex teach how to use VideoForge tools |
| Published to PyPI | `pip install videoforge` works; package is publicly listed |
| Published to npm (Remotion bundle) | `npx @videoforge/remotion` renders without local checkout |
| Blog post / demo video | 3-min screencast shows PR → video in one command |

## MVP Definition (v1.0)

The MVP ships at M3 and includes:

- **MCP Server** with 7+ tools: `render_pr`, `render_issue`, `render_changelog`, `fact_check_script`, `logic_check_scenes`, `status`, `list_compositions`
- **4 Composition types**: CodeWalkthrough, PRSummary, IssueExplainer, ChangelogVideo
- **8 Scene types**: TitleScene, CodeScene, DiffScene, BulletScene, ImageScene, ComparisonScene, DiagramScene, OutroScene
- **Local TTS**: All audio generated via Pocket TTS (26 voices, 12 languages)
- **Captions**: Word-level highlighting via `@remotion/captions`
- **Transitions**: Fade, slide, wipe, flip, crossfade between any scene pair
- **GitHub integration**: Webhook ingestion + PR comment publishing via `gh` CLI
- **Content validation**: Fact Checker (L1 advisory) catches hallucinated claims; Logic Checker (L1 advisory) catches narrative gaps
- **Fully offline**: No cloud API dependencies for video generation

## Post-MVP Features (Deferred)

| Feature | Reason for Deferral |
|---------|---------------------|
| Custom voice cloning | Requires model training infra; Pocket TTS does not support it |
| Real-time streaming (progressive render) | Remotion doesn't support frame streaming; would need custom renderer |
| Multi-project workspaces | Adds significant complexity to webhook routing; niche use case |
| Browser-based editor UI | MCP server is the primary interface; UI is a separate product |
| YouTube auto-upload | Adds OAuth complexity; PR comment is sufficient for v1 |
| Animated logo/branding overlay | Cosmetic; can be added via Remotion composition override |
| Whisper forced alignment for captions | Current estimation is sufficient; swap in post-MVP without API change |
| Video template marketplace | Requires ecosystem platform; premature |
| User dashboard / analytics | Server-side infra needed; MCP server is client-side by design |

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| E2E render time (500-line PR) | <5 minutes | `time videoforge render-pr 123` |
| Audio generation time | <30s per minute of video | Pipeline phase timing |
| Caption sync accuracy | <100ms drift | Automated offset measurement |
| Pipeline reliability | >95% success rate | Jobs completed / jobs started |
| MCP tool call latency (non-render) | <500ms p95 | `videoforge status` round-trip |
| Test coverage | >80% lines | `pytest --cov` |
| Install time (fresh env) | <2 minutes | `pip install videoforge` from clean venv |
| Memory during render | <4GB RSS | `ps` monitoring during render |

## Non-Goals

- **Cloud rendering service** — VideoForge is a local MCP server. No SaaS, no cloud broker, no render queues. Remotion runs on the user's machine.
- **Non-GitHub sources** — GitLab, Bitbucket, Gitea are explicitly out of scope for v1. Architecture allows adapters post-MVP.
- **YouTube/TikTok/Instagram optimization** — Output is 16:9 MP4 for developer consumption. No vertical video, no platform-specific exports.
- **Real-time / livestream** — All renders are async. No WebRTC, no live compositing, no sub-second latency.
- **Prosumer video editing** — No timeline UI, no keyframes, no multi-track audio, no color grading. Output is programmatic and deterministic.
- **Non-English narration** — Pocket TTS supports 12 languages but v1 narrates in English only. Multilingual script generation deferred.
- **Mobile app** — No Android/iOS client. MCP tools are CLI-first.

## Definition of Done

| Milestone | Done When |
|-----------|-----------|
| **M0** | All CI checks pass; `videoforge` CLI responds; Remotion renders a test frame; TTS produces valid WAV; both planning documents are committed. |
| **M1** | All 8 scenes + 4 compositions render with mock data; transitions and captions are visible in output; no Remotion peer-dependency warnings. |
| **M2** | Full pipeline runs end-to-end: `videoforge render-pr <number>` produces an MP4 with narration, captions, transitions, and diagrams from a real GitHub PR. |
| **M3** | Webhook server accepts GitHub payloads; rendered video appears as a PR comment; pipeline resumes from failures; `videoforge status` shows live state. |
| **M4** | Published on PyPI and npm; 3+ agents can call all tools; performance targets met; skill files committed; blog post published. |
