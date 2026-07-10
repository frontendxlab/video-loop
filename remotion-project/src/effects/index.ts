export {
  compositeEffects,
  computeGlitchOffsets,
  computeVintageParams,
  computeMagnifierDisplacement,
} from "./composite";
export type { VintageParams, MagnifierMap } from "./composite";
export {
  applyGlitch,
  applyVintage,
  applyMagnifier,
  renderTextContent,
} from "./canvas-apply";
export {
  EffectLayerSchema,
  GlitchConfigSchema,
  VintageConfigSchema,
  MagnifierConfigSchema,
} from "./types";
export type {
  EffectLayer,
  GlitchConfig,
  VintageConfig,
  MagnifierConfig,
  EffectType,
} from "./types";
