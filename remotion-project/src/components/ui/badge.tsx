/**
 * shadcn/ui-inspired Badge component.
 *
 * Styled with design tokens.  Supports variant prop for engine vs scene-kind.
 */

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { colors } from "../../design-tokens";

const badgeBase: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  borderRadius: 9999,
  padding: "2px 10px",
  fontSize: 11,
  fontWeight: 500,
  lineHeight: "18px",
  whiteSpace: "nowrap",
  userSelect: "none",
};

const badgeVariants = cva("", {
  variants: {
    variant: {
      /** Engine badges — colored by primary/accent. */
      engine: {
        ...badgeBase,
        backgroundColor: colors.primary + "20",
        color: colors.primary,
        border: `1px solid ${colors.primary}40`,
      } as React.CSSProperties,
      /** Scene kind badges — neutral tint. */
      scene: {
        ...badgeBase,
        backgroundColor: colors.chromePanel,
        color: colors.textMuted,
        border: `1px solid ${colors.chromeBorder}`,
      } as React.CSSProperties,
      /** Success / active state. */
      success: {
        ...badgeBase,
        backgroundColor: colors.success + "20",
        color: colors.success,
      } as React.CSSProperties,
      /** Use case labels — subtle. */
      useCase: {
        ...badgeBase,
        backgroundColor: "transparent",
        color: colors.textSubtle,
        border: `1px solid ${colors.chromeBorder}`,
        padding: "1px 8px",
      } as React.CSSProperties,
    },
  },
  defaultVariants: {
    variant: "scene",
  },
});

export interface BadgeProps
  extends VariantProps<typeof badgeVariants>,
    React.HTMLAttributes<HTMLSpanElement> {
  variant?: "engine" | "scene" | "success" | "useCase";
}

export const Badge: React.FC<BadgeProps> = ({
  variant = "scene",
  children,
  style,
  ...rest
}) => {
  const resolved = badgeVariants({ variant });
  const baseStyle = typeof resolved === "string" ? badgeBase : resolved;
  return (
    <span style={{ ...baseStyle, ...style } as React.CSSProperties} {...rest}>
      {children}
    </span>
  );
};
