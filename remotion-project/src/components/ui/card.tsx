/**
 * shadcn/ui-inspired Card component.
 *
 * Uses project design tokens instead of Tailwind so it integrates with
 * the existing Remotion theming.  Drop-in replacement when migrating to
 * full Tailwind + shadcn/ui in the TanStack Start app.
 */

import React from "react";
import { colors } from "../../design-tokens";

const cardBase: React.CSSProperties = {
  borderRadius: 12,
  border: `1px solid ${colors.chromeBorder}`,
  background: colors.backgroundElevated,
  overflow: "hidden",
  boxShadow: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)",
};

const cardInteractive: React.CSSProperties = {
  ...cardBase,
  cursor: "pointer",
  transition: "box-shadow 0.2s, transform 0.2s",
};

export const Card: React.FC<{
  children: React.ReactNode;
  interactive?: boolean;
  onClick?: () => void;
  style?: React.CSSProperties;
  className?: string;
}> = ({ children, interactive, onClick, style, className }) => (
  <div
    style={{ ...(interactive ? cardInteractive : cardBase), ...style }}
    onClick={onClick}
    onKeyDown={onClick ? (e) => { if (e.key === "Enter" || e.key === " ") onClick(); } : undefined}
    role={onClick ? "button" : undefined}
    tabIndex={onClick ? 0 : undefined}
    className={className}
  >
    {children}
  </div>
);

const cardHeaderBase: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 4,
  padding: "16px 20px 0",
};

export const CardHeader: React.FC<{
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ children, style }) => <div style={{ ...cardHeaderBase, ...style }}>{children}</div>;

const cardTitleBase: React.CSSProperties = {
  fontSize: 16,
  fontWeight: 600,
  lineHeight: "24px",
  letterSpacing: "-0.01em",
  color: colors.text,
};

export const CardTitle: React.FC<{
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ children, style }) => <div style={{ ...cardTitleBase, ...style }}>{children}</div>;

const cardDescBase: React.CSSProperties = {
  fontSize: 13,
  lineHeight: "20px",
  color: colors.textMuted,
};

export const CardDescription: React.FC<{
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ children, style }) => <div style={{ ...cardDescBase, ...style }}>{children}</div>;

const cardContentBase: React.CSSProperties = {
  padding: "12px 20px 16px",
};

export const CardContent: React.FC<{
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ children, style }) => <div style={{ ...cardContentBase, ...style }}>{children}</div>;

const cardFooterBase: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "flex-end",
  gap: 8,
  padding: "0 20px 16px",
};

export const CardFooter: React.FC<{
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ children, style }) => <div style={{ ...cardFooterBase, ...style }}>{children}</div>;
