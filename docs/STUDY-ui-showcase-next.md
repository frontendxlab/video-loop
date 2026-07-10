# VideoForge Study — Showcase Patterns, UI Architecture, Next Tasks

## Goal

Build VideoForge into deterministic multi-engine video director with interactive web UI.

This study captures:
- Remotion showcase patterns worth absorbing
- mapping into VideoForge scene kinds and orchestration
- web UI architecture using TanStack Start + shadcn/ui
- SSE / queue / job model
- next focused build tracks

---

## 1. Remotion showcase patterns worth absorbing

Source studied: `https://www.remotion.dev/prompts`

### Pattern map

| Prompt showcase | Likely Remotion features | VideoForge additions |
|---|---|---|
| Travel Route on Map with 3D landmarks | `@remotion/three`, map tiles, route path draw, camera move | `map3d`, route scene, landmark overlay |
| News article headline highlight | blur/unblur, text focus, marker overlay, perspective transform | `document-highlight`, OCR/text focus scene |
| Product Demo for Presscut | screen mockups, cursor, feature callouts, UI replication | `screenflow`, product demo scene |
| Launch Video on X | multi-sequence narrative, terminal/cards, layered promo scenes | richer `promo` scene family |
| Cinematic Tech Intro | 3D text, particles, glass HUD, scanner lines | `hero-intro`, cinematic opener |
| Transparent CTA overlay | transparent export, lower-third CTA | `overlay-cta`, lower-third, outro overlay |
| Rocket Launches Timeline | timeline + curved path motion | `trajectory-timeline` |
| Real Estate Investing | counters, lower thirds, footage overlays | `real-estate`, metric overlays |
| Three.js Top 20 Games Sold Ranking | 3D ranking bars, camera fly-through | `3d-ranking` |
| Promotion video for VVTerm | product hero + feature walkthrough | `product-promo` |
| Music CD store promo | audio-reactive visuals | `audio-reactive` |
| Bar + Line Chart combined | hybrid chart animation | `dual-chart` |

### Orchestration implications

- director needs recipe registry, not only scene kind registry
- each recipe must specify:
  - allowed inputs
  - scene graph shape
  - preferred engine(s)
  - transition pack
  - review rules
- recipes must remain deterministic
- AI may help review and repair, not author frames directly

---

## 2. Engine mapping guidance

### Remotion

Best for:
- typography-heavy scenes
- product demos / screenflow
- overlay CTA
- hero intros using Three.js
- audio-reactive scenes
- 3D ranking scenes

### Manim

Best for:
- charts with exact geometry
- graph / system diagrams with layout math
- timelines with exact axes / ticks
- math-heavy explanatory scenes

### Animotion

Best for:
- interactive-feeling HTML scenes
- UI-like diagrams
- lightweight staged HTML animations
- operator-friendly web-motion scenes

---

## 3. UI architecture target

### Stack

- TanStack Start
- shadcn/ui
- TanStack Query
- SSE for live updates
- background job queue
- existing Python engine / reports / provenance as backend source of truth

### Principle

UI does not own orchestration logic.

UI only:
- starts jobs
- streams job state
- shows scene graph / routing / frames / reports
- lets operator retry, stop, reroute, or repair

Deterministic director stays server-side.

---

## 4. UI surfaces

### 4.1 App shell

- left sidebar: Jobs, Create, Recipes, Reports, Settings
- top bar: active job, queue state, provider/model, quick actions
- command palette for jump / retry / rerun / open artifacts

### 4.2 Create flow

- prompt input
- grill panel
- recipe suggestions
- provider / model selection
- director preview before run

### 4.3 Job detail

- stage timeline
- SSE stream log
- subagent cards
- todo/checklist panel
- scene graph / engine routing view
- render progress / review progress

### 4.4 Scene detail

- scene payload
- scene hash
- engine chosen and reason
- generated frames / thumbnails
- per-scene report
- rerender / retry / reroute controls

### 4.5 Reports

- final video report
- provenance graph
- per-scene reports
- overlap / coherence / L0 / L1 summaries

### 4.6 Settings

- provider config
- model config
- queue concurrency
- retry budgets
- review thresholds
- token/theme view

---

## 5. SSE event model

### Event stream endpoint

`/api/jobs/$jobId/stream`

### Event types

- `job.started`
- `job.stage`
- `job.todo`
- `prompt.grilled`
- `director.scene_planned`
- `director.scene_routed`
- `subagent.started`
- `subagent.token`
- `subagent.completed`
- `subagent.failed`
- `render.scene_started`
- `render.scene_completed`
- `review.issue`
- `repair.plan`
- `retry.started`
- `artifact.ready`
- `job.completed`
- `job.failed`

### UI behavior

- keep scrollable event log
- derive stage timeline from event stream
- show subagent status live
- show queue state and retries live
- toast on important transitions

---

## 6. Queue / job model

### Core queues

- `jobs`
- `scene_tasks`
- `review_tasks`
- `repair_tasks`
- `subagent_tasks`

### Deterministic identity

- job id from request + time or explicit run id
- scene ids from IR
- cache keys from content hash + stage

### Required job controls

- stop job
- retry scene
- retry failed subagent
- reroute engine for scene
- rerun review only

---

## 7. Backend-to-UI contracts needed

### Required server functions / API

- `startJob`
- `grillPrompt`
- `loadJob`
- `listJobs`
- `stopJob`
- `retryJob`
- `retryScene`
- `retrySubagent`
- `rerouteScene`
- `updateProviderConfig`
- `updateModelConfig`
- `loadArtifacts`

### Required persisted artifacts

- final video report JSON
- provenance JSON
- per-scene report JSON
- coherence sidecar
- scene thumbnails / sampled frames

---

## 8. Next implementation tracks

### Track 1 — UI shell + SSE + jobs

Deliver:
- TanStack Start app scaffold
- shadcn base shell
- Jobs dashboard
- Job detail page
- SSE event stream plumbing
- queue status / subagent list / live timeline

### Track 2 — prompt / grill / director / scenes

Deliver:
- create job flow
- grill interaction panel
- director preview panel
- scene graph viewer
- engine routing badges + reasoning
- scene detail / frames / reports

### Track 3 — showcase recipes + advanced review controls

Deliver:
- recipe registry from showcase study
- recipe picker / recipe preview
- advanced review controls
- retry / repair / reroute controls
- provider/model setup and per-run override

---

## 9. Subagent fanout guidance

When spawning many subagents, split by file ownership.

### UI shell + SSE + jobs

- route scaffold
- shell/nav/layout
- SSE backend endpoint
- job list page
- job detail event panel
- subagent cards
- queue summary widgets

### prompt / grill / director / scenes

- create form
- grill panel
- provider/model settings forms
- scene graph view
- scene detail page
- frame thumbnail panel
- routing explanation UI

### showcase recipes + advanced review controls

- recipe schema + registry
- recipe explorer page
- recipe to director mapping
- review controls panel
- repair plan viewer
- retry/reroute controls

---

## 10. Guardrails

- keep deterministic backend authoritative
- keep UI additive, not rewrite of engine
- do not mix business logic into client state
- persist every important decision as artifact or event
- prefer SSE + polling fallback over bespoke websocket complexity
- keep each scene, report, and subagent trace inspectable

---

## 11. Recommended immediate build order

1. Scaffold TanStack Start app
2. Add shadcn UI primitives and shell
3. Add SSE endpoint + event model
4. Build Jobs page and Job detail page
5. Wire existing artifacts and reports into UI
6. Build prompt + grill flow
7. Add director preview and scene graph
8. Add recipe registry and prompt showcase mapping
9. Add review controls / repair panel
10. Add provider/model settings + queue controls

---

## 12. Required next major track — full Remotion case-study and prompt inspection

This is mandatory next-track work.

### Objective

Inspect all relevant Remotion prompt showcases / case studies / outstanding human-made examples,
extract recurring methodology, and bring those patterns into VideoForge deterministically.

### What to study

- all pages under `https://www.remotion.dev/prompts`
- related showcase/case-study pages if they reveal motion, composition, scene structure, or code clues
- any linked code examples, public repos, demos, or embedded implementation hints

### What to extract from each case

- visual goal
- scene grammar
- motion grammar
- transition pattern
- typography pattern
- 2D vs 3D usage
- data/asset requirements
- likely Remotion primitives / packages used
- what belongs in deterministic director
- what belongs in Remotion engine implementation
- what belongs in Manim / Animotion fallback or complement
- what quality gates are needed to preserve the effect deterministically

### What VideoForge should produce from this study

1. `case-study registry`
2. `showcase recipe registry` expansion
3. `motion pack registry`
4. `transition pack registry`
5. `composition methodology guide`
6. `engine-routing heuristics` updates
7. `review/gate heuristics` updates
8. `golden demo backlog` for top showcase-style outputs

### Expected implementation outcome

VideoForge should not only mimic isolated scenes.
It should absorb the methodology behind those scenes:

- layered composition
- camera choreography
- typography cadence
- asset staging
- motion pacing
- transition consistency
- hybrid 2D/3D scene building
- deterministic prompt-to-scene decomposition

### Required follow-up tasks

- crawl prompts pages and linked examples
- write structured case-study artifacts into repo docs/data
- map each case to scene kinds / recipes / engines
- identify reusable motion systems and component abstractions
- implement top-priority patterns in Remotion first
- extend director to choose those patterns deterministically
- add review checks specific to those showcase patterns

### Full paginated prompt showcase inventory captured

#### Page 1
- Travel Route on Map with 3D landmarks
- News article headline highlight
- Product Demo for Presscut
- Launch Video on X
- Cinematic Tech Intro
- Transparent Call-To-Action overlay
- Rocket Launches Timeline
- Real Estate Investing
- Three.js Top 20 Games Sold Ranking
- Promotion video for VVTerm
- Music CD store promo
- Bar + Line Chart (combined)

#### Page 2
- Shape to words transformation
- Cursor Agent Skills Announcement
- Spinning, glitching SVG Logo turned 3D
- 3D Retro Pixel Font
- Strava Run visualized
- The Kinetic Marketing
- Audio Spectrum Visualizer
- HTML-in-canvas magnifying glass
- Glitch effect (HTML-in-canvas)
- Vintage screen effect (HTML-in-canvas)
- BMS Active Cell Balancing Animation - 8S1P Pack with Energy Flow Visualization
- Solar System Orbit Animation

#### Page 3
- Apple-Style Device Rise Animation

### Methodology extracted from full showcase pages

#### Recurring visual systems
- 3D product/device hero scenes
- SVG path draw / path morph animation
- HTML-in-canvas post-processing effects
- audio-reactive spectrum / waveform scenes
- kinetic typography / per-character timing
- chart-heavy and dual-axis data stories
- UI mockup / screenflow walkthroughs
- glassmorphism / HUD / cyber overlays
- map / geo route animation
- particle-based atmosphere and decorative motion

#### Recurring implementation patterns
- `useCurrentFrame()` + `interpolate()` everywhere
- `spring()` for entrances and emphasis
- `Sequence` / `Series` / `TransitionSeries` for orchestration
- `@remotion/three` for 3D device, product, ranking, orbit scenes
- SVG path animation for timelines, routes, morphs
- canvas compositing for glitch / vintage / magnifier effects
- audio analysis (`useAudioData`, `visualizeAudio`) for music and motion
- typed reusable motion packs, not one-off scene logic

### Concrete VideoForge backlog derived from showcase study

#### New scene kinds to add
- `map3d`
- `document-highlight`
- `screenflow`
- `hero-intro`
- `overlay-cta`
- `trajectory-timeline`
- `3d-ranking`
- `audio-reactive`
- `dual-chart`
- `svg-morph`
- `three-scene`
- `kinetic-text`
- `canvas-composite`

#### New reusable packs/components
- motion pack registry
- transition pack registry
- glass card / HUD components
- lower third / overlay CTA components
- device frame / screenflow components
- dual-axis chart components
- audio spectrum / waveform components
- particle background system
- map route system
- Three.js scene base + camera rig
- SVG morph/path animation system
- canvas effect pipeline (glitch, vintage, magnifier)

#### Director updates needed
- recipe-driven scene planning
- payload-aware engine routing (`chart:3d`, `timeline:rich`, `map3d`, `screenflow`)
- overlay stack support in scene graph
- per-recipe review hints and quality thresholds

#### Review/gate updates needed
- alpha/overlay validation
- route bounds validation for maps
- dual-axis correctness checks
- text highlight substring validation
- audio-reactive timing quality checks
- 3D scene visibility checks
- canvas effect tolerance checks

### Priority rule for next implementation waves

1. web UI and backend contracts
2. recipe registry + recipe-driven orchestration
3. Remotion engine expansion for showcase patterns
4. review gates specialized to those patterns
5. golden demo fixtures for top showcase outputs
