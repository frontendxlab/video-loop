# VideoForge Technical Specification

**Version:** 1.0.0  
**Status:** Draft  
**Last Updated:** 2026-07-08  
**Repository:** `/home/rashid/projects/videoforge/`

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Technology Stack](#2-technology-stack)
3. [Module Specifications](#3-module-specifications)
   - 3.1 [MCP Server (mcp_server.py)](#31-mcp-server-mcp_serverpy)
   - 3.2 [Configuration Module (config.py)](#32-configuration-module-configpy)
   - 3.3 [TTS Adapter (tts_adapter.py)](#33-tts-adapter-tts_adapterpy)
   - 3.4 [Audio Pipeline (audio_pipeline.py)](#34-audio-pipeline-audio_pipelinepy)
   - 3.5 [Content Fetcher (agents/content_fetcher.py)](#35-content-fetcher-agentscontent_fetcherpy)
   - 3.6 [Content Classifier (agents/content_classifier.py)](#36-content-classifier-agentscontent_classifierpy)
   - 3.7 [Script Writer (agents/script_writer.py)](#37-script-writer-agentsscript_writerpy)
   - 3.8 [Scene Planner (agents/scene_planner.py)](#38-scene-planner-agentsscene_plannerpy)
   - 3.9 [Composition Builder (agents/composition_builder.py)](#39-composition-builder-agentscomposition_builderpy)
   - 3.10 [Image Generator (agents/image_generator.py)](#310-image-generator-agentsimage_generatorpy)
   - 3.11 [Publisher (agents/publisher.py)](#311-publisher-agentspublisherpy)
   - 3.12 [Render Executor (tools/render_executor.py)](#312-render-executor-toolsrender_executorpy)
   - 3.13 [Video Reviewer (tools/video_reviewer.py)](#313-video-reviewer-toolsvideo_reviewerpy)
   - 3.14 [Webhook Handler (webhook/handler.py)](#314-webhook-handler-webhookhandlerpy)
   - 3.15 [Exceptions Module (exceptions.py)](#315-exceptions-module-exceptionspy)
   - 3.16 [Remotion Project (TypeScript/React)](#316-remotion-project-typescriptreact)
4. [Data Flow](#4-data-flow)
   - 4.1 [GitHub PR Explainer Workflow](#41-github-pr-explainer-workflow)
   - 4.2 [Audio Generation Pipeline](#42-audio-generation-pipeline)
   - 4.3 [Remotion Rendering Pipeline](#43-remotion-rendering-pipeline)
   - 4.4 [Webhook-Driven Pipeline](#44-webhook-driven-pipeline)
5. [Interface Contracts](#5-interface-contracts)
   - 5.1 [Config Schema](#51-config-schema)
   - 5.2 [MCP Tool Signatures](#52-mcp-tool-signatures)
   - 5.3 [Remotion InputProps Schema](#53-remotion-inputprops-schema)
   - 5.4 [Scene Plan Schema](#54-scene-plan-schema)
   - 5.5 [Audio Track Schema](#55-audio-track-schema)
   - 5.6 [Caption Schema](#56-caption-schema)
   - 5.7 [GitHub Data Schemas](#57-github-data-schemas)
   - 5.8 [State File Format](#58-state-file-format)
   - 5.9 [Diagram Config Schema](#59-diagram-config-schema)
6. [Error Handling Strategy](#6-error-handling-strategy)
   - 6.1 [Exception Hierarchy](#61-exception-hierarchy)
   - 6.2 [Retry Policies](#62-retry-policies)
   - 6.3 [Fallback Behaviors](#63-fallback-behaviors)
   - 6.4 [Pipeline Error Propagation](#64-pipeline-error-propagation)
7. [Testing Strategy](#7-testing-strategy)
   - 7.1 [Test Pyramid](#71-test-pyramid)
   - 7.2 [Unit Tests: Python](#72-unit-tests-python)
   - 7.3 [Unit Tests: TypeScript/React](#73-unit-tests-typescriptreact)
   - 7.4 [Integration Tests](#74-integration-tests)
   - 7.5 [End-to-End Tests](#75-end-to-end-tests)
   - 7.6 [Mocking Strategy](#76-mocking-strategy)
   - 7.7 [Test Fixtures](#77-test-fixtures)
8. [Security Considerations](#8-security-considerations)
   - 8.1 [Input Validation](#81-input-validation)
   - 8.2 [HMAC Signature Verification](#82-hmac-signature-verification)
   - 8.3 [Shell Injection Prevention](#83-shell-injection-prevention)
   - 8.4 [Secrets Management](#84-secrets-management)
   - 8.5 [Subprocess Security](#85-subprocess-security)
9. [Performance Budgets](#9-performance-budgets)
   - 9.1 [Render Time Budgets](#91-render-time-budgets)
   - 9.2 [Memory Limits](#92-memory-limits)
   - 9.3 [Token Budgets](#93-token-budgets)
   - 9.4 [Audio Pipeline Budgets](#94-audio-pipeline-budgets)
10. [Agent Skill Specifications](#10-agent-skill-specifications)
    - 10.1 [video-ingest.skill.md](#101-video-ingestskillmd)
    - 10.2 [video-research.skill.md](#102-video-researchskillmd)
    - 10.3 [video-script.skill.md](#103-video-scriptskillmd)
    - 10.4 [video-scene-plan.skill.md](#104-video-scene-planskillmd)
    - 10.5 [video-assets.skill.md](#105-video-assetsskillmd)
    - 10.6 [video-compose.skill.md](#106-video-composeskillmd)
    - 10.7 [video-render.skill.md](#107-video-renderskillmd)
    - 10.8 [video-review.skill.md](#108-video-reviewskillmd)
11. [Appendix](#11-appendix)
    - 11.1 [Glossary](#111-glossary)
    - 11.2 [Environment Variables](#112-environment-variables)
    - 11.3 [Configuration File Reference](#113-configuration-file-reference)

---

## 1. System Overview

### 1.1 High-Level Architecture

VideoForge is an MCP-native automated video generation pipeline that creates developer-focused explainer videos from GitHub content. It bridges a Python MCP server (orchestration, TTS, GitHub integration) with a TypeScript/React Remotion project (composition, rendering, captions).

```
                              +-----------------------+
                              |     GitHub Events     |
                              | (Push, PR, Issue,     |
                              |  Release)             |
                              +----------+------------+
                                         |
                                         v
+----------------------------------------+----------------------------------------+
|                                 MCP Server (Python)                              |
|                                                                                   |
|  +-------------------+  +-------------------+  +----------------+                 |
|  | Content Fetcher   |  | Content Classifier|  | Script Writer  |                 |
|  | (gh CLI / HTTP)   |  | (LLM analysis)    |  | (LLM gen)      |                 |
|  +--------+----------+  +--------+----------+  +-------+--------+                 |
|           |                      |                      |                          |
|           v                      v                      v                          |
|  +-------------------+  +-------------------+  +----------------+                 |
|  | Scene Planner     |  | Image Generator   |  | TTS Adapter    |                 |
|  | (LLM scene plan)  |  | (AI / Stock /     |  | (Pocket TTS    |                 |
|  |                   |  |  Code-Only)       |  |  HTTP client)  |                 |
|  +--------+----------+  +--------+----------+  +-------+--------+                 |
|           |                      |                      |                          |
|           +----------------------+----------------------+                          |
|                                  |                                                 |
|                                  v                                                 |
|  +-------------------+  +-------------------+  +----------------+                 |
|  | Composition       |  | Render Executor   |  | Video Reviewer |                 |
|  | Builder           |  | (Remotion         |  | (LLM review)   |                 |
|  | (Zod InputProps)  |  |  subprocess)      |  |                |                 |
|  +--------+----------+  +--------+----------+  +-------+--------+                 |
|           |                      |                      |                          |
|           +----------------------+----------------------+                          |
|                                  |                                                 |
|                                  v                                                 |
|  +-------------------+  +-------------------+                                     |
|  | Publisher         |  | Webhook Handler   |                                     |
|  | (gh PR comment)   |  | (HMAC-256 verify) |                                     |
|  +-------------------+  +-------------------+                                     |
+----------------------------------+------------------------------------------------+
                                   |
                                   v
+----------------------------------+------------------------------------------------+
|                             Remotion Project (TypeScript/React)                     |
|                                                                                    |
|  +-------------------+  +-------------------+  +----------------+                  |
|  | Compositions:     |  | Scenes:           |  | Transitions:   |                  |
|  | CodeWalkthrough   |  | TitleScene        |  | FadeTransition |                  |
|  | PRSummary         |  | CodeScene         |  | SlideTransition |                  |
|  | IssueExplainer    |  | DiffScene         |  | ZoomTransition  |                  |
|  | ChangelogVideo    |  | BulletScene       |  | ... (12 total)  |                  |
|  +-------------------+  | ImageScene        |  +----------------+                  |
|                         | ComparisonScene   |                                      |
|                         | DiagramScene      |  +----------------+                  |
|                         | OutroScene        |  | Components:    |                  |
|                         +-------------------+  | CaptionOverlay  |                  |
|                                                 | AnimatedText   |                  |
|                                                 | CodeBlock      |                  |
|                                                 | DiffView       |                  |
|                                                 +----------------+                  |
+------------------------------------------------------------------+----------------+
                                   |
                                   v
                    +-------------------------------+
                    |        Output Video            |
                    |  (.mp4, .webm, .gif)            |
                    +-------------------------------+
```

### 1.2 Component Diagram

```
+============================================================================+
|                          VideoForge System                                   |
+============================================================================+
|                                                                              |
|  +----------------------------------+  +----------------------------------+  |
|  |       Python Layer (MCP)         |  |     TypeScript Layer (Remotion)  |  |
|  |                                  |  |                                  |  |
|  |  mcp_server.py                   |  |  Root.tsx (Composition defs)     |  |
|  |  config.py                       |  |  types.ts (shared types)         |  |
|  |  exceptions.py                   |  |  design-tokens.ts                |  |
|  |  tts_adapter.py                  |  |  index.ts (registerRoot)         |  |
|  |  audio_pipeline.py               |  |                                  |  |
|  |  agents/*.py (7 agents)          |  |  compositions/ (4 comps)         |  |
|  |  tools/*.py (2 tools)            |  |  scenes/ (8 scenes)              |  |
|  |  webhook/handler.py              |  |  transitions/ (12 transitions)   |  |
|  +----------------------------------+  |  components/ (4 components)      |  |
|                                         +----------------------------------+  |
|                                                                              |
|  +----------------------------------+  +----------------------------------+  |
|  |       External Services          |  |     Configuration & State        |  |
|  |                                  |  |                                  |  |
|  |  Pocket TTS (HTTP FastAPI)       |  |  config.yaml                     |  |
|  |  GitHub (gh CLI + webhooks)      |  |  STATE.md                        |  |
|  |  AI Image (Stable Diffusion)     |  |  PLAN.json                       |  |
|  |  Stock Photos (Pexels/Pixabay)   |  |  environment variables           |  |
|  |  npm (@shetty4l/diagrams)        |  |                                  |  |
|  +----------------------------------+  +----------------------------------+  |
|                                                                              |
+============================================================================+
```

### 1.3 Architectural Principles

1. **MCP-Native**: All tools expose MCP tool interfaces via FastMCP. No REST/gRPC endpoints except webhooks.
2. **Stateless Python, Stateful Remotion**: The MCP server is stateless per request. All state flows through inputProps JSON. Remotion is stateful only during rendering.
3. **Sequential Pipeline, Resilient Errors**: The pipeline runs 11 phases sequentially. A failure in one phase is captured and the pipeline continues to the next phase; no phase-level rollback.
4. **Agent Specialization**: Each Python agent owns a complete pipeline phase, producing structured JSON consumed by the next.
5. **Kill Switch**: `VIDEOFORCE_KILL_SWITCH` env var is polled before each phase. If set, execution halts gracefully.
6. **Shared TTS Connection**: TTS adapter maintains a shared HTTP session to Pocket TTS, reused across requests.
7. **Configuration Overrides**: YAML config is layered with environment variable overrides (lowercase keys with underscores correspond to YAML paths).

---

## 2. Technology Stack

### 2.1 Python Dependencies

| Package | Version | Purpose | Why Chosen |
|---------|---------|---------|------------|
| `mcp` | >=1.0.0 | FastMCP server framework | MCP-native design; stdio transport; tool/function decorators |
| `httpx` | >=0.27.0 | HTTP client for Pocket TTS | Async support; connection pooling; timeout control |
| `pyyaml` | >=6.0 | YAML config parsing | Standard; well-tested; multi-document support |
| `pydantic` | >=2.0 | Config model validation | Type-safe config; JSON Schema generation; validation errors |
| `pydantic-settings` | >=2.0 | Env var override support | Pairs with pydantic; nested env var mapping |
| `soundfile` | >=0.12 | WAV file I/O (read/write) | Handles 24-bit WAV; supports int16/float32; fast C bindings |
| `numpy` | >=1.26 | Audio buffer manipulation | Crossfade math; sample-level operations; array slicing |
| `pydub` | >=0.25 | Audio chunk stitching | Crossfade concat out of the box; FFmpeg backend |
| `ffmpeg-python` | >=0.20 | FFmpeg subprocess wrapper | Pythonic FFmpeg API; avoid raw subprocess strings |
| `httpx-sse` | >=0.4 | SSE streaming (future TTS) | Streaming JSON responses; event parsing |
| `pytest` | >=8.0 | Unit/integration testing | Standard; fixtures; monkeypatch; tmp_path |
| `pytest-asyncio` | >=0.23 | Async test support | Async generator fixtures; event loop management |
| `pytest-cov` | >=5.0 | Coverage reporting | HTML/XML/Cobertura output; branch coverage |
| `respx` | >=0.20 | HTTP mocking for httpx | Pattern-match URLs; mock responses; assert calls |
| `ruff` | >=0.4 | Linting + formatting | Fast Python linter; autofix; pyproject.toml config |
| `mypy` | >=1.10 | Static type checking | Strict mode; pydantic plugin; typed dicts |

### 2.2 TypeScript Dependencies

| Package | Version | Purpose | Why Chosen |
|---------|---------|---------|------------|
| `remotion` | ^4.0.228 | Video composition framework | Programmatic React video; frame-based rendering; server-side |
| `@remotion/bundler` | ^4.0.228 | Webpack bundler for Remotion | Required for remotion render; custom entry point |
| `@remotion/renderer` | ^4.0.228 | Server-side rendering API | `renderMedia()` API; progress callbacks; cancel support |
| `@remotion/media-utils` | ^4.0.228 | Audio visualization | `useAudioData()` hook; `visualizeAudio()` for waveform |
| `@remotion/transitions` | ^4.0.228 | Scene transition system | `TransitionSeries`, `TransitionPresentation`; pluggable |
| `@remotion/captions` | ^4.0.228 | TikTok-style captions | `createTikTokStyleCaptions()`; word-level highlighting |
| `@remotion/google-fonts` | ^4.0.228 | Font loading | Google Fonts subset; `loadFont()`; WOFF2 optimization |
| `zod` | ^3.23 | Runtime type validation | inputProps validation; discriminated unions for scenes |
| `react` | ^18.3 | UI library | Component model; hooks; concurrent features |
| `react-dom` | ^18.3 | DOM rendering | Required by Remotion; SSR support |

### 2.3 Dev Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `vitest` | ^2.0 | Test runner (fast, Vite-based) |
| `@testing-library/react` | ^16.0 | Component testing utilities |
| `jsdom` | ^24.0 | DOM environment for tests |
| `eslint` | ^9.0 | Code quality (flat config) |
| `prettier` | ^3.3 | Formatting |
| `typescript` | ^5.5 | Type checking |

### 2.4 External Services

| Service | Purpose | Integration Method |
|---------|---------|-------------------|
| Pocket TTS Server | Text-to-speech generation | HTTP POST /tts (form data) |
| GitHub CLI (`gh`) | PR/issue data fetch, comment posting | subprocess.run |
| AI Image (Stable Diffusion) | Custom diagram/hero image generation | HTTP API (configurable provider) |
| Stock Photos (Pexels/Pixabay) | Background/tech imagery | HTTP REST API |
| @shetty4l/diagrams (npm) | Diagram rendering engine | subprocess node execution |

### 2.5 System Dependencies

| Tool | Min Version | Purpose |
|------|-------------|---------|
| Python | 3.12+ | MCP server runtime |
| Node.js | 20+ | Remotion rendering |
| FFmpeg | 6.0+ | Audio crossfade stitching, video metadata |
| gh CLI | 2.0+ | GitHub API operations |
| npm | 10+ | Package management |

---

## 3. Module Specifications

### 3.1 MCP Server (`mcp_server.py`)

#### Purpose
Entry point for all MCP interactions. Registers all tools with FastMCP, initializes shared resources (TTS client, config), and dispatches to agent modules.

#### Responsibilities
- Initialize FastMCP server with name, host, port, log_level from config
- Register and expose all MCP tools as `@mcp.tool()` decorated functions
- Poll `VIDEOFORCE_KILL_SWITCH` before each tool execution
- Maintain shared `TTSClient` instance for connection reuse
- Log all tool invocations with timing

#### Public API

```python
class MCPServer:
    def __init__(self, config: AppConfig) -> None
    def run(self) -> None:
        """Start the MCP server. Blocking. Uses stdio transport."""

# FastMCP tool decorators registered:
@mcp.tool()
def health_check() -> dict  # {"status": "ok"}

@mcp.tool()
def get_server_info() -> dict  # config snapshot

@mcp.tool()
def generate_speech(text: str, output_path: str, voice: str | None = None) -> dict

@mcp.tool()
def list_voices() -> dict

@mcp.tool()
def list_saved_voices() -> dict

@mcp.tool()
def process_audio_script(script_text: str, scene_id: str, output_dir: str) -> dict

@mcp.tool()
def fetch_github_pr(url: str) -> dict

@mcp.tool()
def fetch_github_issue(url: str) -> dict

@mcp.tool()
def plan_scenes(script: str) -> dict

@mcp.tool()
def generate_images(scene: dict) -> dict

@mcp.tool()
def build_composition(scene_plan: dict, audio_map: dict, image_map: dict) -> dict

@mcp.tool()
def render_video(composition_id: str, input_props: dict) -> dict

@mcp.tool()
def review_video(video_path: str) -> dict

@mcp.tool()
def doctor() -> dict  # pre-flight check
```

#### Internal Design
- Uses `mcp.server.fastmcp.FastMCP` for server framework
- Tool functions are plain async def with type annotations
- Each tool extracts params from FastMCP context, delegates to agent modules
- Shared `TTSClient` instance is stored on server object, initialized lazily
- Kill switch checked via `os.environ.get("VIDEOFORCE_KILL_SWITCH")` — if truthy, return early with status message

#### Error Handling
- All tool functions wrap implementation in try/except, returning `{"error": str(e)}` dict
- Logs exceptions via `logging.exception()` before returning error
- Unhandled crashes log fatal and re-raise (MCP protocol handles disconnection)

#### Configuration Options
- From `config.yaml` → `server.name`, `server.host`, `server.port`, `server.log_level`
- Kill switch is env var only (`VIDEOFORCE_KILL_SWITCH`)

---

### 3.2 Configuration Module (`config.py`)

#### Purpose
Load and validate the YAML configuration file, apply environment variable overrides, and provide typed access to all config values.

#### Responsibilities
- Load `config.yaml` from project root
- Validate against `pydantic.BaseModel` schemas
- Apply environment variable overrides (lowercase, underscore-separated path)
- Expose `AppConfig` as a frozen (immutable) dataclass

#### Public API

```python
def load_config(path: str | None = None) -> AppConfig:
    """Load config from YAML file, apply env overrides, return validated object."""

class AppConfig(BaseModel, frozen=True):
    server: ServerConfig
    pocket_tts: PocketTTSConfig
    pipeline: PipelineConfig
    assets: AssetsConfig
    github: GitHubConfig

class ServerConfig(BaseModel):
    name: str = "VideoForge"
    host: str = "127.0.0.1"
    port: int = 8080
    log_level: str = "INFO"

class PocketTTSConfig(BaseModel):
    server_url: str = "http://127.0.0.1:8120"
    default_voice: str = "en_US-amy-medium"
    language: str = "en"
    max_retries: int = 3
    timeout_seconds: int = 60

class PipelineConfig(BaseModel):
    max_video_duration_seconds: int = 180
    default_fps: int = 30
    default_resolution: tuple[int, int] = (1920, 1080)
    default_codec: str = "h264"
    max_caption_tokens_per_chunk: int = 50

class AssetsConfig(BaseModel):
    ai_generation: ProviderConfig
    stock_photos: ProviderConfig

class ProviderConfig(BaseModel):
    enabled: bool = False
    provider: str = ""

class GitHubConfig(BaseModel):
    webhook_secret_env: str = "VIDEOFORGE_WEBHOOK_SECRET"
    auto_post_pr_comments: bool = True
```

#### Internal Design
- `pyyaml` loads the YAML file
- `pydantic` validates and coerces types
- Env var override convention: `VIDEOFORGE_SERVER__LOG_LEVEL` → `config.server.log_level` (double underscore for nesting)
- On validation failure, raises `ConfigurationError` with detailed message
- `frozen=True` ensures immutability after load

#### Error Handling
- `FileNotFoundError` if YAML file missing → `ConfigurationError("Config file not found: {path}")`
- `pydantic.ValidationError` caught and re-raised as `ConfigurationError` with field-by-field errors
- `yaml.YAMLError` → `ConfigurationError("Invalid YAML syntax")`

#### Configuration Options
- See [Section 5.1](#51-config-schema) for full schema
- All env var overrides listed in [Section 11.2](#112-environment-variables)

---

### 3.3 TTS Adapter (`tts_adapter.py`)

#### Purpose
HTTP client for Pocket TTS server. Handles speech generation requests with retry logic, voice listing, and audio response parsing.

#### Responsibilities
- Send text chunks to Pocket TTS `/tts` endpoint
- Handle StreamingResponse (audio/wav) and JSON (base64) response formats
- Exponential backoff retry with configurable max_retries
- Maintain shared HTTP session (httpx.AsyncClient)
- Provide voice listing with hardcoded fallback

#### Public API

```python
class TTSClient:
    def __init__(self, config: PocketTTSConfig) -> None

    async def generate_speech(
        self,
        text: str,
        voice: str | None = None,
        output_path: str | Path | None = None,
    ) -> bytes:
        """Generate speech audio. Returns WAV bytes. If output_path given, writes to disk."""

    async def list_voices(self) -> list[VoiceInfo]:
        """Fetch available voices from server, fall back to hardcoded list."""

    async def close(self) -> None:
        """Close underlying HTTP session."""

class VoiceInfo(TypedDict):
    id: str
    name: str
    language: str
    gender: str | None
```

#### Internal Design

**Speech Generation Flow:**
1. Build form data: `{"text": text, "voice": voice or config.default_voice}`
2. POST to `{config.server_url}/tts` with `follow_redirects=True`
3. Check response `content-type` header:
   - If `audio/wav` (or any `audio/*`): read raw bytes
   - If `application/json` (or other): parse JSON, extract `audio_base64` or `audio` field, base64 decode
4. If `output_path` provided, write bytes to file
5. Return raw WAV bytes

**Retry Logic:**
```python
for attempt in range(config.max_retries):
    try:
        return await self._do_generate(text, voice, output_path)
    except (httpx.TimeoutException, httpx.TransportError, TTSAudioError) as e:
        if attempt == config.max_retries - 1:
            raise TTSGenerationError(
                f"TTS failed after {config.max_retries} retries: {e}"
            ) from e
        wait = 2 ** attempt * (1 + random.random())  # exp backoff + jitter
        await asyncio.sleep(wait)
```

**Hardcoded Voice List (26 voices):**
```python
FALLBACK_VOICES: list[VoiceInfo] = [
    {"id": "en_US-amy-medium", "name": "Amy", "language": "en-US", "gender": "female"},
    {"id": "en_US-joe-medium", "name": "Joe", "language": "en-US", "gender": "male"},
    {"id": "en_US-kathleen-medium", "name": "Kathleen", "language": "en-US", "gender": "female"},
    {"id": "en_US-lessac-medium", "name": "Lessac", "language": "en-US", "gender": "female"},
    {"id": "en_US-libritts_r-medium", "name": "LibriTTS R", "language": "en-US", "gender": "female"},
    {"id": "en_US-libritts-high", "name": "LibriTTS High", "language": "en-US", "gender": "female"},
    {"id": "en_GB-aru-medium", "name": "Aru", "language": "en-GB", "gender": "female"},
    {"id": "en_GB-jenny-medium", "name": "Jenny", "language": "en-GB", "gender": "female"},
    {"id": "en_GB-semper-medium", "name": "Semper", "language": "en-GB", "gender": "female"},
    {"id": "en_GB-vctk-medium", "name": "VCTK", "language": "en-GB", "gender": "female"},
    {"id": "en_GB-hf_female-medium", "name": "HF Female", "language": "en-GB", "gender": "female"},
    {"id": "en_GB-hf_male-medium", "name": "HF Male", "language": "en-GB", "gender": "male"},
    # ... 14 more voices covering en-US, en-GB, es, fr, de, ja, ko, zh
]
```

#### Error Handling
- `httpx.TimeoutException` → retry (up to max_retries) → `TTSGenerationError` if exhausted
- `httpx.HTTPStatusError` (non-2xx) → `TTSServerError` with status and body
- Missing `audio_base64` in JSON response → `TTSAudioError("Response missing audio content")`
- File write failure → `TTSAudioError("Cannot write audio to {path}")`

#### Configuration Options
- `pocket_tts.server_url`: TTS server base URL (default: `http://127.0.0.1:8120`)
- `pocket_tts.default_voice`: Default voice ID (default: `en_US-amy-medium`)
- `pocket_tts.max_retries`: Max retry attempts (default: 3)
- `pocket_tts.timeout_seconds`: Request timeout (default: 60)

---

### 3.4 Audio Pipeline (`audio_pipeline.py`)

#### Purpose
Transform script text into a complete audio file with associated word-level timestamp metadata, ready for Remotion caption overlays.

#### Responsibilities
- Split script text into sentences
- Group sentences into chunks (≤50 tokens each)
- Generate WAV per chunk via TTSClient
- Stitch chunks into single WAV with crossfade
- Extract word-level timestamps (uniform estimation fallback)
- Generate caption JSON in @remotion/captions format

#### Public API

```python
def split_sentences(text: str) -> list[str]:
    """Split text on sentence boundaries (. ! ? followed by space or end)."""

def group_into_chunks(
    sentences: list[str],
    max_tokens: int = 50,
    chars_per_token: float = 4.0,
) -> list[str]:
    """Group sentences into chunks respecting max_tokens constraint."""

async def generate_chunk_wavs(
    chunks: list[str],
    tts_client: TTSClient,
    voice: str,
    output_dir: str | Path,
) -> list[Path]:
    """Generate one WAV per chunk. Returns list of file paths."""

def stitch_wavs(
    chunk_paths: list[Path],
    output_path: str | Path,
    crossfade_ms: int = 50,
) -> Path:
    """Stitch chunk WAVs with crossfade using pydub."""

def extract_word_timestamps(
    audio_path: str | Path,
    script_text: str,
    sample_rate: int = 24000,
    words_per_second: float = 2.8,
) -> list[WordTimestamp]:
    """Extract word timestamps using uniform estimation fallback."""

def generate_caption_json(
    word_timestamps: list[WordTimestamp],
) -> list[CaptionEntry]:
    """Generate @remotion/captions-compatible JSON."""

async def process_audio_script(
    script_text: str,
    scene_id: str,
    output_dir: str | Path,
    tts_client: TTSClient,
    voice: str | None = None,
    config: PipelineConfig | None = None,
) -> SceneAudioMetadata:
    """Full pipeline: split → group → generate → stitch → timestamps → captions."""

class WordTimestamp(TypedDict):
    word: str
    start_ms: float
    end_ms: float

class CaptionEntry(TypedDict):
    text: str
    startMs: float
    endMs: float

class SceneAudioMetadata(TypedDict):
    scene_id: str
    audio_path: str
    duration_seconds: float
    duration_frames: int
    sample_rate: int
    word_timestamps: list[WordTimestamp]
    captions: list[CaptionEntry]
```

#### Internal Design

**Sentence Splitting Algorithm:**
```python
def split_sentences(text: str) -> list[str]:
    """Split on . ! ? followed by whitespace or end-of-string."""
    pattern = r"(?<=[.!?])\s+|(?<=[.!?])$"
    parts = re.split(pattern, text)
    return [p.strip() for p in parts if p.strip()]
```

**Chunk Grouping Algorithm:**
```python
def group_into_chunks(sentences: list[str], max_tokens: int, chars_per_token: float) -> list[str]:
    chunks, current = [], []
    current_token_count = 0

    for sentence in sentences:
        sentence_tokens = max(1, math.ceil(len(sentence) / chars_per_token))
        if current_token_count + sentence_tokens > max_tokens and current:
            chunks.append(" ".join(current))
            current, current_token_count = [], 0
        current.append(sentence)
        current_token_count += sentence_tokens

    if current:
        chunks.append(" ".join(current))
    return chunks
```

**Crossfade Stitching (pydub):**
```python
def stitch_wavs(chunk_paths, output_path, crossfade_ms=50):
    combined = AudioSegment.silent(duration=0)
    for path in chunk_paths:
        segment = AudioSegment.from_wav(path)
        if len(combined) == 0:
            combined = segment
        else:
            # Overlap last crossfade_ms of combined with first crossfade_ms of segment
            combined = combined.append(segment, crossfade=crossfade_ms)
    combined.export(output_path, format="wav")
    return Path(output_path)
```

**Uniform Timestamp Estimation (fallback):**
```python
def extract_word_timestamps(audio_path, script_text, sample_rate=24000, words_per_second=2.8):
    from pydub import AudioSegment
    audio = AudioSegment.from_wav(audio_path)
    duration_ms = len(audio)
    words = script_text.split()
    word_duration_ms = duration_ms / len(words)
    timestamps = []
    for i, word in enumerate(words):
        start_ms = i * word_duration_ms
        end_ms = (i + 1) * word_duration_ms
        timestamps.append(WordTimestamp(word=word, start_ms=start_ms, end_ms=end_ms))
    return timestamps
```

**Future Enhancement Path:**
- Replace uniform estimation with Whisper.cpp forced-alignment via subprocess
- Whisper returns per-word timestamps with high accuracy
- Fall back to uniform estimation when Whisper binary not available

#### Error Handling
- Empty script text → `AudioPipelineError("Script text is empty")`
- TTS failure for a chunk → captured as `ChunkGenerationError`, re-raised after all chunks attempted
- Stitch failure (corrupted WAV) → `AudioStitchError` with diagnostics
- Timestamp extraction on silent/mono audio → `TimestampExtractionError`
- Per-chunk TTS failures are logged individually; function raises on first failure unless `continue_on_error=True`

#### Configuration Options
- `pipeline.max_caption_tokens_per_chunk`: Max tokens per TTS chunk (default: 50)
- Crossfade duration: hardcoded `crossfade_ms=50` (tunable parameter)

---

### 3.5 Content Fetcher (`agents/content_fetcher.py`)

#### Purpose
Fetch GitHub content (PRs, issues, releases) via the `gh` CLI and return structured data.

#### Responsibilities
- Execute `gh pr view {url} --json title,body,additions,deletions,files,author,labels,comments,createdAt`
- Execute `gh issue view {url} --json title,body,labels,comments,author,createdAt,state`
- Execute `gh pr diff {url}` for diff content
- Parse JSON output into typed dicts
- Extract file-level diffs with line ranges

#### Public API

```python
async def fetch_github_pr(url: str) -> GitHubPR:
    """Fetch PR data from GitHub URL. Uses gh CLI subprocess."""

async def fetch_github_issue(url: str) -> GitHubIssue:
    """Fetch issue data from GitHub URL. Uses gh CLI subprocess."""

async def fetch_pr_diff(url: str) -> str:
    """Fetch raw diff for a PR."""

class GitHubPR(TypedDict):
    title: str
    body: str
    diff: str
    files: list[PRFile]
    author: str
    labels: list[str]
    comments: list[Comment]
    created_at: str
    additions: int
    deletions: int

class PRFile(TypedDict):
    path: str
    status: str  # added, modified, removed, renamed
    additions: int
    deletions: int

class Comment(TypedDict):
    author: str
    body: str
    created_at: str

class GitHubIssue(TypedDict):
    title: str
    body: str
    labels: list[str]
    comments: list[Comment]
    author: str
    created_at: str
    state: str  # open, closed
```

#### Internal Design
- Uses `asyncio.create_subprocess_exec` for `gh` CLI calls (NOT `subprocess.run` — avoids blocking event loop)
- JSON output from `gh` is parsed with `json.loads()`
- Diff output is captured as raw string (may be large; no parsing needed)
- URL validation: expects `https://github.com/{owner}/{repo}/pull/{number}` or `/issues/{number}`

#### Error Handling
- `gh` CLI not found → `GitHubCLINotFoundError("gh CLI not found on PATH")`
- Non-zero exit code → `GitHubAPIError(stderr)` with captured stderr
- JSON parse failure → `GitHubDataError("Invalid JSON from gh CLI")`
- Invalid URL format → `GitHubValidationError("URL must match ...")`

#### Configuration Options
- None (uses system `gh` CLI; authentication is pre-configured by user)

---

### 3.6 Content Classifier (`agents/content_classifier.py`)

#### Purpose
Analyze fetched GitHub content and classify it into a video type (PR summary, issue explainer, changelog, code walkthrough).

#### Responsibilities
- Accept fetched GitHubPR or GitHubIssue
- Use LLM to classify content type and extract key topics
- Return classification with confidence score
- Determine optimal video structure (scenes needed)

#### Public API

```python
async def classify_content(
    content: GitHubPR | GitHubIssue,
) -> ContentClassification:
    """Classify GitHub content into video type. Uses LLM."""

class ContentClassification(TypedDict):
    video_type: Literal["pr_summary", "issue_explainer", "changelog", "code_walkthrough"]
    title: str
    topics: list[str]
    complexity: Literal["low", "medium", "high"]
    suggested_scenes: list[str]
    confidence: float  # 0.0 - 1.0
```

#### Internal Design
- Constructs a structured LLM prompt containing the content metadata
- LLM returns JSON following the `ContentClassification` schema
- Confidence threshold: if < 0.6, fall back to a generic classification
- Uses the MCP LLM tool interface (not direct API call)

#### Error Handling
- LLM call failure → `ClassificationError("LLM classification failed: {e}")`
- Invalid LLM JSON response → `ClassificationError("Invalid classification JSON")`
- Low confidence → returns generic classification with `confidence < 0.6` flag

#### Configuration Options
- None (LLM provider is configured externally via MCP)

---

### 3.7 Script Writer (`agents/script_writer.py`)

#### Purpose
Generate a narrative script for the video based on classified GitHub content.

#### Responsibilities
- Accept classified content + video type
- Generate a well-structured script with natural language narrative
- Include code references, diff explanations, and call-to-action
- Output script text with scene annotations

#### Public API

```python
async def write_script(
    classification: ContentClassification,
    content: GitHubPR | GitHubIssue,
    style: ScriptStyle | None = None,
) -> ScriptResult:
    """Generate a narrative script for the video."""

class ScriptStyle(TypedDict):
    tone: Literal["professional", "casual", "technical", "enthusiastic"]
    target_audience: Literal["developers", "managers", "general"]
    max_duration_seconds: int  # influences script length

class ScriptResult(TypedDict):
    script_text: str  # full narrative text
    scenes: list[ScriptScene]  # annotated scene boundaries
    estimated_duration_seconds: float
    word_count: int

class ScriptScene(TypedDict):
    title: str
    text: str
    scene_type: Literal["title", "code", "diff", "bullet", "image", "comparison", "diagram", "outro"]
    estimated_duration_seconds: float
```

#### Internal Design
- Constructs LLM prompt with content, classification, and style preferences
- Prompt instructs LLM to return a script with scene markers
- Post-processes response to extract structured scene list
- Estimates duration: assumes 2.8 words/second average speaking rate

#### Error Handling
- LLM failure → `ScriptGenerationError("LLM script generation failed")`
- Script too short (< 50 words) → `ScriptValidationError("Script too short for video")`
- Script too long (> 540 words for 180s max) → automatic truncation with warning

#### Configuration Options
- `pipeline.max_video_duration_seconds` limits script length (default: 180s)

---

### 3.8 Scene Planner (`agents/scene_planner.py`)

#### Purpose
Transform a narrative script into a structured scene plan with precise timing, transitions, and visual layout.

#### Responsibilities
- Accept script with scene annotations
- Allocate frame-accurate timing based on audio duration
- Assign transitions between scenes
- Generate scene plan JSON compatible with Remotion inputProps
- Select transition type per scene boundary

#### Public API

```python
async def plan_scenes(
    script: ScriptResult,
    audio_metadata: SceneAudioMetadata | None = None,
    fps: int = 30,
) -> ScenePlan:
    """Plan scene structure from script and audio timing."""

class ScenePlan(TypedDict):
    total_duration_frames: int
    fps: int
    scenes: list[PlannedScene]
    transitions: list[PlannedTransition]

class PlannedScene(TypedDict):
    index: int
    type: str  # scene type literal
    start_frame: int
    duration_frames: int
    props: dict  # scene-specific props
    audio_track: AudioTrackRef | None

class PlannedTransition(TypedDict):
    from_scene_index: int
    to_scene_index: int
    type: str  # fade, slide, zoom, wipe, dissolve, flip, scale, rotate, blur, morph, glitch, warp
    duration_frames: int

class AudioTrackRef(TypedDict):
    src: str
    start_frame: int
    duration_frames: int
```

#### Internal Design
- Matches script scenes to audio word timestamps for frame-accurate cuts
- Allocates transition duration (default 15 frames at 30fps = 0.5s)
- Transition type selection heuristic:
  - Title → next scene: `fade`
  - Code → next code: `slide`
  - Scene type change: `wipe` or `dissolve`
  - Outro: `fade`
- Overlap: each transition overlaps the end of one scene with the start of the next (transition duration is subtracted from both scenes)

#### Error Handling
- Audio-scene duration mismatch > 10% → `ScenePlanningError("Audio duration mismatch")`
- No scenes planned → `ScenePlanningError("Script has zero scenes")`
- Transition duration > scene duration → automatically reduced to `scene_duration / 3`

#### Configuration Options
- `pipeline.default_fps`: Frames per second (default: 30)

---

### 3.9 Composition Builder (`agents/composition_builder.py`)

#### Purpose
Assemble the final Remotion `inputProps` JSON from scene plan, audio map, and image map.

#### Responsibilities
- Combine scene plan, audio file paths, and image paths into a single inputProps object
- Validate against Zod schema (discriminated union)
- Resolve asset paths to absolute paths
- Apply style tokens (colors, fonts, code theme)

#### Public API

```python
async def build_composition(
    scene_plan: ScenePlan,
    audio_map: dict[str, SceneAudioMetadata],  # scene_id → metadata
    image_map: dict[str, str],  # scene_id → image path
    style: StyleConfig | None = None,
) -> CompositionResult:
    """Build complete inputProps JSON."""

class CompositionResult(TypedDict):
    composition_id: str  # matches Remotion composition ID
    input_props: dict  # full inputProps JSON (passes Zod validation)
    asset_paths: list[str]  # all referenced asset paths
    estimated_render_time_seconds: float

class StyleConfig(TypedDict):
    primary_color: str  # hex color
    font: str  # Google Font name
    code_theme: str  # Shiki theme name
```

#### Internal Design
- Walks scene plan and maps each scene to its audio track + image
- Resolves all paths to absolute using `Path.resolve()`
- Applies style defaults if not provided:
  - `primary_color`: `"#6C63FF"`
  - `font`: `"Inter"`
  - `code_theme`: `"github-dark"`
- Validates the assembled input_props against Zod schema via Node.js subprocess (`npx tsx -e`)
- On validation failure, returns detailed field-level errors

#### Error Handling
- Missing audio for scene → `CompositionError("Scene {index} has no audio track")`
- Missing image for image-type scene → `CompositionError("Image scene {index} missing image")`
- Zod validation failure → `CompositionValidationError(field_errors)` with list of errors
- Asset file not found → `CompositionError("Asset not found: {path}")`

#### Configuration Options
- `style.*` from config (if extended in future)

---

### 3.10 Image Generator (`agents/image_generator.py`)

#### Purpose
Generate or source visual assets for scenes, using a 3-tier system: AI generation, stock photos, or code-only rendering.

#### Responsibilities
- Determine which scenes need images (title backgrounds, illustration, comparison visuals)
- Select tier based on content type and config
- Call AI image API or stock photo API or skip
- Return image paths

#### Public API

```python
async def generate_images(
    scene_plan: ScenePlan,
    output_dir: str | Path,
) -> dict[str, str]:  # scene_index → image_path

async def generate_ai_image(
    prompt: str,
    output_path: str | Path,
    provider: str = "stable_diffusion",
) -> Path:
    """Generate image via AI API."""

async def fetch_stock_image(
    query: str,
    output_path: str | Path,
    provider: str = "pexels",
) -> Path:
    """Fetch stock photo from Pexels/Pixabay."""

def scene_to_image_prompt(scene: PlannedScene) -> str | None:
    """Generate a text prompt for an image based on scene type and props."""
```

#### Internal Design

**3-Tier Asset System:**
1. **AI-Generated** (enabled if `assets.ai_generation.enabled`): For title backgrounds, custom diagrams, conceptual illustrations
2. **Stock Photos** (enabled if `assets.stock_photos.enabled`): For tech backgrounds, abstract visuals
3. **Code-Only** (default): No images; scene renders with code/diff/bullet text only

**Scene-to-Prompt Mapping:**
| Scene Type | Prompt Strategy |
|------------|-----------------|
| `title` | Generate from script topic + title |
| `code` | No image (code is the visual) |
| `diff` | No image (diff is the visual) |
| `bullet` | Generate from topic keywords |
| `image` | Scene provides its own config |
| `comparison` | No image (comparison is the visual) |
| `diagram` | No image (uses @shetty4l/diagrams) |
| `outro` | Logo/brand image |

#### Error Handling
- AI API failure → log warning, fall back to stock photo
- Stock API failure → log warning, skip image (scene renders without background)
- Rate limiting → add 1s delay before retry (no exponential backoff)
- Invalid image data → `ImageGenerationError("API returned invalid image data")`

#### Configuration Options
- `assets.ai_generation.enabled` (bool)
- `assets.ai_generation.provider` (string)
- `assets.stock_photos.enabled` (bool)
- `assets.stock_photos.provider` (string)

---

### 3.11 Publisher (`agents/publisher.py`)

#### Purpose
Publish the generated video back to GitHub as a PR comment with markdown body linking to the video.

#### Responsibilities
- Upload video to configured storage (local path or object storage)
- Construct markdown comment with video link, description, and metadata
- Post comment via `gh pr comment {pr_number} --body {markdown}`
- Handle authentication and error responses

#### Public API

```python
async def publish_video(
    video_path: str | Path,
    target: PublishTarget,
    metadata: PublishMetadata,
) -> PublishResult:
    """Publish video to GitHub PR as comment."""

class PublishTarget(TypedDict):
    type: Literal["github_pr", "github_issue"]
    url: str  # full GitHub URL

class PublishMetadata(TypedDict):
    title: str
    description: str
    duration_seconds: float
    scenes: int

class PublishResult(TypedDict):
    success: bool
    comment_url: str | None
    error: str | None
```

#### Internal Design
1. Validate video file exists and has reasonable size (> 1KB, < 500MB)
2. Construct markdown body:
   ```markdown
   ## 🎬 VideoForge Summary
   **{title}**
   {description}
   - Duration: {duration_seconds}s
   - Scenes: {scenes}
   - [Download Video]({video_url})
   ```
3. Execute `gh pr comment {pr_number} --body '{markdown}'` via subprocess
4. Capture comment URL from output

#### Error Handling
- Video file not found → `PublishError("Video file not found: {path}")`
- gh CLI failure → `PublishError("Failed to post comment: {stderr}")`
- Video too large → `PublishError("Video exceeds size limit")`
- Missing target URL → `PublishError("No target URL provided")`

#### Configuration Options
- `github.auto_post_pr_comments`: Enable/disable auto-publishing (default: true)

---

### 3.12 Render Executor (`tools/render_executor.py`)

#### Purpose
Execute Remotion rendering via `@remotion/renderer` API, managing the Node.js subprocess and monitoring progress.

#### Responsibilities
- Call `renderMedia()` or `selectComposition()` from `@remotion/renderer`
- Pass inputProps JSON via stdin or environment variable
- Monitor render progress via callbacks
- Handle render cancellation via kill switch polling
- Return output video path

#### Public API

```python
async def render_video(
    composition_id: str,
    input_props: dict,
    output_path: str | Path | None = None,
    fps: int = 30,
    resolution: tuple[int, int] = (1920, 1080),
    codec: str = "h264",
) -> RenderResult:
    """Render a Remotion composition with given inputProps."""

async def select_composition(
    composition_id: str,
    input_props: dict,
) -> CompositionMetadata:
    """Get composition metadata (duration, fps, dimensions)."""

class RenderResult(TypedDict):
    output_path: str
    duration_frames: int
    duration_seconds: float
    render_time_seconds: float
    fps: int
    resolution: tuple[int, int]
    codec: str

class CompositionMetadata(TypedDict):
    id: str
    duration_in_frames: int
    fps: int
    width: int
    height: int
```

#### Internal Design

**Render Execution Flow:**
1. Validate composition exists in Remotion project
2. Build inputProps JSON → write to temp file
3. Execute `npx remotion render` subprocess with:
   - `--props` pointing to temp JSON file
   - `--codec` from config
   - `--output` for output path
   - `--log verbose` for progress
4. Poll stdout for progress updates (frame count / total)
5. Check kill switch between frames
6. On completion, verify output file exists

**Subprocess Command Construction:**
```python
cmd = [
    "npx", "remotion", "render",
    composition_id,
    str(output_path),
    "--props", str(props_path),
    "--codec", codec,
    "--log", "verbose",
]
```

#### Error Handling
- Subprocess non-zero exit → `RenderExecutionError(stderr)` with full stderr
- Output file not created → `RenderExecutionError("Renderer did not produce output")`
- Kill switch detected → `RenderCancelledError("Cancelled by kill switch")` with partial output deleted
- Composition not found → `RenderExecutionError("Composition '{id}' not registered in Root.tsx")`
- Memory limit exceeded → `RenderExecutionError("Remotion process OOM")`

#### Configuration Options
- `pipeline.default_fps` (default: 30)
- `pipeline.default_resolution` (default: (1920, 1080))
- `pipeline.default_codec` (default: "h264")

---

### 3.13 Frame Reviewer (`tools/frame_reviewer.py`)

#### Purpose
Per-frame visual analysis of the rendered video through 5 progressive levels. Catches animation jitter, element overlap, frozen frames, transition artifacts, and temporal inconsistencies that global metrics miss. Every frame is analyzed — not sampled.

#### Responsibilities
- **L1 Frame Integrity**: Detect corrupt, black, frozen, and dropped frames
- **L2 Element Boundary**: Detect element clipping, overlapping, and zero-opacity at expected-visible frames
- **L3 Animation Smoothness**: Detect position jitter, opacity flicker, scale oscillation between consecutive frames
- **L4 Transition Completeness**: Detect incomplete transitions, overlapping scenes, abrupt cuts where transitions expected
- **L5 Temporal Consistency**: Detect element disappearance/reappearance, caption-frame mismatch, scene content mismatch

#### Public API

```python
class FrameReviewReport(TypedDict):
    video_path: str
    passed: bool
    levels: dict[int, LevelResult]  # 1-5
    passed_frames: int
    total_frames: int
    failing_frames: list[int]
    summary: str

class LevelResult(TypedDict):
    level: int
    name: str
    passed: bool
    failing_frames: list[int]  # frame numbers
    details: list[FrameIssue]

class FrameIssue(TypedDict):
    frame: int
    issue_type: str  # "corrupt" | "black" | "frozen" | "overlap" | "clip" | "jitter" | "flicker" | "incomplete_transition" | "missing_element" | "caption_mismatch"
    severity: Literal["error", "warning", "info"]
    description: str
    location: str | None  # e.g. "x=320,y=240,w=100,h=60"


async def review_frames(
    video_path: str | Path,
    input_props: dict | None = None,
    config: FrameReviewConfig | None = None,
) -> FrameReviewReport:
    """Run 5-level frame review on the rendered video.

    Args:
        video_path: Path to the rendered MP4.
        input_props: Remotion inputProps (provides scene boundaries, caption timings, expected transition durations).
        config: Review thresholds per level.

    Returns:
        Structured report with per-level results and per-frame issues.
    """
```

#### Internal Design

**Level 1 — Frame Integrity:**
```python
async def check_frame_integrity(video_path: str) -> LevelResult:
    """Use FFmpeg filters to detect corrupt, black, frozen frames."""
    # Black frames: ffmpeg -vf blackdetect=black_min_duration=0.1:...
    # Frozen frames: ffmpeg -vf freezedetect=noise=0.001:duration=1
    # Corrupt frames: ffmpeg -err_detect explode (checks CRC in bitstream)
    # Returns per-frame issues with frame numbers
```

**Level 2 — Element Boundary:**
```python
async def check_element_boundaries(
    video_path: str,
    input_props: dict
) -> LevelResult:
    """Check for clipped/overlapping elements using Remotion render metadata.

    Remotion can output element bounding boxes at each frame via
    <Composition> with `element` attribute. These are compared against
    viewport boundaries (1920x1080) and pairwise IoU.
    """
    # For each frame, compute bounding boxes from Remotion metadata
    # IoU > 0.3 between any two elements = overlap warning
    # Any element with bbox outside viewport = clipping error
```

**Level 3 — Animation Smoothness:**
```python
async def check_animation_smoothness(
    video_path: str,
    input_props: dict
) -> LevelResult:
    """Detect jitter, flicker, oscillation by analyzing frame-to-frame deltas.

    Jitter: element jumps >3px between consecutive frames with no easing curve.
    Flicker: opacity oscillates every frame (e.g. 1→0→1→0).
    Scale oscillation: scale alternates frame-to-frame.
    """
    # Extract element positions/tracking data from Remotion metadata
    # Apply high-pass filter to detect >3px jumps not explained by easing
    # Check for alternating patterns in opacity/scale values
```

**Level 4 — Transition Completeness:**
```python
async def check_transition_completeness(
    video_path: str,
    input_props: dict
) -> LevelResult:
    """Verify all transitions complete as specified.

    Transition type from inputProps.scenes[N].transition_out determines
    expected duration/behavior. Compare actual frame sequence against spec.
    """
    # For each transition boundary:
    #   1. Detect where entering scene becomes fully visible
    #   2. Compare actual transition duration to spec ±1 frame
    #   3. Check alpha blend at midpoint (should be ~0.5)
    #   4. Detect hard cuts where transition_type != "none"
```

**Level 5 — Temporal Consistency:**
```python
async def check_temporal_consistency(
    video_path: str,
    input_props: dict
) -> LevelResult:
    """Check element persistence, caption sync, and scene-content matching.

    Uses pixel-change masks to detect elements that disappear then reappear.
    Compares caption timing from inputProps against frame-accurate word schedule.
    Cross-references scene type against content detected via OCR/classification.
    """
    # Element persistence: track pixel-change regions across frames
    # Caption sync: verify highlighted caption word matches frame number
    # Scene content: for "code" scenes, verify code-like pixels exist
```

#### FFmpeg / FFprobe Integration

All Level 1 checks use FFmpeg filters natively. Levels 2-5 additionally use Remotion's frame metadata export (element bounding boxes per frame) which is emitted during render when `--enable-frame-metadata` flag is passed.

```python
# Frame extraction for per-frame pixel analysis
FRAME_EXTRACT_CMD = [
    "ffmpeg", "-i", video_path,
    "-vf", "fps=1,showinfo",  # 1 frame per second sampling for L2-L5
    "-f", "rawvideo",
    "-pix_fmt", "rgb24",
    "-"
]
```

#### Level Aggregation

A frame must pass L1 before L2 is checked, L2 before L3, etc. If L1 fails for a frame, that frame is skipped for L2-L5. The overall report shows:

- **Passed**: All frames passed all 5 levels
- **Passed with warnings**: Some frames had L3-L5 warnings (acceptable)
- **Failed**: Any frame failed L1 or L2

#### Error Handling

| Scenario | Behavior |
|----------|----------|
| Video file not found | `ReviewError("Video file not found at path")` |
| FFmpeg not available | `ReviewError("FFmpeg not found on PATH. Required for frame extraction.")` |
| input_props not provided | L2-L5 checks are skipped; L1 runs with degraded accuracy |
| Frame metadata not embedded | L2-L5 use pixel-diff heuristics instead of exact element boundaries |
| Corrupt bitstream mid-video | L1 reports exact frame range of corruption; review continues on remaining frames |

#### Configuration

```python
# pyproject.toml or config.yaml section
[tool.videoforge.review.frames]
enabled = true
max_black_frames_pct = 1.0       # L1: % of frames allowed to be black
max_frozen_duration_s = 2.0      # L1: max frozen duration
max_overlap_iou = 0.3             # L2: max overlap IoU
max_jitter_px = 3.0              # L3: max position jump between frames
transition_tolerance_frames = 1  # L4: tolerance for transition duration mismatch
caption_sync_tolerance_ms = 150  # L5: max caption timing offset
```

---

### 3.14 Webhook Handler (`webhook/handler.py`)

#### Purpose
Handle incoming GitHub webhook events and trigger pipeline execution.

#### Responsibilities
- Receive HTTP POST requests on configurable endpoint
- Verify HMAC-SHA256 signature
- Parse event type from `X-GitHub-Event` header
- Dispatch to appropriate pipeline (push, pull_request, issues, release)
- Return 200/202 on acceptance, 4xx on validation failure

#### Public API

```python
async def handle_webhook(request: Request) -> Response:
    """Main webhook handler. Verifies signature, dispatches event."""

class WebhookEvent(TypedDict):
    event_type: str  # push, pull_request, issues, release
    action: str | None  # opened, synchronize, created, published
    payload: dict  # raw GitHub event payload
    delivery_id: str  # X-GitHub-Delivery header

class WebhookConfig(BaseModel):
    secret: str  # HMAC secret
    endpoint: str = "/webhook"  # URL path
```

#### Internal Design

**HMAC-SHA256 Verification:**
```python
def verify_signature(payload: bytes, signature_header: str, secret: str) -> bool:
    """Verify HMAC-SHA256 signature from GitHub webhook."""
    expected = "sha256=" + hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)
```

**Event Dispatch:**
```python
EVENT_DISPATCH = {
    "pull_request": handle_pr_event,
    "issues": handle_issue_event,
    "push": handle_push_event,
    "release": handle_release_event,
}
```

- Returns 202 Accepted after starting pipeline (non-blocking)
- Returns 400 Bad Request on invalid signature
- Returns 422 Unprocessable if event type not supported

#### Error Handling
- Missing signature header → `WebhookError("Missing X-Hub-Signature-256")`
- Signature mismatch → `WebhookError("Signature verification failed")` (401)
- Unknown event type → `WebhookError("Unsupported event: {event_type}")` (422)
- Payload too large (> 25MB) → `WebhookError("Payload exceeds limit")` (413)

#### Configuration Options
- `github.webhook_secret_env`: Env var name containing HMAC secret (default: `VIDEOFORGE_WEBHOOK_SECRET`)
- Webhook endpoint path: hardcoded to `/webhook`

---

### 3.15 Exceptions Module (`exceptions.py`)

#### Purpose
Define all typed exceptions for the VideoForge Python package.

#### Hierarchy

```
Exception
├── VideoForgeError (base)
│   ├── ConfigurationError
│   │   ├── ConfigFileNotFound
│   │   ├── ConfigValidationError
│   │   └── ConfigParseError
│   ├── TTSBaseError
│   │   ├── TTSConnectionError
│   │   ├── TTSGenerationError
│   │   ├── TTSServerError
│   │   └── TTSAudioError
│   ├── AudioPipelineError
│   │   ├── SentenceSplitError
│   │   ├── ChunkGenerationError
│   │   ├── AudioStitchError
│   │   └── TimestampExtractionError
│   ├── GitHubBaseError
│   │   ├── GitHubCLINotFoundError
│   │   ├── GitHubAPIError
│   │   ├── GitHubDataError
│   │   └── GitHubValidationError
│   ├── ClassificationError
│   ├── ScriptGenerationError
│   │   └── ScriptValidationError
│   ├── ScenePlanningError
│   ├── CompositionError
│   │   └── CompositionValidationError
│   ├── ImageGenerationError
│   ├── RenderExecutionError
│   │   └── RenderCancelledError
│   ├── PublishError
│   ├── ReviewError
│   └── WebhookError
```

#### Design Principles
- All exceptions inherit from `VideoForgeError` for catch-all handling
- Each module has a specific base exception (e.g., `TTSBaseError`)
- Constructor includes `message: str`, optional `cause: Exception`, optional `context: dict`
- All exceptions can be serialized via `.to_dict()` → `{"error": message, "type": type_name, "context": context}`

---

### 3.17 Fact Checker (`agents/fact_checker.py`)

Validates script claims against source content before scene planning.

#### Purpose
Prevent hallucinated code references, incorrect technical terminology, and misattributed changes from reaching the video. Catches errors at the text stage (cheap) rather than after TTS generation (expensive).

#### Public API

```python
def fact_check_script(
    script: ScriptData,
    source: GitHubSourceData,
    config: FactCheckConfig | None = None,
) -> FactCheckReport:
    """Validate all factual claims in the script against source content.

    Args:
        script: The generated video script with scene-by-scene narration.
        source: Source content from GitHub (PR diff, issue body, file list).
        config: Optional configuration (L1 advisory / L2 blocking).

    Returns:
        FactCheckReport with per-claim verification results.

    Raises:
        FactCheckError: If the checker itself fails (e.g., upstream API error).
    """

def extract_claims_from_script(script: ScriptData) -> list[Claim]:
    """Parse the script and extract all factual claims.

    A claim is any statement that asserts something about the code:
    - "This function validates tokens" → claim: function validation exists
    - "Line 42 adds error handling" → claim: line 42 is an error handler
    - "The API now returns 401" → claim: API returns 401 status
    """

def verify_claim_against_source(claim: Claim, source: GitHubSourceData) -> Verification:
    """Verify a single claim against the source content.

    Uses pattern matching, substring search, and LLM analysis to determine
    whether the claim is supported by the source.
    """
```

#### Internal Design

1. **Claim Extraction**: Parse the script for factual statements using pattern matching:
   - Function/method references: words followed by `()` or `()`
   - Line references: "line N", "on line N"
   - Behavioral descriptions: "validates", "checks", "returns", "throws"
   - File references: file paths, module names
2. **Source Parsing**: Extract function names, API endpoints, variable names, and imports from the PR diff
3. **Verification**: For each claim, check if the referenced element exists in the source:
   - Function names → grep the diff
   - Line references → check the specified line
   - Behavioral claims → use LLM to compare claim against code context
4. **Report Generation**: Aggregate all verifications into a structured report

#### Error Handling

- Claim extraction failure → skip the claim, add to `warnings`
- Source parsing failure → raise `FactCheckError`
- LLM timeout → fall back to pattern-only checking
- Empty script or source → return empty report (all pass)

#### Configuration

```yaml
validation:
  fact_checker:
    enabled: true
    mode: "advisory"  # "advisory" (L1) or "blocking" (L2)
    max_claims: 50
    llm_timeout_seconds: 15
```

### 3.18 Logic Checker (`agents/logic_checker.py`)

Validates scene plan narrative coherence and logical consistency before asset generation.

#### Purpose
Ensure the video tells a coherent story: context → problem → solution → impact. Catch logical leaps, missing prerequisites, and pacing issues before rendering.

#### Public API

```python
def logic_check_scenes(
    script: ScriptData,
    scene_plan: ScenePlan,
    source: GitHubSourceData,
    config: LogicCheckConfig | None = None,
) -> LogicCheckReport:
    """Validate narrative coherence and logical flow of the scene plan.

    Args:
        script: Full video script.
        scene_plan: Planned scene sequence with types, durations, transitions.
        source: Source content from GitHub.
        config: Optional configuration (L1/L2 mode).

    Returns:
        LogicCheckReport with per-scene and global coherence checks.
    """

def check_narrative_arc(scene_plan: ScenePlan) -> NarrativeAssessment:
    """Assess whether the scene sequence forms a coherent narrative arc.

    Validates that the 4 phases are present:
    1. Context (title/orientation)
    2. Problem (what changed, why)
    3. Solution (the code/diff/diagram)
    4. Impact (what this means, next steps)
    """

def check_cause_effect(script: ScriptData, scene_plan: ScenePlan) -> list[CausalIssue]:
    """Check that all cause/effect claims are supported by the scene content.

    Example: If the script says "adding caching reduces latency", but no scene
    shows a caching implementation, this is flagged.
    """

def check_scene_ordering(scene_plan: ScenePlan, diff_files: list[str]) -> list[OrderingIssue]:
    """Verify scenes are in a logical order.

    Rules:
    - Code is introduced before it's shown modified
    - Tests follow implementation (not precede)
    - Simple concepts precede complex ones
    - Summary/outro is always last
    """
```

#### Internal Design

1. **Narrative Arc Detection**: Classify each scene into one of 4 narrative roles (context, problem, solution, impact) based on its type and content. Flag if any role is missing.
2. **Causal Chain Validation**: Extract "because X, Y" and "so that Z" patterns from the script. For each, verify there's a scene that makes the causal relationship visible.
3. **Prerequisite Check**: Build a dependency graph of concepts mentioned across scenes. Flag if a scene references a concept (e.g., "JWT token") that wasn't introduced in a prior scene.
4. **Pacing Analysis**: Compute per-scene information density (claims per second). Flag scenes that are too dense (>1 claim/sec) or too sparse (<0.1 claim/sec).

#### Error Handling

- Scene plan empty → skip all checks, return warnings
- Script and scene plan length mismatch → raise `LogicCheckError`
- Unrecognized scene type → treat as "context" role

#### Configuration

```yaml
validation:
  logic_checker:
    enabled: true
    mode: "advisory"
    min_scene_duration: 2
    max_scene_duration: 30
    max_density_claims_per_sec: 1.0
```

### 3.19 Remotion Project (TypeScript/React)

#### Purpose
Video composition and rendering engine. Takes inputProps JSON and produces rendered video output.

#### 3.16.1 Root Entry (`src/index.ts`, `src/Root.tsx`)

**`index.ts`**:
```typescript
import { registerRoot } from "remotion";
import { Root } from "./Root";
registerRoot(Root);
```

**`Root.tsx`**:
```typescript
import { Composition } from "remotion";
import { CodeWalkthrough } from "./compositions/CodeWalkthrough";
import { PRSummary } from "./compositions/PRSummary";
import { IssueExplainer } from "./compositions/IssueExplainer";
import { ChangelogVideo } from "./compositions/ChangelogVideo";

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="CodeWalkthrough"
        component={CodeWalkthrough}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="PRSummary"
        component={PRSummary}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="IssueExplainer"
        component={IssueExplainer}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="ChangelogVideo"
        component={ChangelogVideo}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
```

#### 3.16.2 Compositions

Each composition is a React component that:
- Accepts `inputProps` typed via Zod schema
- Uses `<TransitionSeries>` for scene transitions
- Renders scenes sequentially with their audio tracks
- Applies captions overlay

**CodeWalkthrough** — Step-through of a code change with highlighting
**PRSummary** — Overview of a pull request with diff, stats, author
**IssueExplainer** — Explanation of a GitHub issue with reproduction steps
**ChangelogVideo** — Release changelog with version highlights

#### 3.16.3 Scene Components (8)

Each scene component:
- Exports a Zod schema for its props
- Accepts `durationInFrames` (derived from audio timing)
- Has entry animation driven by `useCurrentFrame()` + `interpolate()`
- Handles position/sizing via `<AbsoluteFill>` + CSS

| Scene | File | Description |
|-------|------|-------------|
| TitleScene | `scenes/TitleScene.tsx` | Video title with subtitle, animated entry |
| CodeScene | `scenes/CodeScene.tsx` | Syntax-highlighted code with optional line highlighting |
| DiffScene | `scenes/DiffScene.tsx` | Side-by-side or unified diff view |
| BulletScene | `scenes/BulletScene.tsx` | Bullet points with staggered reveal |
| ImageScene | `scenes/ImageScene.tsx` | Full-bleed image with caption overlay |
| ComparisonScene | `scenes/ComparisonScene.tsx` | Before/after side-by-side with labels |
| DiagramScene | `scenes/DiagramScene.tsx` | Animated diagram via @shetty4l/diagrams or SVG |
| OutroScene | `scenes/OutroScene.tsx` | End card with title and CTA |

**Scene Prop Patterns:**
```typescript
// Each scene follows this pattern
import { z } from "zod";
import { AbsoluteFill, useCurrentFrame, interpolate, spring } from "remotion";

export const TitleSceneSchema = z.object({
  type: z.literal("title"),
  title: z.string(),
  subtitle: z.string().optional(),
  duration: z.number(),
});

type TitleSceneProps = z.infer<typeof TitleSceneSchema>;

export const TitleScene: React.FC<TitleSceneProps & { durationInFrames: number }> = ({
  title,
  subtitle,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });
  const slideUp = spring({ frame, fps: 30, config: { damping: 12 } });

  return (
    <AbsoluteFill style={{ opacity, transform: `translateY(${(1 - slideUp) * 50}px)` }}>
      <h1>{title}</h1>
      {subtitle && <h2>{subtitle}</h2>}
    </AbsoluteFill>
  );
};
```

**Animation Patterns:**
| Pattern | Implementation | Use Case |
|---------|---------------|----------|
| Fade in | `interpolate(frame, [0, 15], [0, 1])` | Text, images |
| Slide up | `spring({ frame, config: { damping: 12 } })` | Title, bullets |
| Scale | `interpolate(frame, [0, 20], [0.8, 1])` | Cards, panels |
| Typewriter | Character-by-character reveal | Code lines |
| Staggered | `frame - index * 5` delay per item | Bullet lists, gallery |

#### 3.16.4 Transition Components (12)

Each transition implements `TransitionPresentation` from `@remotion/transitions`:

```typescript
interface TransitionPresentation<Props> {
  component: React.FC<{
    children: React.ReactNode;
    presentationProgress: number;  // 0 → 1
    presentationDirection: "entering" | "exiting";
  } & Props>;
  props?: Props;
}
```

| Transition | Effect | Duration (frames) |
|------------|--------|-------------------|
| FadeTransition | Crossfade | 15 |
| SlideTransition | Slide in from direction | 20 |
| ZoomTransition | Zoom in/out | 20 |
| WipeTransition | Wipe from edge | 15 |
| DissolveTransition | Dissolve through white | 10 |
| FlipTransition | 3D flip | 25 |
| ScaleTransition | Scale + fade | 15 |
| RotateTransition | Rotate + fade | 20 |
| BlurTransition | Blur in/out | 10 |
| MorphTransition | Shape morph | 30 |
| GlitchTransition | Glitch effect | 8 |
| WarpTransition | Perspective warp | 20 |

**Transition Implementation Pattern:**
```typescript
export const FadeTransition: TransitionPresentation<Record<string, never>> = {
  component: ({ children, presentationProgress, presentationDirection }) => {
    const opacity =
      presentationDirection === "entering"
        ? interpolate(presentationProgress, [0, 1], [0, 1])
        : interpolate(presentationProgress, [0, 1], [1, 0]);

    return <div style={{ opacity }}>{children}</div>;
  },
  props: {},
};
```

#### 3.16.5 Shared Components (4)

| Component | File | Purpose |
|-----------|------|---------|
| CaptionOverlay | `components/CaptionOverlay.tsx` | TikTok-style word highlighting via `createTikTokStyleCaptions()` |
| AnimatedText | `components/AnimatedText.tsx` | Text with reveal animation (typewriter, fade, slide) |
| CodeBlock | `components/CodeBlock.tsx` | Syntax-highlighted code block with optional line numbers |
| DiffView | `components/DiffView.tsx` | Unified diff view with green/red line highlighting |

**CaptionOverlay Integration:**
```typescript
import { createTikTokStyleCaptions } from "@remotion/captions";
import { useCurrentFrame } from "remotion";

// Inside composition component:
const frame = useCurrentFrame();
const captions = createTikTokStyleCaptions({
  captions: inputProps.captions,
  currentFrame: frame,
  fps: 30,
});
// captions contains per-word highlighted segments
```

---

## 4. Data Flow

### 4.1 GitHub PR Explainer Workflow

```
GitHub Webhook
     │
     ▼
┌─────────────────────────────────┐
│  Webhook Handler                │
│  └─ Verify HMAC-SHA256 signature│
│  └─ Parse event type            │
│  └─ Extract PR URL              │
└──────────┬──────────────────────┘
           │ event payload
           ▼
┌─────────────────────────────────┐
│  PHASE 1: INGEST                │
│  └─ Content Fetcher             │
│     └─ gh pr view {url} --json  │
│     └─ gh pr diff {url}         │
│     └─ Returns GitHubPR {        │
│           title, body, diff,     │
│           files, author,         │
│           labels, comments       │
│         }                        │
└──────────┬──────────────────────┘
           │ GitHubPR
           ▼
┌─────────────────────────────────┐
│  PHASE 2: RESEARCH              │
│  └─ Content Classifier          │
│     └─ LLM: analyze content     │
│     └─ Returns ContentClassification {
│           video_type, title,    │
│           topics, complexity,   │
│           suggested_scenes      │
│         }                       │
└──────────┬──────────────────────┘
           │ ContentClassification
           ▼
┌─────────────────────────────────┐
│  PHASE 3: SCRIPT                │
│  └─ Script Writer               │
│     └─ LLM: generate narrative  │
│     └─ Returns ScriptResult {   │
│           script_text,          │
│           scenes[],             │
│           estimated_duration    │
│         }                       │
└──────────┬──────────────────────┘
           │ ScriptResult
           ▼
┌─────────────────────────────────┐
│  PHASE 4: FACT CHECK            │
│  └─ Fact Checker                │
│     └─ Extract claims from      │
│     │  script text              │
│     └─ Verify against PR diff   │
│     │  Function/API names       │
│     │  Behavior accuracy        │
│     │  Terminology correctness  │
│     │  Change attribution       │
│     └─ Returns FactCheckReport  │
│        (L1: advisory, L2:       │
│         blocking with report)   │
└──────────┬──────────────────────┘
           │ FactCheckReport + ScriptResult
           ▼
┌─────────────────────────────────┐
│  PHASE 5: SCENE PLAN            │
│  └─ Scene Planner               │
│     └─ Match script to audio    │
│     └─ Allocate frames          │
│     └─ Select transitions       │
│     └─ Returns ScenePlan        │
└──────────┬──────────────────────┘
           │ ScenePlan + ScriptResult
           ▼
┌─────────────────────────────────┐
│  PHASE 6: LOGIC CHECK           │
│  └─ Logic Checker               │
│     └─ Narrative arc assessment │
│     │  Context → Problem →      │
│     │  Solution → Impact        │
│     └─ Cause/effect validation  │
│     └─ Scene ordering check     │
│     └─ Pacing analysis          │
│     └─ Returns LogicCheckReport │
└──────────┬──────────────────────┘
           │ LogicCheckReport + ScenePlan
           ▼
┌─────────────────────────────────┐
│  PHASE 7: AUDIO                 │
│  └─ Audio Pipeline              │
│     └─ split_sentences()        │
│     └─ group_into_chunks()      │
│     └─ generate_chunk_wavs()    │
│     └─ stitch_wavs()            │
│     └─ extract_word_timestamps()│
│     └─ generate_caption_json()  │
│     └─ Returns SceneAudioMetadata
└──────────┬──────────────────────┘
           │ SceneAudioMetadata[]
           ▼
┌─────────────────────────────────┐
│  PHASE 8: ASSETS                │
│  └─ Image Generator             │
│     └─ AI generation / Stock    │
│     └─ Returns image_map        │
└──────────┬──────────────────────┘
           │ image_map (scene_id → path)
           ▼
┌─────────────────────────────────┐
│  PHASE 9: COMPOSE               │
│  └─ Composition Builder         │
│     └─ Assemble inputProps      │
│     └─ Validate against Zod     │
│     └─ Returns CompositionResult│
└──────────┬──────────────────────┘
           │ inputProps JSON
           ▼
┌─────────────────────────────────┐
│  PHASE 10: RENDER               │
│  └─ Render Executor             │
│     └─ npx remotion render      │
│     └─ Poll kill switch         │
│     └─ Returns RenderResult     │
└──────────┬──────────────────────┘
           │ video file
           ▼
┌─────────────────────────────────┐
│  PHASE 11: REVIEW + PUBLISH     │
│  └─ Video Reviewer              │
│  │  └─ FFprobe quality checks   │
│  │  └─ Returns ReviewReport     │
│  └─ Publisher                   │
│     └─ gh pr comment --body     │
│     └─ Returns PublishResult    │
└─────────────────────────────────┘
┌─────────────────────────────────┐
│  PHASE 6: ASSETS                │
│  └─ Image Generator             │
│     └─ AI generation / Stock    │
│     └─ Returns image_map        │
└──────────┬──────────────────────┘
           │ image_map (scene_id → path)
           ▼
┌─────────────────────────────────┐
│  PHASE 7: COMPOSE               │
│  └─ Composition Builder         │
│     └─ Assemble inputProps      │
│     └─ Validate against Zod     │
│     └─ Returns CompositionResult│
└──────────┬──────────────────────┘
           │ inputProps JSON
           ▼
┌─────────────────────────────────┐
│  PHASE 8: RENDER                │
│  └─ Render Executor             │
│     └─ npx remotion render      │
│     └─ Poll kill switch         │
│     └─ Returns RenderResult     │
└──────────┬──────────────────────┘
           │ video file
           ▼
┌─────────────────────────────────┐
│  PHASE 9: REVIEW + PUBLISH      │
│  └─ Video Reviewer              │
│  │  └─ FFprobe quality checks   │
│  │  └─ Returns ReviewReport     │
│  └─ Publisher                   │
│     └─ gh pr comment --body     │
│     └─ Returns PublishResult    │
└─────────────────────────────────┘
```

### 4.2 Audio Generation Pipeline

```
Script Text
     │
     ▼
┌──────────────┐
│ split_       │  regex: (?<=[.!?])\s+
│ sentences()  │
└──────┬───────┘
       │ ["Sentence one.", "Sentence two!", "Sentence three?"]
       ▼
┌──────────────┐
│ group_into_  │  ≤50 tokens per chunk
│ chunks()     │  ~4 chars/token estimate
└──────┬───────┘
       │ ["Sentence one. Sentence two!", "Sentence three?"]
       ▼
┌──────────────┐     ┌──────────────────┐
│ generate_    │────▶│ Pocket TTS Server │
│ chunk_wavs() │◀────│ (HTTP POST /tts)  │
└──────┬───────┘     └──────────────────┘
       │ [chunk1.wav, chunk2.wav]
       ▼
┌──────────────┐
│ stitch_wavs()│  pydub crossfade=50ms
└──────┬───────┘
       │ scene_audio.wav (full scene audio)
       ▼
┌──────────────┐
│ extract_word_│  Uniform estimation:
│ timestamps() │  duration_ms / word_count
└──────┬───────┘
       │ [{word, start_ms, end_ms}, ...]
       ▼
┌──────────────┐
│ generate_    │  @remotion/captions format
│ caption_     │  {text, startMs, endMs}
│ json()       │
└──────┬───────┘
       │ SceneAudioMetadata
```

### 4.3 Remotion Rendering Pipeline

```
inputProps JSON
     │
     ▼
┌──────────────────────────────────┐
│  Zod Schema Validation           │
│  (discriminated union on type)   │
└──────────┬───────────────────────┘
           │ validated inputProps
           ▼
┌──────────────────────────────────┐
│  Root.tsx                         │
│  └─ Selects composition by ID    │
└──────────┬───────────────────────┘
           │ matched composition
           ▼
┌──────────────────────────────────┐
│  Composition Component           │
│  (e.g., PRSummary)               │
│  └─ TransitionSeries             │
│     └─ Scene 0: TitleScene       │
│     │  └─ useCurrentFrame()      │
│     │  └─ interpolate() anim     │
│     ├─ Transition (fade)         │
│     ├─ Scene 1: CodeScene        │
│     │  └─ useCurrentFrame()      │
│     │  └─ CodeBlock render       │
│     ├─ Transition (slide)        │
│     ├─ Scene 2: DiffScene        │
│     │  └─ DiffView render        │
│     └─ ...                       │
│  └─ Audio tracks (per scene)     │
│  └─ CaptionOverlay (global)      │
└──────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  @remotion/renderer.renderMedia() │
│  └─ Bundles Remotion project     │
│  └─ Renders each frame           │
│  └─ Encodes to output codec      │
└──────────┬───────────────────────┘
           │ output.mp4
```

### 4.4 Webhook-Driven Pipeline

```
GitHub
  │
  │ POST /webhook (JSON payload + HMAC-SHA256 signature)
  ▼
┌─────────────────────────────────────┐
│  Receive webhook payload            │
│  ├─ Read X-Hub-Signature-256 header │
│  ├─ Read X-GitHub-Event header      │
│  ├─ Read X-GitHub-Delivery header   │
│  │                                   │
│  ├─ Verify HMAC-SHA256 signature    │
│  │  ├─ Match? → continue            │
│  │  └─ Mismatch → 401 Unauthorized  │
│  │                                   │
│  ├─ Dispatch by event type:         │
│  │  ├─ pull_request → handlePR()    │
│  │  ├─ issues → handleIssue()       │
│  │  ├─ push → handlePush()          │
│  │  └─ release → handleRelease()    │
│  │                                   │
│  └─ Return 202 Accepted             │
└──────────┬──────────────────────────┘
           │
           ▼
    ┌──────────────────┐
    │ Pipeline Execution│  (async, non-blocking)
    │ Phase 1: INGEST   │
    │ Phase 2: RESEARCH │
    │ Phase 3: SCRIPT   │
    │ Phase 4: AUDIO    │
    │ Phase 5: SCENE    │
    │ Phase 6: ASSETS   │
    │ Phase 7: COMPOSE  │
    │ Phase 8: RENDER   │
    │ Phase 9: PUBLISH  │
    └──────────────────┘
           │
           ▼
    STATE.md updated  │  Per-phase status written
    per phase         │  to STATE.md for observability
```

---

## 5. Interface Contracts

### 5.1 Config Schema

Full `config.yaml` structure:

```yaml
server:
  name: VideoForge
  host: 127.0.0.1
  port: 8080
  log_level: INFO

pocket_tts:
  server_url: http://127.0.0.1:8120
  default_voice: en_US-amy-medium
  language: en
  max_retries: 3
  timeout_seconds: 60

pipeline:
  max_video_duration_seconds: 180
  default_fps: 30
  default_resolution:
    width: 1920
    height: 1080
  default_codec: h264
  max_caption_tokens_per_chunk: 50

assets:
  ai_generation:
    enabled: false
    provider: stable_diffusion
  stock_photos:
    enabled: false
    provider: pexels

github:
  webhook_secret_env: VIDEOFORGE_WEBHOOK_SECRET
  auto_post_pr_comments: true
```

### 5.2 MCP Tool Signatures

Each tool is a Python function with typed parameters and a typed return dict:

```python
# health_check
@mcp.tool()
def health_check() -> dict
# Returns: {"status": "ok", "timestamp": "2026-07-08T12:00:00Z"}

# get_server_info
@mcp.tool()
def get_server_info() -> dict
# Returns: config snapshot (dict of AppConfig)

# generate_speech
@mcp.tool()
def generate_speech(
    text: str,
    output_path: str,
    voice: str | None = None,
) -> dict
# Returns: {"audio_path": "/tmp/videoforge/audio/scene_1.wav"}
# Raises: TTSGenerationError, TTSServerError

# list_voices
@mcp.tool()
def list_voices() -> dict
# Returns: {"voices": [{"id": "...", "name": "...", ...}], "count": 26}

# list_saved_voices
@mcp.tool()
def list_saved_voices() -> dict
# Returns: {"voices": [{"id": "...", "name": "...", ...}], "count": 26}

# process_audio_script
@mcp.tool()
def process_audio_script(
    script_text: str,
    scene_id: str,
    output_dir: str,
    voice: str | None = None,
) -> dict
# Returns: SceneAudioMetadata (see 5.5)
# Raises: AudioPipelineError

# fetch_github_pr
@mcp.tool()
def fetch_github_pr(url: str) -> dict
# Returns: GitHubPR (see 5.7)
# Raises: GitHubBaseError

# fetch_github_issue
@mcp.tool()
def fetch_github_issue(url: str) -> dict
# Returns: GitHubIssue (see 5.7)
# Raises: GitHubBaseError

# plan_scenes
@mcp.tool()
def plan_scenes(
    script: str,
    audio_metadata: dict | None = None,
    fps: int = 30,
) -> dict
# Returns: ScenePlan (see 5.4)
# Raises: ScenePlanningError

# generate_images
@mcp.tool()
def generate_images(scene: dict) -> dict
# Returns: {"images": {"scene_0": "/path/to/image.png", ...}}
# Raises: ImageGenerationError

# build_composition
@mcp.tool()
def build_composition(
    scene_plan: dict,
    audio_map: dict,
    image_map: dict,
    style: dict | None = None,
) -> dict
# Returns: CompositionResult (input_props)
# Raises: CompositionError

# render_video
@mcp.tool()
def render_video(
    composition_id: str,
    input_props: dict,
    output_path: str | None = None,
) -> dict
# Returns: {"output_path": "/path/to/video.mp4", "duration_frames": 300, ...}
# Raises: RenderExecutionError

# review_video
@mcp.tool()
def review_video(video_path: str) -> dict
# Returns: ReviewReport (see 3.13)
# Raises: ReviewError

# doctor
@mcp.tool()
def doctor() -> dict
# Returns: {"status": "ok", "checks": [{"name": "...", "passed": true, ...}]}
```

### 5.3 Remotion InputProps Schema

```typescript
import { z } from "zod";

// ── Scene Types (Discriminated Union) ──
const TitleSceneSchema = z.object({
  type: z.literal("title"),
  title: z.string().min(1).max(200),
  subtitle: z.string().min(1).max(500).optional(),
  duration: z.number().int().positive(),
});

const CodeSceneSchema = z.object({
  type: z.literal("code"),
  code: z.string().min(1),
  lang: z.string().min(1),
  highlightLines: z.array(z.number().int().positive()).optional(),
  caption: z.string().optional(),
  duration: z.number().int().positive(),
});

const DiffSceneSchema = z.object({
  type: z.literal("diff"),
  oldCode: z.string(),
  newCode: z.string(),
  lang: z.string().min(1),
  duration: z.number().int().positive(),
});

const BulletSceneSchema = z.object({
  type: z.literal("bullet"),
  points: z.array(z.string().min(1)).min(2).max(5),
  duration: z.number().int().positive(),
});

const ImageSceneSchema = z.object({
  type: z.literal("image"),
  src: z.string().min(1),
  caption: z.string().optional(),
  duration: z.number().int().positive(),
});

const ComparisonSceneSchema = z.object({
  type: z.literal("comparison"),
  labelBefore: z.string().min(1),
  labelAfter: z.string().min(1),
  duration: z.number().int().positive(),
});

const DiagramSceneSchema = z.object({
  type: z.literal("diagram"),
  config: z.object({
    grid: z.object({
      cols: z.number().int().positive(),
      rows: z.number().int().positive(),
      cellWidth: z.number().int().positive(),
      cellHeight: z.number().int().positive(),
    }),
    nodes: z.array(z.object({
      id: z.string(),
      label: z.string(),
      x: z.number(),
      y: z.number(),
      w: z.number().optional(),
      h: z.number().optional(),
      color: z.string().optional(),
    })),
    connections: z.array(z.object({
      from: z.string(),
      to: z.string(),
      label: z.string().optional(),
      color: z.string().optional(),
    })),
    timeline: z.object({
      actions: z.array(z.object({
        frame: z.number(),
        type: z.enum(["fillBox", "drawLine", "dim", "reveal", "hold", "parallel"]),
        target: z.string(),
        duration: z.number().optional(),
      })),
    }),
  }),
  duration: z.number().int().positive(),
});

const OutroSceneSchema = z.object({
  type: z.literal("outro"),
  title: z.string().min(1).max(200),
  cta: z.string().optional(),
  duration: z.number().int().positive(),
});

// ── Scene Discriminated Union ──
const SceneSchema = z.discriminatedUnion("type", [
  TitleSceneSchema,
  CodeSceneSchema,
  DiffSceneSchema,
  BulletSceneSchema,
  ImageSceneSchema,
  ComparisonSceneSchema,
  DiagramSceneSchema,
  OutroSceneSchema,
]);

// ── Audio Track ──
const AudioTrackSchema = z.object({
  src: z.string().min(1),      // path to WAV file
  startFrame: z.number().int().nonnegative(),
  durationFrames: z.number().int().positive(),
});

// ── Caption Entry ──
const CaptionEntrySchema = z.object({
  text: z.string().min(1),
  startMs: z.number().nonnegative(),
  endMs: z.number().positive(),
});

// ── Style ──
const StyleSchema = z.object({
  primaryColor: z.string().regex(/^#[0-9a-fA-F]{6}$/),
  font: z.string().min(1),
  codeTheme: z.string().min(1),
});

// ── Root InputProps ──
export const InputPropsSchema = z.object({
  title: z.string().min(1).max(500),
  scenes: z.array(SceneSchema).min(1).max(50),
  audioTracks: z.array(AudioTrackSchema).min(1),
  captions: z.array(CaptionEntrySchema),
  voice: z.string().min(1),
  style: StyleSchema,
});

export type InputProps = z.infer<typeof InputPropsSchema>;
export type Scene = z.infer<typeof SceneSchema>;
export type SceneType = Scene["type"];
```

### 5.4 Scene Plan Schema

```python
class ScenePlan(TypedDict):
    total_duration_frames: int
    fps: int
    scenes: list[PlannedScene]
    transitions: list[PlannedTransition]

class PlannedScene(TypedDict):
    index: int
    type: str  # "title" | "code" | "diff" | "bullet" | "image" | "comparison" | "diagram" | "outro"
    start_frame: int
    duration_frames: int
    props: dict  # scene-specific props per InputPropsSchema
    audio_track: AudioTrackRef | None

class AudioTrackRef(TypedDict):
    src: str  # path to WAV file
    start_frame: int
    duration_frames: int

class PlannedTransition(TypedDict):
    from_scene_index: int
    to_scene_index: int
    type: str  # "fade" | "slide" | "zoom" | "wipe" | "dissolve" | "flip" | "scale" | "rotate" | "blur" | "morph" | "glitch" | "warp"
    duration_frames: int
```

### 5.5 Audio Track Schema

```python
class SceneAudioMetadata(TypedDict):
    scene_id: str
    audio_path: str
    duration_seconds: float
    duration_frames: int       # duration_seconds * fps
    sample_rate: int           # typically 24000
    word_timestamps: list[WordTimestamp]
    captions: list[CaptionEntry]

class WordTimestamp(TypedDict):
    word: str
    start_ms: float
    end_ms: float

class CaptionEntry(TypedDict):
    text: str
    startMs: float
    endMs: float
```

### 5.6 Caption Schema

```typescript
// @remotion/captions input format
interface CaptionEntry {
  text: string;
  startMs: number;
  endMs: number;
}

// Output from createTikTokStyleCaptions()
interface TikTokCaptionsResult {
  segments: CaptionSegment[];
}

interface CaptionSegment {
  text: string;
  startMs: number;
  endMs: number;
  words: {
    text: string;
    startMs: number;
    endMs: number;
  }[];
}
```

### 5.7 GitHub Data Schemas

```python
class GitHubPR(TypedDict):
    title: str
    body: str
    diff: str
    files: list[PRFile]
    author: str
    labels: list[str]
    comments: list[Comment]
    created_at: str
    additions: int
    deletions: int

class PRFile(TypedDict):
    path: str
    status: str  # "added" | "modified" | "removed" | "renamed"
    additions: int
    deletions: int

class Comment(TypedDict):
    author: str
    body: str
    created_at: str

class GitHubIssue(TypedDict):
    title: str
    body: str
    labels: list[str]
    comments: list[Comment]
    author: str
    created_at: str
    state: str  # "open" | "closed"
```

### 5.8 State File Format

`STATE.md` tracks pipeline execution state for observability:

```markdown
# VideoForge Pipeline State

## Pipeline: PR #42 — Add authentication middleware

**Status:** IN_PROGRESS  
**Started:** 2026-07-08T12:00:00Z  
**Updated:** 2026-07-08T12:02:15Z  

| Phase | Status | Started | Duration | Error |
|-------|--------|---------|----------|-------|
| 1. INGEST | ✅ COMPLETE | 12:00:00 | 3.2s | — |
| 2. RESEARCH | ✅ COMPLETE | 12:00:04 | 5.1s | — |
| 3. SCRIPT | ✅ COMPLETE | 12:00:09 | 8.7s | — |
| 4. AUDIO | 🔄 IN_PROGRESS | 12:00:18 | — | — |
| 5. SCENE PLAN | ⏳ PENDING | — | — | — |
| 6. ASSETS | ⏳ PENDING | — | — | — |
| 7. COMPOSE | ⏳ PENDING | — | — | — |
| 8. RENDER | ⏳ PENDING | — | — | — |
| 9. REVIEW/PUBLISH | ⏳ PENDING | — | — | — |

## Kill Switch
VIDEOFORCE_KILL_SWITCH: unset
```

### 5.9 Diagram Config Schema

```python
class DiagramConfig(TypedDict):
    grid: DiagramGrid
    nodes: list[DiagramNode]
    connections: list[DiagramConnection]
    timeline: DiagramTimeline

class DiagramGrid(TypedDict):
    cols: int
    rows: int
    cellWidth: int
    cellHeight: int

class DiagramNode(TypedDict):
    id: str
    label: str
    x: int
    y: int
    w: int | None       # default: cellWidth
    h: int | None       # default: cellHeight
    color: str | None   # hex color

class DiagramConnection(TypedDict):
    from: str            # node id
    to: str              # node id
    label: str | None
    color: str | None

class DiagramTimeline(TypedDict):
    actions: list[TimelineAction]

class TimelineAction(TypedDict):
    frame: int           # frame number (0-indexed)
    type: Literal["fillBox", "drawLine", "dim", "reveal", "hold", "parallel"]
    target: str          # node id or connection id
    duration: int | None # frames over which action occurs
```

---

## 6. Error Handling Strategy

### 6.1 Exception Hierarchy

All exceptions inherit from `VideoForgeError`:

```
VideoForgeError
  ├── ConfigurationError
  │   ├── ConfigFileNotFound
  │   ├── ConfigValidationError
  │   └── ConfigParseError
  ├── TTSBaseError
  │   ├── TTSConnectionError
  │   ├── TTSGenerationError
  │   ├── TTSServerError
  │   └── TTSAudioError
  ├── AudioPipelineError
  │   ├── SentenceSplitError
  │   ├── ChunkGenerationError
  │   ├── AudioStitchError
  │   └── TimestampExtractionError
  ├── GitHubBaseError
  │   ├── GitHubCLINotFoundError
  │   ├── GitHubAPIError
  │   ├── GitHubDataError
  │   └── GitHubValidationError
  ├── ClassificationError
  ├── ScriptGenerationError
  │   └── ScriptValidationError
  ├── ScenePlanningError
  ├── CompositionError
  │   └── CompositionValidationError
  ├── ImageGenerationError
  ├── RenderExecutionError
  │   └── RenderCancelledError
  ├── PublishError
  ├── ReviewError
  └── WebhookError
```

### 6.2 Retry Policies

| Operation | Retry Strategy | Max Attempts | Backoff | When to Give Up |
|-----------|---------------|-------------|---------|-----------------|
| TTS speech generation | Exponential + jitter | `max_retries` (default: 3) | 2s, 4s, 8s ±50% jitter | All attempts exhausted |
| HTTP requests (httpx) | Exponential | 3 | 1s, 2s, 4s | Connection timeout, 5xx status |
| Stock photo API | Fixed delay | 2 | 1s | Rate limit, 4xx status |
| AI image generation | None (single attempt) | 1 | — | Any failure → fall back to stock |
| gh CLI subprocess | None | 1 | — | Non-zero exit code |
| FFmpeg subprocess | None | 1 | — | Non-zero exit code |

### 6.3 Fallback Behaviors

| Component | Primary | Fallback 1 | Fallback 2 |
|-----------|---------|-----------|------------|
| TTS response parsing | audio/wav content-type | JSON with base64 audio | Raise `TTSAudioError` |
| Voice listing | Server `/voices` API | Hardcoded 26-voice list | Empty list (raise warning) |
| Word timestamps | Whisper forced-alignment | Uniform estimation | All words at center frame |
| Image generation | AI image API | Stock photo API | Skip image (code-only scene) |
| Scene transitions | ML-selected transitions | Sequential fade | Hardcoded default per scene type |
| Video codec | h264 (hardware-accelerated) | h264 (software) | Raise `RenderExecutionError` |
| GitHub data | gh CLI | Direct GitHub REST API | Raise `GitHubAPIError` |

### 6.4 Pipeline Error Propagation

```
Phase execution:
  try:
      result = await phase_function(input_data)
      update_state(PHASE, COMPLETE, result)
  except VideoForgeError as e:
      update_state(PHASE, FAILED, error=e.to_dict())
      log_exception(e)
      # Pipeline continues to next phase
  except Exception as e:
      update_state(PHASE, FAILED, error={"type": "unexpected", "message": str(e)})
      log_exception(e)
      # Pipeline continues to next phase
  finally:
      check_kill_switch()

Kill switch behavior:
  if os.environ.get("VIDEOFORCE_KILL_SWITCH"):
      update_state(PIPELINE, CANCELLED)
      return  # Stop pipeline execution
```

**Design Decisions:**
- Pipeline never fails entirely due to a single phase error
- Each phase result may be `None` if phase failed; downstream phases must handle `None` inputs
- Errors are captured in `STATE.md` for debugging
- Kill switch is the only way to abort a running pipeline
- No phase-level rollback or compensation transactions

---

## 7. Testing Strategy

### 7.1 Test Pyramid

```
         ╱╲
        ╱  ╲
       ╱ E2E╲          3-5 end-to-end tests
      ╱──────╲          (full pipeline with mocks)
     ╱        ╲
    ╱Integration╲      20-30 integration tests
   ╱────────────╲      (module interactions with real deps)
  ╱              ╲
 ╱   Unit Tests   ╲    100+ unit tests
╱──────────────────╲   (individual functions, mocked deps)
```

### 7.2 Unit Tests: Python

**Framework:** pytest 8+ with pytest-asyncio  
**Coverage target:** 90%+ lines, 85%+ branches

| Module | Test File | Key Test Cases |
|--------|-----------|----------------|
| `config.py` | `tests/test_config.py` | Load valid YAML, invalid YAML, missing file, env var overrides |
| `tts_adapter.py` | `tests/test_tts_adapter.py` | Successful generation, retry logic, audio/wav vs JSON response, timeout, server error, voice list with fallback |
| `audio_pipeline.py` | `tests/test_audio_pipeline.py` | Sentence splitting (various punctuation), chunk grouping (empty, exact size, overflow), stitch with crossfade, uniform timestamp estimation, full pipeline end-to-end |
| `agents/content_fetcher.py` | `tests/test_content_fetcher.py` | gh CLI success, non-zero exit, invalid URL, missing gh binary |
| `agents/content_classifier.py` | `tests/test_content_classifier.py` | Valid classification, low confidence, LLM failure |
| `agents/script_writer.py` | `tests/test_script_writer.py` | Script generation, too-short script, too-long script truncation |
| `agents/scene_planner.py` | `tests/test_scene_planner.py` | Frame allocation, transition selection, audio-scene mismatch |
| `agents/composition_builder.py` | `tests/test_composition_builder.py` | Input assembly, missing assets, Zod validation errors |
| `agents/image_generator.py` | `tests/test_image_generator.py` | AI generation, stock fallback, code-only fallback, API failures |
| `tools/render_executor.py` | `tests/test_render_executor.py` | Successful render, cancelled render, missing composition, OOM |
| `tools/video_reviewer.py` | `tests/test_video_reviewer.py` | All checks pass, blank frame detection, missing audio stream |
| `webhook/handler.py` | `tests/test_webhook.py` | Valid signature, invalid signature, missing header, unsupported event |
| `exceptions.py` | `tests/test_exceptions.py` | All exception types, to_dict() serialization |

**Example Test Patterns:**

```python
# tests/test_tts_adapter.py
import pytest
from videoforge.tts_adapter import TTSClient
from videoforge.exceptions import TTSGenerationError, TTSServerError

@pytest.mark.asyncio
async def test_generate_speech_success(tts_client, respx_mock):
    route = respx_mock.post("http://127.0.0.1:8120/tts").respond(
        content=b"RIFF...WAV data...",
        headers={"content-type": "audio/wav"},
    )
    result = await tts_client.generate_speech("Hello world", voice="en_US-amy-medium")
    assert result == b"RIFF...WAV data..."
    assert route.called

@pytest.mark.asyncio
async def test_generate_speech_retry_on_timeout(tts_client, respx_mock):
    route = respx_mock.post("http://127.0.0.1:8120/tts").mock(
        side_effect=[httpx.TimeoutException, httpx.TimeoutException, httpx.Response(200, content=b"...")],
    )
    result = await tts_client.generate_speech("Hello")
    assert result == b"..."
    assert len(route.calls) == 3

@pytest.mark.asyncio
async def test_generate_speech_exhausted_retries(tts_client, respx_mock):
    route = respx_mock.post("http://127.0.0.1:8120/tts").mock(
        side_effect=httpx.TimeoutException,
    )
    with pytest.raises(TTSGenerationError):
        await tts_client.generate_speech("Hello")
    assert len(route.calls) == 3
```

### 7.3 Unit Tests: TypeScript/React

**Framework:** vitest 2+ with jsdom environment  
**Coverage target:** 80%+ lines, functions, branches, statements

| Module | Test File | Key Test Cases |
|--------|-----------|----------------|
| `Root.tsx` | `__tests__/Root.test.tsx` | Renders all compositions, Zod validation |
| Scene components | `__tests__/scenes/*.test.tsx` | Each scene renders with valid props, missing props, frame animation |
| Transition components | `__tests__/transitions/*.test.tsx` | Entering/exiting directions, 0→1 progress, children rendered |
| Shared components | `__tests__/components/*.test.tsx` | CaptionOverlay word highlighting, CodeBlock syntax highlighting, DiffView diff rendering |
| Types | `__tests__/types.test.ts` | Zod schema validation, discriminated union parsing, invalid input rejection |

**Example Test Patterns:**

```typescript
// __tests__/scenes/TitleScene.test.tsx
import { render } from "@testing-library/react";
import { expect, test } from "vitest";
import { TitleScene } from "../../src/scenes/TitleScene";
import { RemotionTestProvider } from "../RemotionTestProvider";

test("renders title and subtitle", () => {
  const { getByText } = render(
    <RemotionTestProvider frame={0}>
      <TitleScene
        type="title"
        title="My Test Title"
        subtitle="Test Subtitle"
        durationInFrames={150}
      />
    </RemotionTestProvider>
  );
  expect(getByText("My Test Title")).toBeDefined();
  expect(getByText("Test Subtitle")).toBeDefined();
});

test("applies fade-in animation at frame 0", () => {
  const { container } = render(
    <RemotionTestProvider frame={0}>
      <TitleScene
        type="title"
        title="Test"
        durationInFrames={150}
      />
    </RemotionTestProvider>
  );
  const fill = container.firstChild as HTMLElement;
  expect(fill.style.opacity).toBe("0");
});

test("full opacity at frame 15", () => {
  const { container } = render(
    <RemotionTestProvider frame={15}>
      <TitleScene
        type="title"
        title="Test"
        durationInFrames={150}
      />
    </RemotionTestProvider>
  );
  const fill = container.firstChild as HTMLElement;
  expect(fill.style.opacity).toBe("1");
});

test("validates schema: rejects missing title", () => {
  const result = TitleSceneSchema.safeParse({
    type: "title",
    duration: 150,
  });
  expect(result.success).toBe(false);
});
```

### 7.4 Integration Tests

**Scope:** Verify module interactions with real dependencies (TTS server, gh CLI, FFmpeg).

| Test | What It Verifies | Dependencies Required |
|------|-----------------|----------------------|
| TTS → Audio Pipeline | Full TTS integration, crossfade stitching | Pocket TTS server running |
| gh CLI → Content Fetcher | Real GitHub PR fetch | gh CLI authenticated |
| FFmpeg → Stitcher | WAV crossfade with real FFmpeg | FFmpeg on PATH |
| Remotion → Renderer | Real video rendering (small) | Node.js, Remotion deps |
| Config → Env Override | Env var override system | None (pure Python) |

### 7.5 End-to-End Tests

**Scope:** Full pipeline execution with mocked external services.

```python
# tests/e2e/test_full_pipeline.py
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_pr_explainer_pipeline(e2e_config, mock_gh_cli, mock_tts_server, mock_remotion):
    """End-to-end test: GitHub PR → video output."""
    pipeline = Pipeline(e2e_config)

    # Execute all phases
    result = await pipeline.run(
        trigger_type="github_pr",
        trigger_url="https://github.com/owner/repo/pull/42",
    )

    # Verify all phases completed
    assert result.phases["ingest"].status == "complete"
    assert result.phases["render"].status == "complete"
    assert result.phases["publish"].status == "complete"

    # Verify output exists
    assert Path(result.output_path).exists()
    assert Path(result.output_path).stat().st_size > 1000  # at least 1KB

    # Verify comment was posted
    assert mock_gh_cli.last_command.startswith("gh pr comment 42")
```

### 7.6 Mocking Strategy

| Service | Mocking Tool | What to Mock |
|---------|-------------|-------------|
| Pocket TTS | respx (httpx mock) | `/tts` endpoint, `/voices` endpoint |
| gh CLI | pytest `monkeypatch` | `create_subprocess_exec` return value |
| FFmpeg/FFprobe | pytest `monkeypatch` | Subprocess calls |
| Remotion render | Temporary disabled (integration only) | Subprocess call, file creation |
| AI Image API | respx | HTTP POST to image provider |
| Stock Photo API | respx | HTTP GET to Pexels/Pixabay |
| LLM calls | `unittest.mock.AsyncMock` | LLM tool invocation |
| File system | `tmp_path` fixture | All file I/O |

**Shared Mock Fixtures (conftest.py):**
```python
# tests/conftest.py
@pytest.fixture
def tts_client(config):
    return TTSClient(config.pocket_tts)

@pytest.fixture
def mock_tts_server(respx_mock):
    """Mock Pocket TTS server returning valid WAV."""
    respx_mock.post("http://127.0.0.1:8120/tts").respond(
        content=b"RIFF\x24\x00\x00\x00WAVE...",
        headers={"content-type": "audio/wav"},
    )
    return respx_mock

@pytest.fixture
def tmp_audio_dir(tmp_path):
    """Temporary directory for audio files."""
    d = tmp_path / "audio"
    d.mkdir()
    return d

@pytest.fixture
def sample_wav(tmp_audio_dir):
    """Generate a minimal valid WAV file for testing."""
    import struct, wave
    path = tmp_audio_dir / "sample.wav"
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(struct.pack(f"<{24000}h", *[0]*24000))  # 1 sec silence
    return path
```

### 7.7 Test Fixtures

**Python Test Fixtures (tests/conftest.py):**
- `config`: Loaded `AppConfig` from test YAML
- `tts_client`: `TTSClient` with test config
- `mock_tts_server`: respx-mocked Pocket TTS
- `mock_gh_cli`: monkeypatched subprocess
- `tmp_audio_dir`: `tmp_path / "audio"`
- `sample_wav`: 1-second silent WAV
- `sample_script`: Multi-sentence script text
- `sample_pr_data`: `GitHubPR` fixture
- `sample_input_props`: Valid InputProps fixture

**TypeScript Test Fixtures (__tests__/setup.ts):**
- `RemotionTestProvider`: Wraps children with Remotion context
- `mock_frame`: `useCurrentFrame()` mock
- `sample_captions`: Caption array fixture
- `sample_scene_plan`: ScenePlan object fixture

```typescript
// __tests__/RemotionTestProvider.tsx
import React from "react";

interface Props {
  frame?: number;
  fps?: number;
  children: React.ReactNode;
}

export const RemotionTestProvider: React.FC<Props> = ({
  frame = 0,
  fps = 30,
  children,
}) => {
  return (
    <div data-testid="remotion-provider" data-frame={frame} data-fps={fps}>
      {children}
    </div>
  );
};
```

---

## 8. Security Considerations

### 8.1 Input Validation

| Input | Validation | Location |
|-------|-----------|----------|
| Script text | Non-empty, max 10,000 chars, printable ASCII/UTF-8 | `audio_pipeline.py` |
| GitHub URLs | Must match `https://github.com/{owner}/{repo}/(pull|issue)/{number}` | `content_fetcher.py` |
| Output paths | Must be within allowed output directory (no path traversal) | All tools |
| Voice IDs | Must match known voice list or contain only `[a-zA-Z0-9_-]` | `tts_adapter.py` |
| Scene types | Must be one of the 8 known types (discriminated union) | `composition_builder.py` |
| inputProps | Zod schema validation (runtime) | Remotion project |
| Webhook payload | Max 25MB, valid JSON | `webhook/handler.py` |

**Path Traversal Prevention:**
```python
import os
from pathlib import Path

def validate_output_path(path: str, allowed_base: Path) -> Path:
    resolved = Path(path).resolve()
    allowed = allowed_base.resolve()
    if not str(resolved).startswith(str(allowed)):
        raise ValueError(f"Path {path} is outside allowed directory {allowed_base}")
    return resolved
```

### 8.2 HMAC Signature Verification

GitHub webhooks are signed with HMAC-SHA256 using a shared secret. Verification is mandatory for all incoming webhooks.

```python
import hmac
import hashlib

SECRET_ENV_VAR = "VIDEOFORGE_WEBHOOK_SECRET"

def verify_webhook_signature(
    payload: bytes,
    signature_header: str | None,
    secret: str | None = None,
) -> bool:
    """
    Verify HMAC-SHA256 signature from GitHub webhook.

    Args:
        payload: Raw request body (bytes)
        signature_header: Value of X-Hub-Signature-256 header
        secret: HMAC secret (from env var if not provided)

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature_header:
        return False

    secret = secret or os.environ.get(SECRET_ENV_VAR, "")
    if not secret:
        return False

    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature_header)
```

**Security Properties:**
- Timing-safe comparison via `hmac.compare_digest` (prevents timing attacks)
- Secret loaded from environment variable only (never in config file or code)
- Missing or empty secret → all signatures rejected (fail closed)
- Secret must be ≥ 32 characters (validated at startup)

### 8.3 Shell Injection Prevention

All subprocess calls use explicit argument lists (NOT shell strings):

```python
# DANGEROUS — NEVER USE:
subprocess.run(f"gh pr view {url}", shell=True)  # Shell injection!

# SAFE — ALWAYS USE:
await asyncio.create_subprocess_exec(
    "gh", "pr", "view", url, "--json", "title,body",
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
)
```

**Rules:**
- Never use `shell=True` in subprocess calls
- Never use string formatting/concatenation for command arguments
- Use `asyncio.create_subprocess_exec()` for async operations
- Use `subprocess.run()` with list arguments for sync operations
- All GitHub URLs are validated with regex before passing to gh CLI

### 8.4 Secrets Management

| Secret | Storage | Access Method |
|--------|---------|---------------|
| GitHub webhook secret | Environment variable `VIDEOFORGE_WEBHOOK_SECRET` | `os.environ.get()` |
| GitHub token | Pre-configured via `gh auth` | Not handled by VideoForge |
| AI Image API key | Environment variable | `os.environ.get()` |
| Stock Photo API key | Environment variable | `os.environ.get()` |
| Pocket TTS URL | Config file (no auth needed for local) | Config value |

**Secrets Policy:**
- No secrets stored in code, config files, or state files
- All API keys loaded from environment variables via `os.environ.get()`
- Secrets never appear in logs (redacted by logging formatter)
- Webhook secret validated at startup (not empty, ≥ 32 chars)
- `gh` CLI uses its own OAuth token (managed by GitHub CLI)

### 8.5 Subprocess Security

| Subprocess | Args | Security Measure |
|------------|------|-----------------|
| gh CLI | `["gh", "pr", "view", url, "--json", "..."]` | URL validated against regex |
| npx remotion | `["npx", "remotion", "render", comp_id, out, "--props", props_file]` | comp_id validated, props_file from trusted source |
| FFmpeg | `ffmpeg-python` API | No raw subprocess; paths validated |
| FFprobe | `["ffprobe", "-v", "quiet", "-print_format", "json", ...]` | File path validated |

**Additional Measures:**
- All subprocess calls have timeouts to prevent hung processes
- `npx` is called with `--yes` flag suppressed to prevent auto-install of untrusted packages
- Temp files for props are created with `tempfile.NamedTemporaryFile(delete=False)` and cleaned up
- Subprocess stdout/stderr are captured, never echoed to terminal in production

---

## 9. Performance Budgets

### 9.1 Render Time Budgets

| Content Type | Target Duration | Max Render Time | Ratio |
|-------------|----------------|-----------------|-------|
| PR Summary (3 scenes) | 60s video | 10 min | 10x realtime |
| Issue Explainer (5 scenes) | 90s video | 20 min | 13x realtime |
| Code Walkthrough (8 scenes) | 120s video | 30 min | 15x realtime |
| Changelog (10 scenes) | 180s video | 45 min | 15x realtime |
| Audio generation | Per minute of audio | 30s | 0.5x realtime |

**Budget Notes:**
- Render times assume H.264 software encoding, 1920×1080, 30fps
- Hardware-accelerated encoding (h264_nvenc / h264_videotoolbox) targets 3x realtime
- Audio generation is the fastest phase (sub-second per chunk)
- Image generation is the most variable phase (2-30s per image)

### 9.2 Memory Limits

| Component | Limit | Notes |
|-----------|-------|-------|
| MCP Server (Python) | 512 MB RSS | Shared across requests |
| TTSClient session | 200 MB | Audio buffer cache |
| Audio Pipeline | 500 MB | WAV files in memory during stitch |
| Image Generator | 300 MB | Image loading + processing |
| Remotion (Node.js) | 2 GB RSS | Per render process |
| FFmpeg | 500 MB | Per encode process |

**Mitigation:**
- Audio chunks are written to disk, not held in memory after stitch
- Large WAV files are streamed through pydub (chunked processing)
- Remotion renders are isolated in subprocesses (OOM kills only the render, not the MCP server)
- Image files are downloaded to temp directory, not retained in memory

### 9.3 Token Budgets

| LLM Operation | Input Tokens (max) | Output Tokens (max) | Model |
|---------------|-------------------|--------------------|-------|
| Content Classification | 8,000 | 500 | gpt-4o-mini |
| Script Writing | 12,000 | 2,000 | gpt-4o |
| Image Prompt Generation | 4,000 | 200 | gpt-4o-mini |
| Video Review | 1,000 | 500 | gpt-4o-mini |

**Token Mitigation:**
- GitHub PR diff can be large (>50,000 tokens). Truncated to 8,000 tokens for classification
- Full diff preserved in scene plan for code scenes
- Script text limited by `max_video_duration_seconds` (180s × 2.8 words/s ≈ 504 words)

### 9.4 Audio Pipeline Budgets

| Operation | Time Budget | Notes |
|-----------|------------|-------|
| Sentence splitting | < 10ms | Regex on ≤ 10K text |
| Chunk grouping | < 5ms | O(n) linear pass |
| TTS per chunk | < 5s | 50 tokens, server local |
| Crossfade stitch | < 1s per 10 chunks | pydub, FFmpeg backend |
| Timestamp estimation | < 100ms | Pure Python math |
| Full pipeline (60s audio) | < 30s | 10-15 chunks |

**Audio Quality Specifications:**
| Parameter | Value |
|-----------|-------|
| Sample rate | 24 kHz |
| Bit depth | 16-bit signed PCM |
| Channels | Mono |
| Format | WAV (PCM) |
| Crossfade overlap | 50ms |
| Silence padding (start/end) | 200ms / 100ms |

---

## 10. Agent Skill Specifications

Each `.skill.md` file in `skills/` teaches a loop-engineering agent how to execute one phase of the pipeline. Skills follow a consistent template:

### 10.1 `video-ingest.skill.md`

**Purpose:** Teach the agent how to fetch and validate GitHub content.

**Teaches:**
- How to call `fetch_github_pr(url)` or `fetch_github_issue(url)` MCP tools
- How to validate the URL format before calling
- How to handle `gh` CLI authentication errors
- What fields to extract from the returned data

**Agent Instructions Summary:**
1. Accept a GitHub URL (PR or issue)
2. Validate URL format: `https://github.com/{owner}/{repo}/pull/{number}` or `/issues/{number}`
3. Call `fetch_github_pr(url)` or `fetch_github_issue(url)`
4. Verify `gh` CLI returns non-empty JSON
5. Extract: title, body, diff, files, author, labels
6. If diff is empty, note that the PR has no code changes
7. Return structured GitHub content to next phase

**Output:** `GitHubPR` or `GitHubIssue` dict

### 10.2 `video-research.skill.md`

**Purpose:** Teach the agent how to analyze GitHub content and classify the video type.

**Teaches:**
- How to determine video type from PR/issue structure
- How to evaluate content complexity
- How to identify key topics and code areas
- How to suggest scene types for the video

**Agent Instructions Summary:**
1. Receive structured GitHub content from ingest phase
2. Analyze: title, body, diff files, labels, comments
3. Classify into one of: `pr_summary`, `issue_explainer`, `changelog`, `code_walkthrough`
4. Rate complexity: `low` (single file change), `medium` (multi-file, straightforward), `high` (cross-cutting change)
5. Extract key topics from labels, title, and body
6. Suggest 3-8 scene types appropriate for the content
7. Return classification with confidence score

**Output:** `ContentClassification` dict

### 10.3 `video-script.skill.md`

**Purpose:** Teach the agent how to generate a narrative script from classified content.

**Teaches:**
- How to write developer-friendly narrative script
- How to structure script with scene markers
- How to reference code and diffs in narrative
- How to maintain consistent tone and pacing
- How to estimate spoken duration

**Agent Instructions Summary:**
1. Receive classified content from research phase
2. Write a narrative script with clear scene boundaries
3. Each scene should have a descriptive title
4. Script should explain code changes, not just repeat them
5. Target: ~2.8 words/second speaking rate
6. Include call-to-action in outro
7. Return script with scene annotations and duration estimates

**Script Structure Template:**
```
[SCENE: title]
Video title: {title}
Subtitle: {subtitle}
Spoken text: ...

[SCENE: code]
Code highlight: {file_path}
Spoken text: Explain the change...

[SCENE: difference]
Spoken text: Show the before/after...

[SCENE: bullet]
Spoken text: Key points...

[SCENE: outro]
Spoken text: Summary and CTA...
```

**Output:** `ScriptResult` dict with script_text and scenes[]

### 10.4 `video-scene-plan.skill.md`

**Purpose:** Teach the agent how to create a frame-accurate scene plan.

**Teaches:**
- How to match script scenes to audio timing
- How to calculate frame counts from duration
- How to select appropriate transitions
- How to handle scene overlaps

**Agent Instructions Summary:**
1. Receive script with scene annotations + audio metadata
2. For each scene, calculate `duration_frames = audio_duration_seconds * fps`
3. Assign transitions between scenes based on type transitions
4. Ensure total duration matches audio length (within tolerance)
5. Allocate audio tracks per scene
6. Handle edge cases: first scene (no incoming transition), last scene (no outgoing)
7. Return complete ScenePlan

**Transition Selection Heuristic:**
| From → To | Transition |
|-----------|-----------|
| title → any | fade |
| code → code | slide |
| code → diff | wipe |
| bullet → code | dissolve |
| image → any | fade |
| comparison → any | slide |
| diagram → any | dissolve |
| any → outro | fade |

**Output:** `ScenePlan` dict

### 10.5 `video-assets.skill.md`

**Purpose:** Teach the agent how to generate or source visual assets.

**Teaches:**
- How to determine which scenes need images
- How to call AI image generation or stock photo APIs
- How to write effective image prompts
- When to skip image generation (code-only scenes)

**Agent Instructions Summary:**
1. Receive scene plan from scene-plan phase
2. For each scene, determine if an image is needed:
   - `title`: Always (background image)
   - `code`/`diff`: Never (code is the visual)
   - `bullet`: If AI/stock enabled (background)
   - `image`: Use scene config
   - `comparison`: Never (comparison UI is the visual)
   - `diagram`: Use @shetty4l/diagrams
   - `outro`: Brand logo/icon
3. For AI generation: write descriptive prompt from scene content
4. For stock photos: query based on keywords
5. Return map of scene_index → image path

**Prompt Writing Guidelines:**
- Keep prompts under 200 characters
- Include technical context (e.g., "abstract visualization of code branching")
- Specify style: "minimal, tech-themed, dark background with neon accents"

**Output:** `dict[str, str]` (scene_index → image_path)

### 10.6 `video-compose.skill.md`

**Purpose:** Teach the agent how to assemble the final composition input props.

**Teaches:**
- How to combine scene plan, audio map, and image map
- How to validate against the Zod schema
- How to apply consistent styling across scenes
- How to handle path resolution

**Agent Instructions Summary:**
1. Receive scene plan, audio metadata, image paths, and style config
2. For each scene:
   - Build scene props matching its type in InputPropsSchema
   - Attach audio track reference
   - Attach image path (if applicable)
3. Assemble audio tracks list
4. Assemble captions list from all scenes' audio metadata
5. Apply style defaults if not provided
6. Validate complete inputProps against Zod schema
7. Return validated CompositionResult

**Output:** `CompositionResult` dict with input_props

### 10.7 `video-render.skill.md`

**Purpose:** Teach the agent how to execute Remotion rendering.

**Teaches:**
- How to call `render_video()` MCP tool
- How to monitor render progress
- How to handle render cancellation or failure
- How to verify output file

**Agent Instructions Summary:**
1. Receive composition ID and inputProps from compose phase
2. Call `render_video(composition_id, input_props)`
3. Monitor progress via tool output (frame count / total frames)
4. Check for cancellation (kill switch) between status polls
5. On completion, verify output file exists and has reasonable size
6. If render fails, capture error and decide whether to retry (once)
7. Return RenderResult with output path and metadata

**Output:** `RenderResult` dict

### 10.8 `video-review.skill.md`

**Purpose:** Teach the agent how to review rendered video and publish to GitHub.

**Teaches:**
- How to call `review_video()` MCP tool
- How to interpret review results
- How to construct markdown comment for GitHub
- How to post comment via Publisher tool

**Agent Instructions Summary:**
1. Receive rendered video path from render phase
2. Call `review_video(video_path)`
3. Check review results:
   - All checks passed → proceed to publish
   - Warnings only → proceed with warning note
   - Failures → decide whether to retry render or skip publish
4. Construct markdown body:
   - Title, duration, scene count
   - Review results (checks passed/failed)
   - Link to video file
   - Call to action (e.g., "Watch the explainer video")
5. Call `publish_video()` MCP tool with target and metadata
6. Return PublishResult

**Markdown Template:**
```markdown
## 🎬 VideoForge Summary

**{title}**
{description}

- Duration: {duration_seconds}s
- Scenes: {scenes}
- Quality: {passed_checks}/{total_checks} checks passed

[Download Video]({video_url})
```

**Output:** `PublishResult` dict

---

## 11. Appendix

### 11.1 Glossary

| Term | Definition |
|------|-----------|
| MCP | Model Context Protocol — standard for AI-agent tool communication |
| FastMCP | Python framework for building MCP servers |
| Remotion | React-based programmatic video rendering framework |
| Composition | A Remotion video with defined duration, dimensions, and rendering logic |
| inputProps | JSON data passed into a Remotion composition at render time |
| TransitionSeries | Remotion component that manages sequential scenes with transitions |
| TransitionPresentation | Interface for defining custom scene transitions |
| TikTok-style captions | Word-level highlighted captions via `@remotion/captions` |
| Crossfade | Audio transition where first segment fades out as second fades in |
| HMAC-SHA256 | Hash-based message authentication code with SHA-256 |
| Kill switch | Environment variable that triggers graceful pipeline shutdown |
| Loop engineering | Development pattern using iterative agent feedback loops |
| LLM | Large Language Model (e.g., GPT-4o) |
| Discriminated union | Zod pattern where a `type` field determines the schema |
| Standard deviation tone | A particular perspective expressed with detached, clinical tone |

### 11.2 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VIDEOFORGE_KILL_SWITCH` | (unset) | Set to any truthy value to halt pipeline |
| `VIDEOFORGE_WEBHOOK_SECRET` | (unset) | HMAC-SHA256 secret for GitHub webhooks |
| `VIDEOFORGE_SERVER__NAME` | `VideoForge` | MCP server name |
| `VIDEOFORGE_SERVER__HOST` | `127.0.0.1` | MCP server bind address |
| `VIDEOFORGE_SERVER__PORT` | `8080` | MCP server port |
| `VIDEOFORGE_SERVER__LOG_LEVEL` | `INFO` | Logging level |
| `VIDEOFORGE_POCKET_TTS__SERVER_URL` | `http://127.0.0.1:8120` | Pocket TTS server URL |
| `VIDEOFORGE_POCKET_TTS__DEFAULT_VOICE` | `en_US-amy-medium` | Default TTS voice |
| `VIDEOFORGE_POCKET_TTS__MAX_RETRIES` | `3` | TTS retry count |
| `VIDEOFORGE_POCKET_TTS__TIMEOUT_SECONDS` | `60` | TTS request timeout |
| `VIDEOFORGE_PIPELINE__DEFAULT_FPS` | `30` | Video frames per second |
| `VIDEOFORGE_PIPELINE__DEFAULT_CODEC` | `h264` | Video codec |
| `VIDEOFORGE_PIPELINE__MAX_VIDEO_DURATION_SECONDS` | `180` | Max video length |
| `VIDEOFORGE_ASSETS__AI_GENERATION__ENABLED` | `false` | Enable AI image generation |
| `VIDEOFORGE_ASSETS__STOCK_PHOTOS__ENABLED` | `false` | Enable stock photos |

### 11.3 Configuration File Reference

**Full config.yaml specification:**

```yaml
# VideoForge Configuration
# ──────────────────────────
# This file uses YAML format.
# Environment variable overrides use VIDEOFORGE_{SECTION}__{KEY} convention.

server:
  name: VideoForge               # MCP server identifier
  host: 127.0.0.1                # Bind address (0.0.0.0 for all interfaces)
  port: 8080                     # MCP server port
  log_level: INFO                # DEBUG, INFO, WARNING, ERROR, CRITICAL

pocket_tts:
  server_url: http://127.0.0.1:8120  # Pocket TTS FastAPI base URL
  default_voice: en_US-amy-medium     # Default voice for speech generation
  language: en                        # Language code for TTS
  max_retries: 3                      # Retry attempts on TTS failure
  timeout_seconds: 60                 # HTTP request timeout

pipeline:
  max_video_duration_seconds: 180      # Maximum video length
  default_fps: 30                      # Frames per second
  default_resolution:
    width: 1920                        # Horizontal pixels
    height: 1080                       # Vertical pixels
  default_codec: h264                  # Video codec (h264, h265, vp9, gif)
  max_caption_tokens_per_chunk: 50     # Max tokens per TTS chunk

assets:
  ai_generation:
    enabled: false                     # Enable AI image generation
    provider: stable_diffusion         # Provider name (stable_diffusion, flux)
  stock_photos:
    enabled: false                     # Enable stock photo fetching
    provider: pexels                   # Provider name (pexels, pixabay)

github:
  webhook_secret_env: VIDEOFORGE_WEBHOOK_SECRET  # Env var name for webhook secret
  auto_post_pr_comments: true                     # Auto-comment on PRs
```

---

*End of VideoForge Technical Specification v1.0.0*
