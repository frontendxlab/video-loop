import { describe, expect, it } from "vitest";

import rawTokens from "../../config/design-tokens.json";
import { animotionTheme, codeTheme, colors, fonts, remotionStyleDefaults } from "../src/design-tokens";

describe("shared design tokens", () => {
  it("loads root token file into Remotion helpers", () => {
    expect(colors.primary).toBe(rawTokens.theme.primaryColor);
    expect(fonts.monoFamily).toBe(rawTokens.fonts.mono.family);
    expect(codeTheme.shikiTheme).toBe(rawTokens.code.theme.name);
  });

  it("keeps Remotion and Animotion defaults aligned", () => {
    expect(remotionStyleDefaults.primaryColor).toBe(animotionTheme.accentColor);
    expect(remotionStyleDefaults.font).toBe(animotionTheme.bodyFont);
    expect(remotionStyleDefaults.codeTheme).toBe(animotionTheme.codeTheme);
  });
});
