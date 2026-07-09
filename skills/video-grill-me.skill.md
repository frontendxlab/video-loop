# VideoForge Grill-Me — Requirement Gathering Skill

> Inspired by Matt Pocock's `grill-me` skill. Use this BEFORE creating any video to
> extract precise requirements, define the visual approach, and set quality criteria.

## Step 1: Define the Video Purpose

Ask these questions to the user/requester:

1. **What is the video topic?** (one sentence)
2. **Who is the target audience?** (beginner, intermediate, expert)
3. **What is the desired length?** (seconds or minutes)
4. **What is the key takeaway?** (what should viewers remember?)
5. **What is the tone?** (professional, casual, technical, inspiring)

## Step 2: Choose Visual Approach Per Section

For each section of the content, determine the best visual treatment:

| Content Type | Recommended Scene Type | Why |
|---|---|---|
| Title / Section header | `title` | Clean, centered title with spring entry |
| List of concepts | `bullet` | Staggered card entries, audio-synced |
| Code example | `code-walkthrough` | Line-by-line reveal with audio timing |
| Architecture / Taxonomy | `mindmap` | Tree diagram, nodes draw in as narrated |
| Image / Screenshot | `image` | Full-bleed with Ken Burns effect |
| Side-by-side compare | `comparison` | Split screen with animated divider |
| Before/after code | `diff` | Red/green diff with line matching |
| Ending / CTA | `outro` | Centered card with call-to-action |

## Step 3: Plan Animation Timing

For each scene, determine the word-to-animation mapping:

1. Count total words in narration text
2. Divide words by number of visual elements (bullet points, mind map nodes, code lines)
3. Each visual element animates in during its word range using `getStepProgress()`
4. Previous elements dim to 0.4-0.5 opacity when new elements appear

## Step 4: Set Quality Gates

Before rendering, verify:

- [ ] All scenes have `wordTimestamps` computed from TTS duration
- [ ] Each scene passes `sceneStartFrame` to its Remotion component
- [ ] BulletScene divides words evenly across points
- [ ] MindMap nodes have `timing.startMs`/`endMs` matching narration order
- [ ] Code-walkthrough lines have proportional word ranges
- [ ] Total video frames match expected duration (±5%)
- [ ] Audio tracks exist for every scene
- [ ] Audio files are copied to `public/audio/`

## Step 5: Define Visual Style

```
Background: gradient(#0f0f23, #1a1a3e)
Cards: rgba(255,255,255,0.06) with backdrop-blur(2px), radius 16px
Text: white (#fff), headings 700 weight, body 400 weight
Accents: #4a90d9 (primary blue), #7c5cbf (purple), #ffeb3b (highlight yellow)
Animations: spring(damping: 12-14, stiffness: 90-100), smooth cubic-bezier fades
Transitions: fade (0.5s), slide (0.6s), wipe (0.4s)
```

## Verification Checklist

After video is generated:

- [ ] Each scene's animation timing matches its audio narration
- [ ] No frames show overlapping elements from previous scenes
- [ ] Captions highlight the correct word at the correct time
- [ ] Mind map nodes appear in the order they are narrated
- [ ] Code lines appear as the narrator reads them
- [ ] Video passes L1 Frame Review (no black/frozen frames)
