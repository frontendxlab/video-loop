import "@testing-library/jest-dom";

/* ResizeObserver stub — needed by Radix UI components in jsdom */
globalThis.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
