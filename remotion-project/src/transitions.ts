import { TransitionPresentation } from "@remotion/transitions";

const defaultDurationInFrames = 30;

type TransitionFn = (props?: {
  durationInFrames?: number;
}) => TransitionPresentation<Record<string, unknown>>;

export const fade: TransitionFn = (props) => {
  const durationInFrames = props?.durationInFrames ?? defaultDurationInFrames;
  return {
    component: ({ progress }) => (
      <div
        style={{
          opacity: progress,
          width: "100%",
          height: "100%",
        }}
      />
    ),
    durationInFrames,
  };
};

export const slide: TransitionFn = (props) => {
  const durationInFrames = props?.durationInFrames ?? defaultDurationInFrames;
  return {
    component: ({ progress }) => (
      <div
        style={{
          transform: `translateX(${100 * (1 - progress)}%)`,
          width: "100%",
          height: "100%",
        }}
      />
    ),
    durationInFrames,
  };
};

export const wipe: TransitionFn = (props) => {
  const durationInFrames = props?.durationInFrames ?? defaultDurationInFrames;
  return {
    component: ({ progress }) => (
      <div
        style={{
          clipPath: `inset(0 ${100 * (1 - progress)}% 0 0)`,
          width: "100%",
          height: "100%",
        }}
      />
    ),
    durationInFrames,
  };
};

export const flip: TransitionFn = (props) => {
  const durationInFrames = props?.durationInFrames ?? defaultDurationInFrames;
  return {
    component: ({ progress }) => (
      <div
        style={{
          transform: `rotateY(${180 * (1 - progress)}deg)`,
          backfaceVisibility: "hidden",
          width: "100%",
          height: "100%",
        }}
      />
    ),
    durationInFrames,
  };
};

export const crossfade: TransitionFn = (props) => {
  const durationInFrames = props?.durationInFrames ?? defaultDurationInFrames;
  return {
    component: ({ progress }) => (
      <div
        style={{
          opacity: progress,
          width: "100%",
          height: "100%",
        }}
      />
    ),
    durationInFrames,
  };
};
