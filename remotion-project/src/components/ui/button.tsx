/**
 * shadcn/ui-inspired Button component.
 */

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { colors, spacing } from "../../design-tokens";

const buttonVariants = cva("", {
  variants: {
    variant: {
      default: {
        backgroundColor: colors.primary,
        color: "#fff",
        border: "none",
      } as React.CSSProperties,
      secondary: {
        backgroundColor: colors.chromePanel,
        color: colors.text,
        border: `1px solid ${colors.chromeBorder}`,
      } as React.CSSProperties,
      ghost: {
        backgroundColor: "transparent",
        color: colors.textMuted,
        border: "none",
      } as React.CSSProperties,
      outline: {
        backgroundColor: "transparent",
        color: colors.primary,
        border: `1px solid ${colors.primary}60`,
      } as React.CSSProperties,
    },
    size: {
      sm: { padding: "4px 12px", fontSize: 12, height: 28 },
      default: { padding: "8px 16px", fontSize: 13, height: 36 },
      lg: { padding: "10px 24px", fontSize: 14, height: 44 },
      icon: { padding: "8px", height: 36, width: 36 },
    },
  },
  defaultVariants: {
    variant: "default",
    size: "default",
  },
});

export interface ButtonProps
  extends VariantProps<typeof buttonVariants>,
    React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "secondary" | "ghost" | "outline";
  size?: "sm" | "default" | "lg" | "icon";
}

const btnBase: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  borderRadius: 8,
  fontWeight: 500,
  cursor: "pointer",
  transition: "opacity 0.15s, background 0.15s",
  gap: spacing.xs,
  fontFamily: "inherit",
  whiteSpace: "nowrap",
};

export const Button: React.FC<ButtonProps> = ({
  variant = "default",
  size = "default",
  children,
  style,
  ...rest
}) => {
  const v = buttonVariants({ variant, size });
  return (
    <button
      style={{ ...btnBase, ...v } as React.CSSProperties}
      {...rest}
    >
      {children}
    </button>
  );
};
