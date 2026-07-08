# VideoForge — Lessons Learned (E2E Testing)

> Updated: 2026-07-08 after 53.5s exam video generated successfully.

## Pocket TTS Integration

### Problem: `tts_model = None` in HTTP server
The `pocket-tts serve` CLI command loads the model via `TTSModel.load_model()` in the CLI handler,
then starts uvicorn with `uvicorn.run("pocket_tts.main:web_app")`. The uvicorn import creates a
separate scope where the module-level `tts_model` is `None`.

**Fix**: Load model FIRST, create FastAPI app SECOND, start uvicorn THIRD. See `scripts/run_tts_server.py`.

### Problem: WAV header has `setnframes(1_000_000_000)`
The Pocket TTS StreamingWAVWriter uses `setnframes(1_000_000_000)` as a placeholder because it
doesn't know the final frame count during streaming. Calling `wave.open().getnframes()` returns
this placeholder (1 billion frames), giving a false duration of 41666 seconds.

**Fix**: Calculate actual duration from file size:
```python
data_bytes = file_size - 44  # WAV header
duration = data_bytes / (sampwidth * channels) / framerate
```
Our `scripts/generate_video.py` contains the `wav_actual_duration()` helper.

## Remotion

### Problem: All compositions hardcoded to TitleScene
The initial Root.tsx registered every composition ID with the TitleScene component, ignoring
the scene type differentiation.

**Fix**: Use a single VideoComposition component that accepts a `scenes` array and dispatches
to the correct scene type via a switch statement. Use `calculateMetadata` to set dynamic
`durationInFrames` from scene durations.

### Problem: Missing `@remotion/cli` dependency
The Remotion CLI (`npx remotion render`) requires `@remotion/cli` to be installed. It's not
included transitively by the core `remotion` package.

**Fix**: Add `@remotion/cli` to `remotion-project/package.json`.

## Frame Reviewer

### L1 (Frame Integrity)
Works well. Requires FFmpeg with blackdetect/freezedetect filters. Returns 1605 frames, 0 issues.

### L2-L5 (Boundaries, Smoothness, Transitions, Consistency)
Require FFprobe/FFmpeg frame extraction on the rendered video. For a 53s video at 1080p,
this takes significant time. These levels work correctly but are slow.

## Verified Pipeline

```
Script (7 scenes, 115 words)
  → TTS (Pocket TTS, voice=alba, 3.6-12.6s per scene)
  → Durations (file-size method, 53.5s total)
  → Scene plan (types + timing)
  → Remotion inputProps (Zod-validated)
  → npx remotion render (H.264, 1920x1080, 30fps, 4.7MB)
  → Frame Review L1 (passed: 0 issues, 1605 frames)
```
