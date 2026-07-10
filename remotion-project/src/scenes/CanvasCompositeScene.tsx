import React, { useRef, useEffect } from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { z } from "zod";
import { EffectLayerSchema } from "../effects/types";
import { compositeEffects } from "../effects/composite";
import { applyGlitch, applyVintage, applyMagnifier, renderTextContent } from "../effects/canvas-apply";
import { colors, fonts } from "../design-tokens";

export const CanvasCompositeSceneSchema = z.object({
  type: z.literal("canvas-composite"),
  title: z.string().min(1),
  subtitle: z.string().optional(),
  layers: z.array(EffectLayerSchema).min(1).max(5),
  duration: z.number().positive(),
  wordTimestamps: z
    .array(z.object({ text: z.string(), startMs: z.number(), endMs: z.number() }))
    .optional(),
  sceneStartFrame: z.number().optional().default(0),
});

export type CanvasCompositeSceneProps = z.infer<typeof CanvasCompositeSceneSchema>;

/**
 * Canvas composite scene — rasterises text content onto OffscreenCanvas,
 * applies effect pipeline (glitch, vintage, magnifier) per frame,
 * renders final pixels to visible <canvas>.
 *
 * Effect variants:
 *   - glitch + vintage     (glitchy retro look)
 *   - magnifier + glitch   (lens zoom + digital tear)
 *   - glitch only          (fast digital distortion)
 *   - vintage only         (warm film + grain)
 *   - magnifier only       (magnifying glass centre)
 *   - all three            (glitch + vintage + magnifier stacked)
 */
export const CanvasCompositeScene: React.FC<CanvasCompositeSceneProps> = ({
  title,
  subtitle,
  layers,
  duration: _duration,
  sceneStartFrame: _sceneStartFrame,
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;

    let pixelData = renderTextContent(
      title,
      subtitle,
      w,
      h,
      colors.backgroundGradient,
      colors.text,
      colors.primary,
      fonts.bodyFamily,
    );

    const composite = compositeEffects(layers, w, h, frame);

    for (const layer of layers) {
      switch (layer.type) {
        case "glitch": {
          if (composite.glitchOffsets) {
            pixelData = applyGlitch(pixelData, w, h, composite.glitchOffsets);
          }
          break;
        }
        case "vintage": {
          if (composite.vintageParams) {
            pixelData = applyVintage(pixelData, w, h, composite.vintageParams, frame);
          }
          break;
        }
        case "magnifier": {
          if (composite.magnifierMap) {
            pixelData = applyMagnifier(pixelData, w, h, composite.magnifierMap);
          }
          break;
        }
      }
    }

    const imageData = new ImageData(pixelData, w, h);
    ctx.putImageData(imageData, 0, 0);
  }, [frame, layers, title, subtitle, width, height, fps]);

  return (
    <AbsoluteFill>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        style={{ width, height }}
      />
    </AbsoluteFill>
  );
};
