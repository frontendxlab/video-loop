import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { z } from "zod";
import { ThreeScene } from "../components/three/ThreeScene";

export const ThreeSceneExampleSchema = z.object({
  type: z.literal("three"),
  duration: z.number().positive(),
});

export type ThreeSceneExampleProps = z.infer<typeof ThreeSceneExampleSchema>;

/**
 * Example 3D content: spinning cube.
 * Replace children with any R3F-compatible scene graph.
 */
const SpinningCube: React.FC = () => {
  const frame = useCurrentFrame();
  const rotation = interpolate(frame, [0, 60], [0, Math.PI * 2]);

  return (
    <mesh rotation={[rotation, rotation * 0.5, 0]}>
      <boxGeometry args={[1.5, 1.5, 1.5]} />
      <meshStandardMaterial color="#e11d48" />
    </mesh>
  );
};

export const ThreeSceneExample: React.FC<ThreeSceneExampleProps> = () => {
  return (
    <ThreeScene camera={{ position: [0, 0, 5] }}>
      <SpinningCube />
    </ThreeScene>
  );
};
