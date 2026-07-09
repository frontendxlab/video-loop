# Graph Report - .  (2026-07-09)

## Corpus Check
- 130 files · ~75,045 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 826 nodes · 1177 edges · 78 communities (62 shown, 16 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 179 edges (avg confidence: 0.69)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- TTS Adapter
- Pipeline Orchestrator
- Project Goals & RTK
- Frame Review
- App Runner / TUI
- Error Handling
- Configuration
- Logic Checking
- Remotion UI Dependencies
- Scene Types
- Content Chunking
- MCP Server
- Fact Checking
- MCP Tools
- Remotion Render
- Scene Components
- CLI Tools
- TypeScript Config
- GitHub Publisher
- Scene React Components
- Video Timing
- Composition Data
- Caption Overlay
- Animated Code Lines
- Animated Mind Map
- Composition Root
- Test Fixtures
- Video Generation
- Scaffold Tests
- Composition Registry
- Transitions
- Scene Planner
- Compose Props
- L2 Boundaries
- TTS Server
- Captions Generation
- Audio Stitcher
- Script Writer
- OpenCode Config
- Plugin Package
- Graphify Plugin
- L1 Integrity
- Status Module
- Engine Package
- Orchestrator Package
- Community 46

## God Nodes (most connected - your core abstractions)
1. `Config` - 31 edges
2. `VideoForge` - 18 edges
3. `MainScreen` - 17 edges
4. `TTSAdapter` - 15 edges
5. `VideoForgeError` - 15 edges
6. `FrameReviewer` - 15 edges
7. `compilerOptions` - 14 edges
8. `GitHubAuthError` - 14 edges
9. `GitHubNetworkError` - 14 edges
10. `create_app()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `build_video()` --calls--> `FrameReviewer`  [INFERRED]
  scripts/generate_video.py → src/videoforge/review/frame_reviewer.py
- `build()` --calls--> `FrameReviewer`  [INFERRED]
  scripts/orchestrator.py → src/videoforge/review/frame_reviewer.py
- `adapter()` --calls--> `TTSAdapter`  [INFERRED]
  tests/audio/test_tts_adapter.py → src/videoforge/audio/adapter.py
- `chunker()` --calls--> `Chunker`  [INFERRED]
  tests/audio/test_chunker.py → src/videoforge/audio/chunker.py
- `test_exceptions_hierarchy()` --indirect_call--> `RenderError`  [INFERRED]
  tests/test_imports.py → src/videoforge/exceptions.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Video Generation Pipeline Phases** — docs_prd_video_pipeline_orchestration, docs_prd_mcp_server_module, docs_prd_remotion_project_module, docs_prd_tts_integration_module, docs_prd_github_integration_module, docs_prd_content_validation_module, docs_prd_review_qa_module [EXTRACTED 1.00]
- **Content Validation Framework** — docs_spec_fact_checker, docs_spec_logic_checker, docs_spec_5_level_frame_review, docs_prd_content_validation_module, docs_prd_review_qa_module [EXTRACTED 1.00]
- **Devils Advocate Design Iteration Outcomes** — docs_research_v1_0_0_devil_advocate_chain, docs_research_v1_0_0_16_agents, docs_research_v1_0_0_remotion_vs_hyperframes, docs_research_v1_0_0_drop_animotion, docs_research_v1_0_0_manim_gate, docs_research_v1_0_0_wavs_base64_decision, docs_research_v1_0_0_async_webhook, docs_research_v1_0_0_3_tier_asset, docs_research_v1_0_0_mcp_advantage [EXTRACTED 1.00]

## Communities (78 total, 16 thin omitted)

### Community 0 - "TTS Adapter"
Cohesion: 0.05
Nodes (32): Path, TTSAdapter, ConfigError, GitHubAuthError, GitHubNetworkError, GitHubNotFoundError, KillSwitchError, PipelineError (+24 more)

### Community 1 - "Pipeline Orchestrator"
Cohesion: 0.05
Nodes (59): Argument, Enum, build(), _estimate_timestamps(), _generate_scene_plan(), grill(), mcp(), plan() (+51 more)

### Community 2 - "Project Goals & RTK"
Cohesion: 0.07
Nodes (42): Rust Token Killer (RTK), VideoForge, 5-Minute Render Goal, Agent-Agnostic Design Goal, Fully Local Pipeline Goal, MCP-Native Architecture Goal, Milestone Plan M0-M4, MVP Definition v1.0 (+34 more)

### Community 3 - "Frame Review"
Cohesion: 0.10
Nodes (11): FrameReviewer, Any, L3Smoothness, Any, L4Transitions, Any, L5Consistency, Any (+3 more)

### Community 4 - "App Runner / TUI"
Cohesion: 0.11
Nodes (17): App, ComposeResult, Screen, AgentLog, AgentStatus, PipelineRunner, Pipeline runner — executes video generation pipeline asynchronously., Async pipeline runner that emits events for the TUI. (+9 more)

### Community 5 - "Error Handling"
Cohesion: 0.09
Nodes (16): Exception, handle_phase_error(), PipelinePhaseError, Any, Pipeline, Any, Any, StateMachine (+8 more)

### Community 6 - "Configuration"
Cohesion: 0.08
Nodes (3): Config, load_config(), Any

### Community 7 - "Logic Checking"
Cohesion: 0.08
Nodes (16): LogicChecker, Any, Logic checker for validating scene plans and scripts., Check scene durations for pacing issues., Run all checks and return a comprehensive report., Check that the scene sequence has a complete narrative arc., Check that cause/effect claims in the script are supported by scene content., Verify scenes are in logical order. (+8 more)

### Community 8 - "Remotion UI Dependencies"
Cohesion: 0.07
Nodes (29): dependencies, react, react-dom, remotion, @remotion/bundler, @remotion/captions, @remotion/cli, @remotion/google-fonts (+21 more)

### Community 9 - "Scene Types"
Cohesion: 0.07
Nodes (26): AudioTrack, AudioTrackSchema, BulletScene, BulletSceneSchema, Caption, CaptionSchema, CodeScene, CodeSceneSchema (+18 more)

### Community 10 - "Content Chunking"
Cohesion: 0.10
Nodes (6): Chunker, chunker(), Tests for audio chunker (sentence splitting + token grouping)., TestChunkGrouper, TestSentenceSplitter, TestTokenCounter

### Community 11 - "MCP Server"
Cohesion: 0.11
Nodes (21): FastMCP, create_app(), _enqueue_job(), _execute_tool_sync(), _get_job_status(), Any, Tests for basic MCP tools., test_health_check_returns_ok() (+13 more)

### Community 12 - "Fact Checking"
Cohesion: 0.09
Nodes (12): FactChecker, Any, Fact-checking utility for verifying script claims against source code., Validates factual claims in scripts against source code diffs., Parse script text and extract factual claims., Verify if a claim is supported by the source diff., Full fact check of a script against source diff., fact_checker() (+4 more)

### Community 13 - "MCP Tools"
Cohesion: 0.11
Nodes (21): engine_estimate_timing(), engine_generate_tts(), engine_plan_scenes(), engine_review_video(), MCP tool wrappers — expose the deterministic video engine as MCP tools.  Any MCP, Run L1 Frame Review on a rendered video.      Args:         video_path: Path to, Estimate word-level timestamps for audio-synced animations.      Args:         w, Plan video scenes from a topic description.      Args:         topic: The video (+13 more)

### Community 14 - "Remotion Render"
Cohesion: 0.13
Nodes (10): RenderError, Remotion render executor., Orchestrates a Remotion render subprocess., RenderExecutor, ProgressParser, Remotion stdout progress parser., Parses frame progress lines from Remotion stdout., executor() (+2 more)

### Community 15 - "Scene Components"
Cohesion: 0.15
Nodes (15): BulletSceneSchema, ComparisonScene(), ComparisonSceneProps, ComparisonSceneSchema, DiagramScene(), DiagramSceneProps, DiagramSceneSchema, NodeSchema (+7 more)

### Community 16 - "CLI Tools"
Cohesion: 0.19
Nodes (17): ask(), batch(), estimate_timestamps(), gui(), info(), log(), make_bullet_scene(), make_code_walkthrough() (+9 more)

### Community 17 - "TypeScript Config"
Cohesion: 0.12
Nodes (16): compilerOptions, declaration, esModuleInterop, forceConsistentCasingInFileNames, jsx, module, moduleResolution, noUnusedLocals (+8 more)

### Community 18 - "GitHub Publisher"
Cohesion: 0.18
Nodes (5): Publisher, _enqueue_job(), handle_webhook(), TestPublisher, TestWebhookHandler

### Community 19 - "Scene React Components"
Cohesion: 0.21
Nodes (12): BulletScene(), BulletSceneProps, CodeScene(), CodeSceneProps, CodeSceneSchema, TitleScene(), TitleSceneProps, TitleSceneSchema (+4 more)

### Community 20 - "Video Timing"
Cohesion: 0.15
Nodes (13): build_timeline(), frame_to_ms(), get_active_step(), get_progress(), ms_to_frame(), WordTiming, Timing engine — deterministic frame-to-audio computation.  Converts word-level t, Compute animation progress (0 to 1) within an audio time window.      Args: (+5 more)

### Community 21 - "Composition Data"
Cohesion: 0.18
Nodes (9): MindMapNode, AudioTrack, CaptionWord, SceneData, VideoCompositionProps, WordTimingData, OutroScene(), OutroSceneProps (+1 more)

### Community 22 - "Caption Overlay"
Cohesion: 0.40
Nodes (7): CaptionOverlay(), CaptionOverlayProps, frameToMs(), getCurrentWord(), getCurrentWordIndex(), getWordOpacity(), WordTiming

### Community 23 - "Animated Code Lines"
Cohesion: 0.27
Nodes (8): AnimatedCodeLines(), KEYWORDS_TS, Token, tokenizeLine(), codeTheme, colors, fonts, spacing

### Community 24 - "Animated Mind Map"
Cohesion: 0.31
Nodes (9): AnimatedCodeLinesProps, AnimatedMindMap(), AnimatedMindMapProps, assignPositions(), COLORS, connectionPath(), flattenBFS(), subtreeWidth() (+1 more)

### Community 25 - "Composition Root"
Cohesion: 0.22
Nodes (8): VideoComposition(), AudioTrackSchema, CaptionWordSchema, DEFAULT_PROPS, InputPropsSchema, RemotionRoot(), SceneSchema, WordTimingSchema

### Community 26 - "Test Fixtures"
Cohesion: 0.20
Nodes (5): Any, Path, Shared fixtures for all test modules., sample_scene_plan(), temp_dir()

### Community 27 - "Video Generation"
Cohesion: 0.33
Nodes (8): build_video(), generate_tts(), Any, Path, Get real WAV duration from file size, not the streaming placeholder header., Generate TTS audio via Pocket TTS. Returns actual duration in seconds., Full pipeline: TTS -> compose -> render -> return MP4 path., wav_actual_duration()

### Community 29 - "Composition Registry"
Cohesion: 0.29
Nodes (6): COMPOSITION_IDS, CompositionId, CompositionRegistry, SCENE_TYPES, SceneBase, SceneType

### Community 32 - "Compose Props"
Cohesion: 0.33
Nodes (4): ComposeProps, Any, Compose inputProps for Remotion from pipeline output., Builds the inputProps JSON dict from the pipeline's scene plan and asset maps.

## Knowledge Gaps
- **109 isolated node(s):** `$schema`, `plugin`, `@opencode-ai/plugin`, `videoforge`, `name` (+104 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FrameReviewer` connect `Frame Review` to `CLI Tools`, `Pipeline Orchestrator`, `Video Generation`, `MCP Tools`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Why does `VideoForgeError` connect `TTS Adapter` to `Error Handling`, `Remotion Render`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `MainScreen` (e.g. with `AgentLog` and `AgentStatus`) actually correct?**
  _`MainScreen` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `TTSAdapter` (e.g. with `TTSConnectionError` and `TTSTimeoutError`) actually correct?**
  _`TTSAdapter` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `plugin`, `@opencode-ai/plugin` to the rest of the system?**
  _198 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `TTS Adapter` be split into smaller, more focused modules?**
  _Cohesion score 0.05405405405405406 - nodes in this community are weakly interconnected._
- **Should `Pipeline Orchestrator` be split into smaller, more focused modules?**
  _Cohesion score 0.05336951605608322 - nodes in this community are weakly interconnected._