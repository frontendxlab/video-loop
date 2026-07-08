# VideoForge — Product Requirements Document

**Version:** 1.0.0  
**Status:** Draft  
**Last Updated:** 2026-07-08  
**Author:** VideoForge Product Team

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Problem Statement](#2-problem-statement)
3. [Vision Statement](#3-vision-statement)
4. [Target Audience](#4-target-audience)
5. [User Personas](#5-user-personas)
6. [User Stories](#6-user-stories)
7. [Functional Requirements](#7-functional-requirements)
   - 7.1 MCP Server Module
   - 7.2 Remotion Project Module
   - 7.3 TTS Integration Module
   - 7.4 GitHub Integration Module
   - 7.5 Pipeline Orchestration Module
   - 7.6 Asset Generation Module
   - 7.7 Review / QA Module
8. [Non-Functional Requirements](#8-non-functional-requirements)
9. [Constraints](#9-constraints)
10. [Out of Scope](#10-out-of-scope)
11. [Success Metrics](#11-success-metrics)
12. [Release Criteria](#12-release-criteria)
13. [Appendix: Scene Types Reference](#13-appendix-scene-types-reference)
14. [Appendix: Scene Transitions Reference](#14-appendix-scene-transitions-reference)
15. [Appendix: Compositions Reference](#15-appendix-compositions-reference)
16. [Appendix: Pipeline Phases Reference](#16-appendix-pipeline-phases-reference)

---

## 1. Product Overview

VideoForge is an MCP-native automated video generation pipeline that transforms GitHub content — pull requests, issues, changelogs, and repository code — into developer-focused explainer videos. It operates as a Model Context Protocol (MCP) server exposing a suite of tools that any MCP-compatible AI agent (Claude Code, Cursor, Windsurf, GitHub Copilot, etc.) can invoke. The system ingests GitHub content, researches context, writes a script, plans scenes, generates assets (text-to-speech audio, images, diagrams), composes a Remotion video, renders it with Chromium, and delivers the final MP4 file — all through a single MCP tool call. VideoForge is designed to be lightweight, API-first, fully local, and agent-agnostic, enabling seamless integration into developer workflows, CI/CD pipelines, and documentation systems.

---

## 2. Problem Statement

Software development generates enormous amounts of textual content — pull requests, code reviews, issue discussions, changelogs, and architectural decision records — that are poorly suited to text-only consumption. Video content is proven to increase comprehension and engagement, yet producing explainer videos for code changes remains prohibitively time-consuming and skill-intensive.

**Key pain points:**

| Pain Point | Description |
|---|---|
| **Manual video production is slow** | Creating a 3-minute code walkthrough video takes 2-6 hours of scripting, recording, editing, and rendering. |
| **Text fatigue in code reviews** | PR descriptions, issue comments, and changelogs are skipped or skimmed, leading to missed context and slower reviews. |
| **No bridge between code and video** | Existing video tools (OBS, ScreenFlow, DaVinci Resolve) are designed for human presenters, not code. No tool reads GitHub content and produces a video automatically. |
| **Agent lock-in** | Every existing AI video tool is tied to a single agent (Claude Code). Teams using different agents cannot share video generation capabilities. |
| **No MCP-native video pipeline** | The MCP ecosystem has no video generation server. Developers who want AI-generated videos must context-switch to external tools. |
| **Code walkthroughs don't scale** | Open source maintainers review dozens of PRs weekly. Creating walkthrough videos for each is impossible, yet each one would accelerate review and onboarding. |
| **CI/CD has no video output** | Pipelines produce text logs, test reports, and build artifacts — but never a visual summary of what changed and why. |

---

## 3. Vision Statement

To make video a first-class output of the software development lifecycle — as automatic as linting, as accessible as markdown, and as native as code — by giving every AI agent the power to generate professional explainer videos from GitHub content with a single tool call.

---

## 4. Target Audience

| Segment | Description |
|---|---|
| **Individual Developers** | Developers who want to create code walkthroughs, document their work, or explain PRs to their team without manual video editing. |
| **Engineering Teams** | Teams that want to include video summaries in their code review workflow to reduce context-switching and speed up reviews. |
| **Open Source Maintainers** | Maintainers reviewing community contributions who need to communicate feedback, explain merges, and onboard contributors at scale. |
| **DevOps / Platform Engineers** | Engineers building CI/CD pipelines who want video artifacts generated automatically on PR merge or release. |
| **Technical Content Creators** | Developers who produce tutorial content, course material, or documentation videos from real codebases. |
| **AI Agent Users** | Anyone using MCP-compatible agents who wants to generate video from code without leaving their agent interface. |

---

## 5. User Personas

### Persona 1: Priya — Full-Stack Developer

| Attribute | Detail |
|---|---|
| **Role** | Senior full-stack developer at a mid-size SaaS company |
| **Team size** | 8 engineers |
| **Pain point** | Spends 3+ hours per week writing detailed PR descriptions that team members still skim. Wishes she could create quick walkthrough videos. |
| **Technical level** | High — comfortable with CLI, Node.js, Python, Docker |
| **Workflow** | GitHub → VS Code → Terminal → Slack |
| **Agent usage** | Uses Claude Code and Cursor daily |
| **Goal** | Reduce PR review cycle time by 40% by attaching 90-second walkthrough videos to complex PRs. |
| **Quote** | "I spend more time explaining my code changes than writing them. I need a way to record a walkthrough without recording a walkthrough." |

### Persona 2: Marcus — Engineering Manager

| Attribute | Detail |
|---|---|
| **Role** | Engineering manager at a fintech startup |
| **Team size** | 12 engineers across 3 squads |
| **Pain point** | Cannot stay on top of all PRs across squads. Relies on PR summaries but often misses context. |
| **Technical level** | Medium — comfortable with GitHub, light on CLI |
| **Workflow** | GitHub → Linear → Slack → Zoom |
| **Agent usage** | Uses Claude Code occasionally |
| **Goal** | Receive automated video summaries of cross-team PRs before standup. |
| **Quote** | "I need to review 20 PRs before our morning standup. A 60-second video per PR would save me an hour a day." |

### Persona 3: Aisha — Open Source Maintainer

| Attribute | Detail |
|---|---|
| **Role** | Core maintainer of a popular open-source framework (50K+ GitHub stars) |
| **Team size** | 5 core maintainers, 300+ contributors |
| **Pain point** | Reviews 10-20 community PRs weekly. Providing thorough feedback on each is exhausting. Contributor onboarding is entirely text-based. |
| **Technical level** | Very high |
| **Workflow** | GitHub Issues → PRs → Discord → GitHub Discussions |
| **Agent usage** | Heavy Claude Code user |
| **Goal** | Auto-generate contributor onboarding walkthroughs and merge-summary videos for the community. |
| **Quote** | "I have 300 contributors and only 5 maintainers. I cannot personally walk everyone through our contribution guide, but a video could." |

### Persona 4: CI/CD Pipeline (Non-Human)

| Attribute | Detail |
|---|---|
| **Role** | Automated build system (GitHub Actions, GitLab CI, Jenkins) |
| **Trigger** | On PR merge, tag push, or release |
| **Constraint** | Must complete within CI job timeout (typically 60 minutes). Must produce a downloadable artifact. |
| **Goal** | Generate a changelog video on every release and upload it to the release assets. |
| **Quote** | "I am a pipeline. I have no eyes. But my human operators do. Give them video." |

### Persona 5: Elena — Technical Content Creator

| Attribute | Detail |
|---|---|
| **Role** | Developer educator, YouTube channel (50K subs), course creator |
| **Pain point** | Spends days scripting, recording, and editing tutorial videos that walk through real GitHub repos. |
| **Technical level** | High |
| **Workflow** | GitHub → OBS → DaVinci Resolve → YouTube Studio |
| **Agent usage** | Light — mostly manual tools |
| **Goal** | Generate first-draft tutorial videos from any GitHub repo in minutes, then polish manually. |
| **Quote** | "I could triple my output if I had a 'repo to first draft' pipeline. Right now I spend 80% of my time on what could be automated." |

---

## 6. User Stories

### GitHub Integration

| ID | Story |
|---|---|
| US-001 | As a developer, I want to generate a video from a GitHub PR URL so that I can attach a walkthrough to my pull request without manual recording. |
| US-002 | As a developer, I want to generate a video from a GitHub issue URL so that I can explain the issue context, reproduction steps, and proposed solution visually. |
| US-003 | As a maintainer, I want to generate a changelog video from a GitHub release or tag so that my community can see what changed in a new version. |
| US-004 | As a developer, I want to generate a video from a GitHub repository path so that I can create tutorial walkthroughs of any codebase. |
| US-005 | As a developer, I want the system to fetch the PR diff, description, comments, and linked issues automatically so that the video has full context. |

### Scripting & Storyboarding

| ID | Story |
|---|---|
| US-006 | As a developer, I want the system to automatically generate a narrative script from the GitHub content so that I don't have to write it myself. |
| US-007 | As a developer, I want to review and edit the generated script before the video renders so that I can correct tone, accuracy, or emphasis. |
| US-008 | As a developer, I want to choose between multiple script tones (professional, casual, technical) so that the video matches my audience. |
| US-009 | As a developer, I want the system to automatically plan scenes (title, code, diff, bullets, outro) from the script so that the video has visual structure. |

### Video Generation

| ID | Story |
|---|---|
| US-010 | As a developer, I want the generated video to include syntax-highlighted code with line-focus animations so that viewers can follow the code easily. |
| US-011 | As a developer, I want diff scenes to show side-by-side before/after code with red/green highlighting so that viewers understand what changed. |
| US-012 | As a developer, I want the video to include text-to-speech narration with one of 26+ voices so that the video has a professional voiceover. |
| US-013 | As a developer, I want the TTS voice to be consistent across all scenes in a single video so that the narration sounds natural. |
| US-014 | As a developer, I want diagrams (architecture, sequence, flow) to be auto-generated from code context so that architectural changes are explained visually. |

### Audio & Captions

| ID | Story |
|---|---|
| US-015 | As a developer, I want word-level caption highlighting synchronized with narration so that viewers can follow along even without audio. |
| US-016 | As a developer, I want to choose between 12+ available languages for TTS narration so that I can create videos for international audiences. |
| US-017 | As a developer, I want background music to be auto-selected and mixed with narration so that the video feels polished without manual audio editing. |

### Transitions & Effects

| ID | Story |
|---|---|
| US-018 | As a developer, I want configurable scene transitions (fade, slide, wipe, flip, crossZoom, clockWipe, glitch, morph) so that the video has visual variety. |
| US-019 | As a developer, I want bullet points to animate in with staggered timing synchronized to narration so that the visual pacing matches the voiceover. |

### Pipeline & Workflow

| ID | Story |
|---|---|
| US-020 | As a developer, I want the video generation to run asynchronously so that I can continue working while the video is being rendered. |
| US-021 | As a developer, I want to receive a webhook notification when the video is complete so that I don't have to poll for status. |
| US-022 | As a developer, I want the system to work with any MCP-compatible agent (Claude Code, Cursor, Windsurf, Copilot) so that I am not locked into one tool. |
| US-023 | As a DevOps engineer, I want to trigger video generation from a GitHub Action so that video artifacts are created automatically on merge. |
| US-024 | As a developer, I want to generate multiple videos in parallel so that I can batch-process a backlog of PRs. |

### Review & Quality

| ID | Story |
|---|---|
| US-025 | As a developer, I want to preview the scene plan before rendering so that I can reorder, add, or remove scenes. |
| US-026 | As a developer, I want the video to include a watermark with the repo name and PR number so that the context is clear in the final output. |
| US-027 | As a developer, I want to customize the color scheme and branding so that the video matches my project or company style guide. |
| US-028 | As a developer, I want the system to retry failed render jobs automatically so that transient Chromium failures don't lose my work. |

### Content Validation

| ID | Story |
|---|---|
| US-035 | As a developer, I want the script to be automatically fact-checked against the source PR diff so that the narration doesn't make incorrect claims about code behavior. |
| US-036 | As a developer, I want the scene plan to be logic-checked for narrative coherence so that the video tells a story that makes sense step by step. |

### Voice & Audio

| ID | Story |
|---|---|
| US-029 | As a developer, I want to clone a voice from an audio sample so that videos can use a custom voice for branded content. |
| US-030 | As a developer, I want to preview available voices before selecting one so that I can choose the right tone for my video. |
| US-031 | As a developer, I want to save and manage custom cloned voices so that I can reuse them across videos. |

### Output & Delivery

| ID | Story |
|---|---|
| US-032 | As a developer, I want the final video to be output as MP4 (H.264) so that it plays on all devices and platforms. |
| US-033 | As a developer, I want the video file path returned as an MCP tool result so that my agent can present it or upload it. |
| US-034 | As a developer, I want the video to automatically upload to the PR as a comment or artifact so that it's immediately visible to reviewers. |

---

## 7. Functional Requirements

### 7.1 MCP Server Module

The MCP server is the entry point for all agent interactions. It exposes tools and resources that any MCP-compatible client can invoke.

#### 7.1.1 MCP Tools

| Tool Name | Input | Output | Description |
|---|---|---|---|
| `generate_from_pr` | `pr_url: string`, `voice?: string`, `language?: string`, `transitions?: string[]`, `branding?: object` | `job_id: string`, `status_url: string` | Initiates a full video generation pipeline from a GitHub pull request URL. Returns immediately with a job ID for async progress tracking. |
| `generate_from_issue` | `issue_url: string`, `voice?: string`, `language?: string`, `transitions?: string[]`, `branding?: object` | `job_id: string`, `status_url: string` | Initiates video generation from a GitHub issue URL. |
| `generate_from_repo` | `repo_url: string`, `path?: string`, `voice?: string`, `language?: string`, `transitions?: string[]`, `branding?: object` | `job_id: string`, `status_url: string` | Initiates video generation from a repository path or file. |
| `generate_changelog` | `repo_url: string`, `from_tag: string`, `to_tag?: string`, `voice?: string`, `language?: string` | `job_id: string`, `status_url: string` | Generates a changelog video from git tags or releases. |
| `get_job_status` | `job_id: string` | `status: string`, `progress: number`, `current_phase: string`, `eta_seconds: number` | Returns the current status of a video generation job. |
| `get_job_result` | `job_id: string` | `video_path: string`, `duration_seconds: number`, `scenes: number`, `file_size_bytes: number` | Returns the result of a completed job, including the video file path. |
| `cancel_job` | `job_id: string` | `success: boolean` | Cancels an in-progress video generation job. |
| `preview_script` | `source_url: string`, `tone?: string` | `script: string`, `scenes: object[]` | Generates a script and scene plan without rendering, allowing user review before committing to a full render. |
| `update_script` | `job_id: string`, `script: string`, `scenes?: object[]` | `success: boolean` | Allows the user to modify the script or scene plan before rendering proceeds. |
| `list_voices` | — | `voices: object[]` | Returns all available predefined and saved voices with metadata (name, language, gender, preview URL). |
| `list_compositions` | — | `compositions: object[]` | Returns available composition templates (CodeWalkthrough, PRSummary, IssueExplainer, ChangelogVideo) with descriptions. |
| `get_pipeline_phases` | `job_id: string` | `phases: object[]` | Returns granular phase-by-phase progress of a job. |
| `set_webhook` | `url: string`, `events?: string[]` | `success: boolean` | Registers a webhook URL to receive job completion and error notifications. |
| `generate_batch` | `jobs: object[]`, `concurrency?: number` | `batch_id: string` | Enqueues multiple video generation jobs for batch processing with configurable concurrency. |

#### 7.1.2 MCP Resources

| Resource URI | Description |
|---|---|
| `videoforge://jobs/{job_id}` | Full job detail including script, scene plan, asset paths, and result. |
| `videoforge://voices` | Complete voice catalog with preview URLs and metadata. |
| `videoforge://compositions` | Composition template definitions with default scene sequences. |
| `videoforge://pipeline-phases` | Phase definitions and descriptions for the generation pipeline. |
| `videoforge://branding-templates` | Saved branding/theme configurations for reuse. |

#### 7.1.3 MCP Prompts

| Prompt ID | Description |
|---|---|
| `generate-video` | Interactive prompt guiding the user through video generation with voice/transition/branding choices. |
| `review-script` | Prompt for reviewing and editing the generated script before rendering. |

### 7.2 Remotion Project Module

The Remotion project is the video rendering engine. It defines compositions, scenes, transitions, and all visual components.

#### 7.2.1 Compositions

| Composition | Scene Sequence | Input Data |
|---|---|---|
| **CodeWalkthrough** | Title → Diff (1-N) → Bullets → Outro | PR diff, description, comments |
| **PRSummary** | Title → Code → Outro | PR title, description, key files |
| **IssueExplainer** | Title → Bullets → Code → Outro | Issue title, body, reproduction steps |
| **ChangelogVideo** | Title → N × (PR Entry) → Outro | Release notes, merged PRs, contributors |

#### 7.2.2 Scene Components

Each scene is a React component that accepts standardized props:

```
interface SceneProps {
  data: Record<string, any>;
  style: SceneStyle;
  transition: TransitionConfig;
  audio: AudioTrack;
  captions: Caption[];
  durationInFrames: number;
}
```

##### TitleScene
- Props: `title`, `subtitle`, `logo?`, `date?`
- Animation: Title slides up from bottom, subtitle fades in with 15-frame stagger
- Background: Gradient or solid color from branding config
- Audio: TTS narration of title/subtitle
- Duration: 4-8 seconds

##### CodeScene
- Props: `code`, `language`, `fileName?`, `focusLines?: number[]`, `theme`
- Technology: Shiki syntax highlighter for tokenization
- Animation: Lines appear with typewriter effect; focus lines highlighted with glow
- Audio: TTS narration describing the code
- Duration: 10-30 seconds

##### DiffScene
- Props: `beforeCode`, `afterCode`, `language`, `fileName?`, `hunkHeaders?`
- Layout: Side-by-side with animated vertical divider
- Styling: Red background for removed lines, green for added lines, gray for unchanged
- Animation: Lines slide in from left (before) and right (after)
- Audio: TTS narration explaining the change
- Duration: 10-25 seconds

##### BulletScene
- Props: `items: string[]`, `title?`, `layout: 'left' | 'center'`
- Animation: Items stagger in from left with opacity + slide, synchronized to TTS word timestamps
- Audio: TTS reading each bullet point
- Duration: 5-20 seconds (depends on item count)

##### ImageScene
- Props: `imageUrl`, `caption?`, `effect: 'kenBurns' | 'none'`
- Animation: Ken Burns slow zoom/pan
- Audio: TTS describing the image
- Duration: 4-10 seconds

##### ComparisonScene
- Props: `leftContent`, `rightContent`, `leftLabel`, `rightLabel`, `type: 'image' | 'code'`
- Layout: 50/50 split with animated vertical divider
- Animation: Divider sweeps from center to reveal both sides
- Audio: TTS explaining the comparison
- Duration: 8-15 seconds

##### DiagramScene
- Props: `diagramType`, `data`, `animated: boolean`
- Technology: shetty4l/diagrams npm package
- Supported types: architecture, sequence, flow, entity-relationship, class, component, network, Gantt, mindmap
- Animation: Elements appear with staggered transitions, edges draw in
- Audio: TTS explaining the architecture
- Duration: 10-25 seconds

##### OutroScene
- Props: `title`, `ctaText?`, `ctaUrl?`, `watermark`, `sponsors?`
- Animation: Content fades in from center, watermark slides up from bottom
- Audio: TTS with closing remarks
- Duration: 5-8 seconds

#### 7.2.3 Scene Transitions

| Transition ID | Config Parameters | Default Duration |
|---|---|---|
| `fade` | `durationInFrames: number` | 15 frames (0.5s at 30fps) |
| `slide-left` | `durationInFrames: number` | 20 frames |
| `slide-up` | `durationInFrames: number` | 20 frames |
| `wipe-left` | `durationInFrames: number`, `division?: number` | 15 frames |
| `flip` | `durationInFrames: number` | 25 frames |
| `crossZoom` | `durationInFrames: number` | 30 frames |
| `clockWipe` | `durationInFrames: number` | 20 frames |
| `glitch` | `durationInFrames: number`, `intensity?: number` | 10 frames |
| `morph` | `durationInFrames: number`, `easing?: string` | 25 frames |
| `none` | — | 0 frames (cut) |
| `push-left` | `durationInFrames: number` | 20 frames |
| `zoom-in` | `durationInFrames: number` | 25 frames |

Transitions are implemented using `@remotion/transitions` (fade, slide, wipe, flip, clockWipe, crossZoom) and custom components (glitch, morph, push-left, zoom-in).

#### 7.2.4 Caption System

- **Source**: Word-level timestamps from TTS engine or Whisper forced alignment
- **Format**: WebVTT-compatible word segments
- **Display**: Each word highlights as it is spoken
- **Styling**: Configurable highlight color, font, size, position (top/bottom)
- **Implementation**: `@remotion/captions` for rendering
- **Accuracy Target**: ±100ms word boundary accuracy (estimated), ±20ms (Whisper pipeline)

#### 7.2.5 Audio Track Management

| Track Type | Source | Mix Strategy |
|---|---|---|
| **Narration** | Pocket TTS | Primary track, centered stereo |
| **Background Music** | Asset cascade (AI-gen → stock → none) | Duck under narration by -12dB during speech, -18dB between speech |
| **Sound Effects** | Procedural generation | Per-scene optional, mixed at -6dB relative to narration |
| **Silence Padding** | FFmpeg | Trimmed to scene boundaries, 200ms crossfade between scenes |

Audio mixing is performed post-render via FFmpeg rather than in-Composition to avoid Remotion audio latency issues and allow independent adjustment.

### 7.3 TTS Integration Module

The TTS module wraps the existing Pocket TTS MCP server and provides sentence-level segmentation for natural-sounding narration.

#### 7.3.1 Voice Management

| Requirement | Description |
|---|---|
| Predefined Voices | Access to all 26 predefined voices from Pocket TTS with metadata (name, language, gender, speed) |
| Saved Voices | CRUD operations for user-saved voices |
| Voice Cloning | Ability to clone a voice from a provided audio sample (20-60 seconds of clean speech) |
| Language Support | 12 language variants: English (US, UK, AU, IN), French, German, Spanish, Italian, Portuguese, Japanese, Korean, Chinese |
| Voice Preview | Short audio preview (5 seconds) for each voice before selection |
| Voice Persistence | Cloned and saved voices persist across server restarts |

#### 7.3.2 Segmentation & Synthesis

| Requirement | Specification |
|---|---|
| Segmentation Strategy | Sentence-level splitting with ≤50 token chunks for natural pacing |
| Punctuation Boundaries | Split on period, question mark, exclamation point, semicolon, colon |
| Maximum Chunk Size | 50 tokens (configurable) with soft break at nearest sentence boundary |
| Minimum Chunk Size | 2 words (to avoid unnatural single-word utterances) |
| Concurrency | Up to 4 parallel TTS synthesis requests |
| Output Format | 24kHz 16-bit mono WAV (matching Pocket TTS output spec) |
| Performance Target | ≤0.5x real-time on CPU with GPU acceleration |

#### 7.3.3 Word-Level Timestamps

| Requirement | Specification |
|---|---|
| Primary Method | Estimation algorithm: align characters to audio duration with per-word timing |
| Fallback Method | Linear interpolation for short chunks (<10 tokens) |
| Future Method | Whisper.cpp forced alignment for ±20ms accuracy |
| Output Format | Array of `{ word: string, startMs: number, endMs: number }` |
| Accuracy Target | ±100ms with estimation, ±20ms with Whisper |
| Storage | Embedded in scene plan JSON alongside audio file path |

### 7.4 GitHub Integration Module

The GitHub module handles fetching content from GitHub URLs and preparing it for the pipeline.

#### 7.4.1 Content Fetching

| Content Type | Data Fetched | API Endpoints Used |
|---|---|---|
| **Pull Request** | PR title, description, diff, changed files list, comments, review comments, linked issues, author, labels, milestone | `/repos/{owner}/{repo}/pulls/{number}`, `/repos/{owner}/{repo}/pulls/{number}/files`, `/repos/{owner}/{repo}/pulls/{number}/comments`, `/repos/{owner}/{repo}/pulls/{number}/reviews` |
| **Issue** | Issue title, body, comments, labels, assignees, linked PRs, milestone | `/repos/{owner}/{repo}/issues/{number}`, `/repos/{owner}/{repo}/issues/{number}/comments` |
| **Repository File** | File content, language detection, line count, last commit info | `/repos/{owner}/{repo}/contents/{path}`, `/repos/{owner}/{repo}/commits?path={path}` |
| **Release / Tag** | Release notes, tag comparison, commit log, contributor list, merged PRs | `/repos/{owner}/{repo}/releases/tags/{tag}`, `/repos/{owner}/{repo}/compare/{base}...{head}` |
| **Repository Tree** | Directory structure, file types, primary language, readme | `/repos/{owner}/{repo}/git/trees/{branch}`, `/repos/{owner}/{repo}/readme` |

#### 7.4.2 Authentication

| Requirement | Specification |
|---|---|
| Anonymous Access | 60 requests/hour (GitHub unauthenticated limit) — sufficient for development |
| Token-Based Access | Personal Access Token (classic or fine-grained) for production use — 5,000 requests/hour |
| Token Configuration | Via environment variable `GITHUB_TOKEN` or MCP server config |
| Rate Limit Handling | Automatic exponential backoff and retry with `Retry-After` header respect |

#### 7.4.3 Webhook Support

| Requirement | Specification |
|---|---|
| Inbound Webhook | Receive GitHub webhook events (pull_request.opened, issues.opened, release.published) |
| Auto-Trigger | Automatically initiate video generation when configured webhook events fire |
| GitHub App | Future consideration for GitHub App integration with checks API |
| Timeout Handling | Respond to GitHub webhook within 10 seconds (GitHub timeout); initiate async job, return 202 immediately |

### 7.5 Pipeline Orchestration Module

The pipeline orchestrator manages the end-to-end video generation flow across all phases.

#### 7.5.1 Pipeline Phases

| Phase | Steps | Description |
|---|---|---|
| **INGEST** | (1) Parse source URL → (2) Fetch content from GitHub → (3) Normalize into intermediate format → (4) Store raw content | Fetches and normalizes all GitHub content into a pipeline-neutral format. |
| **RESEARCH** | (1) Analyze diff/issue content → (2) Fetch related context (linked issues, related files) → (3) Identify key changes and impact → (4) Generate research summary | Enriches the raw content with additional context from the repository and linked resources. |
| **SCRIPT** | (1) Generate narrative script from research + content → (2) Apply tone/style configuration → (3) Segment into scenes → (4) Return for user preview (if review mode) | Produces the narrated script and initial scene segmentation. |
| **SCENE PLAN** | (1) Map script segments to scene types → (2) Assign transitions → (3) Determine timing/duration → (4) Generate scene plan JSON → (5) Return for user approval | Creates the detailed shot-by-shot plan for the video. |
| **ASSET GEN** | (1) Generate TTS audio per scene → (2) Compute word timestamps → (3) Generate/select images → (4) Generate diagrams → (5) Select background music → (6) Cache all assets | Produces all media assets needed for rendering. |
| **COMPOSE** | (1) Build Remotion input props from scene plan + assets → (2) Resolve composition template → (3) Generate captions from word timestamps → (4) Configure transitions | Composes the Remotion project with all data and assets. |
| **RENDER** | (1) Launch Chromium via @remotion/renderer → (2) Render video with audio tracks → (3) Monitor progress → (4) Handle errors and retries | Renders the video using Remotion's Chromium-based renderer. |
| **REVIEW** | (1) Mix audio tracks via FFmpeg → (2) Verify output integrity → (3) Generate thumbnail → (4) Check file size → (5) Pass/fail QA | Post-processes and validates the rendered video. |
| **PUBLISH** | (1) Copy to output directory → (2) Return file path in MCP result → (3) Trigger webhook notification → (4) Upload to GitHub (optional) → (5) Cleanup temp files | Delivers the final video and notifies the caller. |

#### 7.5.2 Job Management

| Requirement | Specification |
|---|---|
| Job ID Format | UUID v4 |
| Job Queue | In-memory queue with SQLite-backed persistence for crash recovery |
| Concurrency | Default 2 concurrent jobs, configurable up to 8 |
| Job Timeout | 30 minutes max per job |
| Cancellation | Graceful cancellation at phase boundaries (current phase completes, next phase not started) |
| Retry Policy | 3 retries on transient failures (Chromium crash, network timeout, rate limit) with exponential backoff |
| Webhook Delivery | POST to registered URL with job result payload; 3 retry attempts with 60-second interval |

#### 7.5.3 Progress Tracking

```
{
  "job_id": "uuid",
  "status": "rendering",
  "overall_progress": 0.65,
  "eta_seconds": 180,
  "current_phase": "RENDER",
  "phase_progress": {
    "ingest": { "status": "completed", "duration_ms": 3400 },
    "research": { "status": "completed", "duration_ms": 8200 },
    "script": { "status": "completed", "duration_ms": 5100 },
    "scene_plan": { "status": "completed", "duration_ms": 2300 },
    "asset_gen": { "status": "completed", "duration_ms": 45000 },
    "compose": { "status": "completed", "duration_ms": 1200 },
    "render": { "status": "in_progress", "duration_ms": 23000, "frames_done": 450, "frames_total": 5400 },
    "review": { "status": "pending" },
    "publish": { "status": "pending" }
  }
}
```

### 7.6 Asset Generation Module

The asset generation module produces all non-TTS media assets including images, diagrams, and audio.

#### 7.6.1 Image Generation

| Requirement | Specification |
|---|---|
| Primary Source | AI image generation (if configured — DALL-E, Stable Diffusion, etc.) |
| Secondary Source | Stock image search (Unsplash API, Pexels API) |
| Fallback | Code-only slides with gradient backgrounds (no images required) |
| Caching | Generated images cached by content hash to avoid regeneration |
| Format | 1920×1080, RGB, JPEG at 90% quality |
| Ken Burns Effect | Applied in-Composition with CSS transforms (zoom: 1.0 → 1.15, pan: configurable) |

#### 7.6.2 Diagram Generation

| Requirement | Specification |
|---|---|
| Engine | shetty4l/diagrams rendered inside Remotion |
| Diagram Types | Architecture, Sequence, Flow, Entity-Relationship, Class, Component, Network, Gantt, Mindmap |
| Data Source | Extracted from code analysis (function calls, imports, file structure) or LLM-generated |
| Animation | Elements stagger in, edges draw with trace animation |
| Styling | Matches video branding (colors, fonts, line styles) |
| Fallback | baoyu-diagram SVG generation if shetty4l/diagrams lacks a needed type |

#### 7.6.3 Background Music

| Requirement | Specification |
|---|---|
| Source Cascade | (1) User-provided track → (2) AI-generated music → (3) Built-in royalty-free tracks → (4) None |
| Library | 10-20 built-in royalty-free tracks across categories: cinematic, tech, ambient, corporate, upbeat |
| Selection Logic | Auto-selected based on video tone (professional → ambient, exciting → upbeat, technical → tech) |
| Looping | Tracks loop seamlessly for videos longer than track duration |
| Mixing | Duck narration ducking via FFmpeg loudnorm + sidechain compression |

#### 7.6.4 Asset Cascade Strategy

```
Level 1: AI-generated  → Best quality, requires API keys, extra latency
Level 2: Stock/library  → Good quality, requires internet, minimal latency
Level 3: Code-only      → Always available, zero external deps, consistent style
```

The cascade selects Level 1 if available and configured, falls back to Level 2 if Level 1 fails or is unavailable, and always has Level 3 as the guaranteed fallback.

### 7.7 Content Validation Module

The content validation module runs two checks before asset generation begins. Catching errors at the text stage avoids wasting TTS generation and Remotion rendering on invalid content.

#### 7.7.1 Fact Checker

The Fact Checker validates the script's factual accuracy against the source content (PR diff, issue body, code files).

| Check | What It Validates | Pass/Fail Criteria |
|---|---|---|
| **Function/API exist** | Every function, class, or API name mentioned in the script exists in the source code or diff | 100% of named references resolve to actual code elements |
| **Behavior accuracy** | Claims about what code does match the actual code (e.g., "this function validates tokens" matches code that contains `validate`/`verify` logic on tokens) | ≥90% of behavioral claims match; mismatches flagged for human review |
| **Terminology correctness** | Technical terms are used correctly (e.g., "JWT token" vs "session cookie", "GET request" vs "POST request") | All terms match source context; incorrect terms flagged with correction |
| **Change attribution** | Claims about "added", "removed", "modified" lines match actual diff status | 100% accurate per file |

**Failure behavior**: Fact Checker produces a report of all claims found, their verification status, and suggested corrections. The pipeline can be configured to:
- **L1 (Advisory)**: Report is logged, pipeline continues with warnings
- **L2 (Blocking)**: Pipeline halts, returns report to user for manual correction

#### 7.7.2 Logic Checker

The Logic Checker validates the scene plan's narrative coherence and logical flow.

| Check | What It Validates | Pass/Fail Criteria |
|---|---|---|
| **Narrative arc** | The scene sequence has a coherent arc: context → problem → solution → impact | All 4 phases present in some form |
| **Cause/Effect** | Claims about cause and effect match the code changes (e.g., "adding caching reduces latency" is only validated if the diff actually adds caching) | All cause/effect claims grounded in diff |
| **Scene ordering** | Scenes are in a logical order (code is introduced before it's modified, test comes after implementation) | No scene refers to content not yet introduced |
| **Pacing** | Scene durations are proportional to content complexity (complex topics get more time, simple transitions are quick) | No scene is <2s or >30s unless explicitly configured |

**Failure behavior**: Logic Checker produces scene-by-scene feedback. Same L1/L2 configuration as Fact Checker.

#### 7.7.3 Integration Point

```
SCRIPT → Fact Checker → (pass/fail) → SCENE PLAN → Logic Checker → (pass/fail) → ASSET GEN
                    ↑                                ↑
              Source diff                        Source diff + script
```

Both validators receive the source content (PR diff, issue body) alongside the generated content they are checking. This lets them compare claims against ground truth.

### 7.8 Review / QA Module

The review module validates the rendered video at two levels: per-frame visual analysis (5-Level Frame Review) and global quality metrics.

#### 7.8.1 5-Level Frame Review

Every frame of the rendered video is analyzed through 5 progressive levels of checks. A frame must pass Level N before Level N+1 is evaluated. This catches animation jitter, element overlap, frozen frames, and transition artifacts that global metrics miss.

| Level | Name | What It Detects | Method |
|---|---|---|---|
| **L1** | Frame Integrity Check | Corrupt frames, black frames, frozen frames (same pixels for >1s), dropped frames | FFmpeg `blackdetect` + `freezedetect` filters; pixel-wise diff between consecutive frames |
| **L2** | Element Boundary Check | Text or UI elements clipped by viewport edges, elements overlapping with >30% bounding-box intersection, elements with zero opacity at expected-visible frames | Extract frame regions via FFmpeg crop; measure bounding-box intersection-over-union (IoU) for known element positions from Remotion render metadata |
| **L3** | Animation Smoothness Check | Position jitter (element jumps >3px between consecutive frames with no easing curve), opacity flicker (opacity oscillates every frame), scale oscillation (scale value alternates frame-to-frame) | Compute frame-to-frame deltas for known animated elements; apply low-pass filter to detect high-frequency noise in position/opacity/scale curves |
| **L4** | Transition Completeness Check | Transitions that don't finish (easing clipped before 1.0), scenes that overlap (both entering and exiting scenes visible beyond transition duration), abrupt cut where transition was expected | Verify transition duration matches spec (±1 frame); check alpha blending at transition midpoint; detect hard cuts where transition type != "none" |
| **L5** | Temporal Consistency Check | Elements that disappear and reappear (missing for >1 frame then return), caption mismatch (highlighted word doesn't match audio at that frame), scene content mismatch (narration describes "code" but frame shows "image") | Track element presence across consecutive frames via pixel-change masks; compare caption timing against frame-accurate word schedule from inputProps; cross-reference scene type in inputProps against OCR-detected content type |

**Failure Behavior:**
- **L1 failure** (corrupt/frozen frame): Video is rejected. Pipeline restarts render.
- **L2 failure** (overlap/clip): Video is flagged for human review. If overlap >5% of frames, rejected.
- **L3 failure** (jitter/flicker): Warnings generated with specific frame ranges. Acceptable unless >10% of animated frames are affected.
- **L4 failure** (incomplete transition): Transition flagged with exact frame range. Pipeline can regenerate with corrected timing.
- **L5 failure** (temporal inconsistency): Caption/scene mismatches reported. Pipeline reverts to scene planning phase for correction.

#### 7.8.2 Automated QA Checks

The QA module generates a structured report:

```
{
  "passed": true,
  "checks": {
    "file_integrity": { "status": "passed" },
    "duration_accuracy": { "status": "passed", "expected": 185.4, "actual": 186.1 },
    "audio_sync": { "status": "passed" },
    "caption_coverage": { "status": "passed", "coverage_percent": 97.3 },
    "resolution": { "status": "passed", "actual": "1920x1080" },
    "black_frames": { "status": "passed", "percent_black": 0.02 },
    "silent_sections": { "status": "passed", "longest_gap_ms": 2100 },
    "audio_level": { "status": "passed", "lufs": -19.2 },
    "file_size": { "status": "passed", "size_mb": 42.3 }
  },
  "warnings": [
    "3 captions had estimated timestamps >150ms off"
  ],
  "thumbnail_path": "/tmp/videoforge/abc123/thumbnail.jpg"
}
```

#### 7.7.3 User Review Points

| Review Point | When | Action |
|---|---|---|
| **Script Review** | After SCRIPT phase | User can edit script text and re-segment scenes |
| **Scene Plan Review** | After SCENE PLAN phase | User can reorder, add, remove scenes; change transitions |
| **Voice Selection** | Before ASSET GEN | User can preview and change voice selection |
| **Post-Render Review** | After RENDER phase | User can view video and approve or request re-render |

---

## 8. Non-Functional Requirements

### 8.1 Performance

| Requirement | Target | Measurement Method |
|---|---|---|
| **Pipeline Latency (simple PR)** | ≤120 seconds | End-to-end timing from MCP tool call to video file path return |
| **Pipeline Latency (complex PR)** | ≤600 seconds | End-to-end timing for large diffs (50+ files, 5000+ lines changed) |
| **TTS Latency** | ≤0.5× real-time on CPU | Audio duration / synthesis wall time |
| **Render Latency** | ≤2× real-time at 30fps 1080p | Video duration / render wall time |
| **TTS Model Load Time** | ≤60 seconds (cold start) | Time from server start to first synthesis ready |
| **TTS Model Load Time** | ≤1 second (warm) | Time from request to synthesis when model is already loaded |
| **MCP Tool Response** | ≤500ms (non-render tools) | Round-trip for get_job_status, list_voices, etc. |
| **Concurrent Jobs** | ≥2 simultaneous pipelines | With stable memory usage (<4GB per job) |
| **Webhook Delivery** | ≤5 seconds from job completion | Time from job done to POST delivery |

### 8.2 Security

| Requirement | Description |
|---|---|
| **No Secret Exposure** | GitHub tokens, API keys, and configuration secrets must never appear in logs, error messages, or MCP tool outputs. |
| **Input Validation** | All URL inputs must be validated against allowed domains (github.com) and sanitized to prevent path traversal. |
| **File Isolation** | Generated assets and output videos must be confined to designated temp directories with no access to system paths. |
| **Resource Limits** | Maximum file size per generated asset: 50MB. Maximum total pipeline temp storage: 2GB. |
| **Safe Rendering** | Chromium must be sandboxed to prevent any filesystem access beyond the designated output directory. |
| **Dependency Scanning** | All npm and Python dependencies must be scanned for known CVEs before release. |
| **Voice Data Privacy** | Cloned voice audio files must not be transmitted externally unless explicitly configured. All processing must remain local. |

### 8.3 Scalability

| Requirement | Description |
|---|---|
| **Job Queue Depth** | Support at least 50 queued jobs without degradation |
| **Concurrent Render Limit** | Configurable concurrency (1-8) with sensible default of 2 |
| **Memory Management** | Release Chromium process after each render; pool TTS model in shared memory |
| **Disk Cleanup** | Automatic cleanup of temp assets after configurable TTL (default: 24 hours) |
| **Horizontal Scaling** | Stateless MCP server with Redis-backed job queue for multi-instance deployment (future) |

### 8.4 Portability

| Requirement | Description |
|---|---|
| **Platform Support** | Linux (primary), macOS (development), Windows (WSL2) |
| **Python Version** | Python 3.10+ |
| **Node.js Version** | Node.js 18+ |
| **Containerization** | Official Docker image with all dependencies (Chromium, Python, Node.js, TTS model) |
| **Agent Compatibility** | Zero agent-specific code; pure MCP protocol compliance for all tool calls |
| **CI/CD Integration** | Runnable in GitHub Actions, GitLab CI, Jenkins, CircleCI without modifications |
| **MCP Protocol** | Strict adherence to MCP specification; no proprietary extensions |

### 8.5 Maintainability

| Requirement | Description |
|---|---|
| **Code Organization** | Modular architecture with clear separation: mcp/, pipeline/, renderer/, tts/, github/, assets/, qa/ |
| **Testing Coverage** | ≥80% unit test coverage for pipeline orchestration, asset generation, and QA modules |
| **Integration Tests** | End-to-end test suite that generates a 30-second test video and validates output |
| **Documentation** | README with setup, configuration, and usage. Example scripts for each composition type. |
| **Error Handling** | Every pipeline phase must handle failures gracefully, log structured errors, and report to caller via MCP result. |
| **Observability** | Structured JSON logging with configurable levels. Metrics endpoint for job counts, durations, and failure rates. |
| **Configuration** | Single config file (JSON/YAML) with environment variable overrides for secrets |

---

## 9. Constraints

### 9.1 Technical Constraints

| Constraint | Impact | Mitigation |
|---|---|---|
| **TTS model load: 30s+ cold start** | First TTS request after server start has high latency | Keep model loaded once; health check endpoint to pre-warm |
| **Word timestamps are estimated** | Caption accuracy is ±100ms, not studio-quality | Document accuracy; offer Whisper pipeline as future upgrade |
| **Chromium rendering on Linux** | Requires specific system dependencies (libnss3, libnspr4, libatk1.0-0, etc.) | Provide Docker image with all deps; document manual install |
| **GitHub webhook 10s timeout** | Cannot render synchronously in webhook handler | All pipelines are async; webhook returns 202 immediately |
| **Pipeline takes 2-10 minutes** | Not usable for real-time or interactive workflows | Async-only architecture with webhook notification; progress tracking |
| **Remotion requires Node.js** | Additional runtime dependency beyond Python | Docker image bundles both runtimes |
| **FFmpeg required for audio mixing** | Additional system dependency | Include in Docker image; document system install |
| **Memory: 1-4GB per render job** | Limits concurrent renders on resource-constrained systems | Default concurrency of 2; configurable lower |

### 9.2 Time Constraints

| Constraint | Target |
|---|---|
| **MVP Release** | Q3 2026 |
| **Core Pipeline (INGEST → RENDER)** | Q3 2026 |
| **Diagram Generation** | Q3 2026 (Phase 1) |
| **Whisper Word Timestamps** | Q4 2026 (Phase 2) |
| **Batch Processing** | Q4 2026 (Phase 2) |
| **CI/CD Integration** | Q4 2026 (Phase 2) |
| **GitHub App (with Checks API)** | Q1 2027 (Phase 3) |
| **AI Image Generation** | Q1 2027 (Phase 3) |

### 9.3 Resource Constraints

| Resource | Limit | Notes |
|---|---|---|
| **TTS Model Size** | 438MB | Pocket TTS model; must be downloaded once |
| **Python Dependencies** | <500MB | FastMCP, httpx, pydantic, etc. |
| **Node.js Dependencies** | <200MB | Remotion, React, Shiki, etc. |
| **Docker Image Size** | <3GB | Includes Python, Node.js, Chromium, FFmpeg, TTS model |
| **RAM per Render Job** | 1-4GB | Chromium + Remotion + TTS peak memory |
| **Disk per Render Job** | 500MB-2GB | Temp assets, audio files, output video |
| **Network** | GitHub API only | No external services required for core functionality |

---

## 10. Out of Scope

The following features are explicitly out of scope for v1.0 and all current planning:

| Feature | Rationale |
|---|---|
| **Human-presenter video (webcam overlay)** | Requires real-time video capture and compositing; out of scope for code-focused explainers |
| **Live streaming** | VideoForge is a batch rendering system, not a streaming platform |
| **YouTube / Vimeo direct upload** | Platform-specific OAuth and API integration; users can upload manually |
| **Interactive / clickable videos** | Video output is standard MP4; no interactive overlays |
| **Mobile app or web UI** | MCP-native means all interaction is through AI agents; no GUI planned |
| **Video editing GUI** | Users edit via script/scene plan JSON, not timeline editors |
| **Screen recording** | VideoForge generates synthetic video from code, not recordings of user activity |
| **Multi-language video (single video with multiple language tracks)** | Each video uses one language; user generates separate videos for each language |
| **Real-time generation (<30s)** | Pipeline has inherent latency from TTS, rendering, and LLM calls |
| **Custom user fonts / advanced typography** | Limited to system fonts and a curated set of bundled fonts |
| **3D animations or WebGL graphics** | Remotion uses React DOM/CSS; 3D is out of scope for v1 |
| **Voice emotion / emphasis control** | Pocket TTS supports basic prosody; fine-grained emotion control not supported |
| **Video chapter markers / chapters** | MP4 chapter markers are platform-specific; not supported |
| **GitHub App with Checks API** | Complex OAuth and event handling; deferred to Phase 3 |
| **Plugin / extension system** | Modular architecture but no formal plugin API in v1 |
| **Self-hosted model training for TTS** | Uses pre-trained Pocket TTS model; no custom training pipeline |
| **Cloud rendering service** | Fully local / self-hosted; no cloud component (except optional AI image gen APIs) |

---

## 11. Success Metrics

### 11.1 Key Performance Indicators (KPIs)

| Metric | Target | Measurement |
|---|---|---|
| **Pipeline Success Rate** | ≥95% of initiated jobs complete successfully | Total successful / total initiated |
| **Average Pipeline Duration (simple PR)** | ≤120 seconds | P50 end-to-end time |
| **Average Pipeline Duration (complex PR)** | ≤600 seconds | P95 end-to-end time |
| **User Script Approval Rate** | ≥80% of auto-generated scripts used without edits | Edits requested / total scripts generated |
| **Voice Satisfaction Rate** | ≥90% of users keep the suggested voice | Voice changes / total videos |
| **Render Failure Rate** | ≤5% of renders require retry | Retries / total renders |
| **TTS Synthesis Quality** | ≥90% user rating of "good" or "excellent" | User survey after first 100 videos |
| **Caption Accuracy** | ≥95% of words within ±150ms of audio | Spot-check against manual alignment |
| **Agent Compatibility** | 100% of tested MCP agents work without modification | Test against Claude Code, Cursor, Windsurf, Copilot |
| **Webhook Delivery Success** | ≥99% of webhooks delivered within 5 retries | Delivery logs |

### 11.2 Business Metrics

| Metric | Target | Timeline |
|---|---|---|
| **Total Videos Generated** | 1,000 within first 3 months | Post-launch |
| **Active Users** | 100 within first 3 months | Users who generate ≥5 videos |
| **GitHub Star Growth** | 500 stars in first 6 months | Open source adoption |
| **CI/CD Integrations** | 10 verified CI/CD pipeline examples | Within 6 months |
| **Community Contributions** | 20 PRs from external contributors | Within 6 months |
| **MCP Ecosystem Rank** | Top 50 most-installed MCP servers | Within 12 months |

### 11.3 Quality Gates

| Gate | Description | Pass Criteria |
|---|---|---|
| **Unit Tests** | All modules have ≥80% line coverage | CI passes with coverage threshold |
| **Integration Tests** | End-to-end test generates valid 30s video | Output passes all QA checks |
| **Render Consistency** | Same input produces bit-identical output | Deterministic rendering (seed-based) |
| **Error Recovery** | Simulated failures at each phase are handled | Job reports correct error status and allows retry |
| **Resource Limits** | Stress test with max concurrency and file sizes | No OOM, no disk overflow, graceful degradation |

---

## 12. Release Criteria

### 12.1 v1.0 Release Criteria

All of the following must be true before v1.0 is released:

| # | Criterion | Verification Method |
|---|---|---|
| R-01 | All 13 MCP tools are implemented and respond correctly | Automated integration test against MCP server |
| R-02 | All 3 MCP resources are implemented and return valid data | Automated resource query test |
| R-03 | All 4 compositions (CodeWalkthrough, PRSummary, IssueExplainer, ChangelogVideo) produce valid videos | Manual review of output for each composition |
| R-04 | All 8 scene types render correctly with sample data | Automated render test per scene type |
| R-05 | All 12 scene transitions render without visual artifacts | Automated render test per transition |
| R-06 | TTS integration works with all 26 predefined voices | Automated synthesis test per voice |
| R-07 | TTS integration supports all 12 languages | Automated synthesis test per language |
| R-08 | Voice cloning works from a provided audio file | Manual test with sample audio |
| R-09 | GitHub PR content fetching works (diff, comments, description) | Integration test against public test repo |
| R-10 | GitHub issue content fetching works | Integration test against public test repo |
| R-11 | GitHub release/changelog content fetching works | Integration test against public test repo |
| R-12 | Async job management works (status, result, cancel) | Automated API test |
| R-13 | Webhook delivery works on job completion | Automated test with webhook receiver |
| R-14 | Script preview and scene plan preview return before render | Automated API test |
| R-15 | All 9 pipeline phases complete without errors for a simple PR | End-to-end test (target PR with 3 files, <100 lines diff) |
| R-16 | QA module validates rendered video and passes | Automated QA check on test output |
| R-17 | Word-level captions are generated and displayed correctly | Visual review of test video |
| R-18 | Background music is mixed with narration ducking | Audio analysis on test output |
| R-19 | DiagramScene renders at least 3 diagram types correctly | Visual and functional test |
| R-20 | Docker image builds and runs without manual dependency install | CI build test |
| R-21 | MCP server works with Claude Code (verified integration) | Manual test with Claude Code |
| R-22 | MCP server works with at least one other agent (Cursor, Windsurf, or Copilot) | Manual test |
| R-23 | All pipeline failures produce structured error messages | Error injection test per phase |
| R-24 | No secrets leak in logs or error messages | Log audit with intentional error scenarios |
| R-25 | Pipeline completes within 2× the target latency for a simple PR | Performance test |
| R-26 | Server can handle 2 concurrent jobs without degradation | Load test |
| R-27 | Documentation is complete: README, setup guide, example usage, API reference | Manual review |
| R-28 | AGENTS.md is present with instructions for AI agents | File exists and covers all tool usage |
| R-29 | License file is present (MIT recommended) | File exists |
| R-30 | All dependencies have no known critical CVEs | `npm audit` and `pip audit` pass |

### 12.2 Stretch Goals (Not Blocking v1.0)

| Goal | Target Version |
|---|---|
| Whisper.cpp word-level timestamp pipeline (±20ms accuracy) | v1.1 |
| AI image generation (DALL-E / Stable Diffusion integration) | v1.1 |
| Batch job processing | v1.1 |
| GitHub Actions reusable workflow | v1.1 |
| Branding templates (save and reuse color/font/config) | v1.2 |
| Custom transitions API | v1.2 |
| GitHub App with Checks API | v2.0 |
| Voice emotion/prosody control | v2.0 |

---

## 13. Appendix: Scene Types Reference

| Scene Type | Component | Use Case | Key Props | Default Duration |
|---|---|---|---|---|
| **TitleScene** | `TitleScene.tsx` | Video opening | title, subtitle, logo | 6s (180 frames) |
| **CodeScene** | `CodeScene.tsx` | Code explanation | code, language, focusLines, theme | 15s (450 frames) |
| **DiffScene** | `DiffScene.tsx` | Before/after comparison | beforeCode, afterCode, language, hunkHeaders | 15s (450 frames) |
| **BulletScene** | `BulletScene.tsx` | Key points listing | items, title, layout | 10s (300 frames) |
| **ImageScene** | `ImageScene.tsx` | Visual context | imageUrl, caption, effect | 6s (180 frames) |
| **ComparisonScene** | `ComparisonScene.tsx` | Side comparison | leftContent, rightContent, leftLabel, rightLabel, type | 12s (360 frames) |
| **DiagramScene** | `DiagramScene.tsx` | Architecture visualization | diagramType, data, animated | 15s (450 frames) |
| **OutroScene** | `OutroScene.tsx` | Video ending | title, ctaText, ctaUrl, watermark | 6s (180 frames) |

---

## 14. Appendix: Scene Transitions Reference

| Transition | Implementation | Import Source | Default Duration |
|---|---|---|---|
| fade | `@remotion/transitions/fade` | `@remotion/transitions` | 15 frames |
| slide-left | `@remotion/transitions/slide` | `@remotion/transitions` | 20 frames |
| slide-up | `@remotion/transitions/slide` | `@remotion/transitions` | 20 frames |
| wipe-left | `@remotion/transitions/wipe` | `@remotion/transitions` | 15 frames |
| flip | `@remotion/transitions/flip` | `@remotion/transitions` | 25 frames |
| crossZoom | `@remotion/transitions/cross-zoom` | `@remotion/transitions` | 30 frames |
| clockWipe | `@remotion/transitions/clock-wipe` | `@remotion/transitions` | 20 frames |
| glitch | Custom component | Project source | 10 frames |
| morph | Custom component | Project source | 25 frames |
| none | Cut (no transition) | — | 0 frames |
| push-left | Custom component | Project source | 20 frames |
| zoom-in | Custom component | Project source | 25 frames |

---

## 15. Appendix: Compositions Reference

| Composition | Scene Sequence | Recommended For | Default Transition |
|---|---|---|---|
| **CodeWalkthrough** | Title → DiffScene (1-10) → BulletScene → OutroScene | PR walkthroughs, code review explanations | slide-left |
| **PRSummary** | Title → CodeScene → OutroScene | Quick PR summaries for standups | fade |
| **IssueExplainer** | Title → BulletScene → CodeScene → OutroScene | Bug reports, feature requests | slide-up |
| **ChangelogVideo** | Title → N×(DiffScene/BulletScene) → OutroScene | Release notes, version changelogs | crossZoom |

Each composition specifies:
- **Default scene sequence**: The standard order of scene types
- **Configurable**: Users can add, remove, or reorder scenes within the composition structure
- **Adaptive**: DiffScene count adapts to number of changed files; BulletScene count adapts to number of items
- **Fallback**: If a requested scene type cannot be populated (e.g., no images for ImageScene), the composition falls back to BulletScene with the same content

---

## 16. Appendix: Pipeline Phases Reference

| Phase | ID | Description | Input | Output | Estimated Duration |
|---|---|---|---|---|---|
| **Ingest** | `INGEST` | Fetch and normalize GitHub content | GitHub URL | Normalized content JSON | 3-15s |
| **Research** | `RESEARCH` | Enrich content with context | Normalized content | Research summary | 5-20s |
| **Script** | `SCRIPT` | Generate narrative script | Research summary | Script with segments | 5-15s |
| **Scene Plan** | `SCENE_PLAN` | Map script to scene sequence | Script segments | Scene plan JSON | 2-5s |
| **Asset Generation** | `ASSET_GEN` | Generate TTS, images, diagrams | Scene plan | Asset files + metadata | 30-180s |
| **Compose** | `COMPOSE` | Build Remotion input props | Scene plan + assets | Remotion input props | 1-3s |
| **Render** | `RENDER` | Render video with Chromium | Remotion input props | Raw video file | 60-300s |
| **Review** | `REVIEW` | Post-process and validate | Raw video file | Validated video + report | 5-15s |
| **Publish** | `PUBLISH` | Deliver and notify | Validated video | File path + webhook | 1-5s |

**Phase Characteristics:**

- **Deterministic**: All phases produce deterministic output given the same inputs (seed-based rendering for Remotion)
- **Idempotent**: Phases can be retried independently without side effects
- **Stateful**: Phase outputs are persisted to disk for inspection and debugging
- **Independent**: Phases receive all data via explicit input; no shared mutable state
- **Logged**: Each phase writes structured JSON logs with timestamps, input/output sizes, and error details
- **Timeboxed**: Each phase has a configurable timeout to prevent runaway jobs

---

## Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0.0 | 2026-07-08 | Product Team | Initial comprehensive PRD |
