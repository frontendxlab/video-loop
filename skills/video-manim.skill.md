# Video Manim Scene Generation Skill

Generate Manim animation code for video scenes in the VideoForge pipeline.

## When To Use

- A scene calls for mathematical visualization, geometric animation, or complex motion graphics
- User requests "manim animation" or "mathematical visualization" in a video scene
- A scene type maps better to programmatic animation than pre-composed Remotion components
- The scene requires dynamic graph plotting, function visualization, or geometric proofs

## Scene Type: MANIM

Add to the scene plan a scene with `"type": "manim"` and `"renderer": "manim"`.

## Manim Code Template

For each Manim scene, generate a complete Python script:

```python
from manim import *
import numpy as np

config.frame_rate = 30
config.pixel_width = 1920
config.pixel_height = 1080
config.quality = "high_quality"
config.background_color = "#1a1a2e"


class SceneName(Scene):
    def construct(self):
        # Background
        bg = Rectangle(
            width=config.frame_width, height=config.frame_height,
            fill_opacity=1, color=config.background_color
        )
        self.add(bg)

        # Title
        title = Tex(r"Scene Title", color=WHITE, font_size=48)
        title.to_edge(UP)
        self.play(Write(title), run_time=0.5)

        # Animation content
        # ... scene-specific animation ...

        self.wait(1.0)
```

## Quality Settings

- `-qh` (high quality): 1920x1080, for final output
- `-ql` (low quality): 854x480, for previews/tests

## Output Integration

Manim renders audio-free. After rendering:
1. Manim output video path is returned (find in `media/videos/` dir)
2. Copy to scene build dir as `scene_NNNN.mp4`
3. Audio TTS track is mixed in during concat step (same as Remotion scenes)

## Scene Templates by Content

| Content | Manim Element | Code |
|---------|--------------|------|
| Graph/plot | `Axes`, `Graph`, `FunctionGraph` | Plot mathematical functions |
| Geometric | `Circle`, `Square`, `Polygon`, `Angle` | Geometry animations |
| Equation | `Tex`, `MathTex` with transforms | Equation solving steps |
| Matrix | `Matrix`, `DecimalMatrix` | Matrix operations |
| Number line | `NumberLine`, `NumberPlane` | Number line animations |
| 3D | `ThreeDScene`, `Sphere`, `Cube` | 3D rotations and views |
| Comparison | `VennDiagram`, `BarChart` | Compare concepts |
| Animation | `Create`, `Transform`, `FadeIn`, `Rotate` | Element transitions |

## Quality Gates

- [ ] Manim code is valid Python (syntax checked)
- [ ] Scene class name matches title (alphanumeric only)
- [ ] `config.frame_rate` matches VideoDefinition fps
- [ ] Resolution matches 1920x1080
- [ ] Animation duration matches scene.duration frames
- [ ] Output video exists and has correct duration
