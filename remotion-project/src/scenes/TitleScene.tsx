import { useCurrentFrame } from "remotion";
import { z } from "zod";

export const TitleSceneSchema = z.object({
  title: z.string(),
  subtitle: z.string().optional(),
  duration: z.number().positive(),
  animation: z.enum(["fadeIn", "slideUp", "typewriter"]).optional().default("fadeIn"),
});

export type TitleSceneProps = z.infer<typeof TitleSceneSchema>;

const ANIMATION_FRAMES = 30;

export const TitleScene: React.FC<TitleSceneProps> = ({
  title,
  subtitle,
  animation = "fadeIn",
}) => {
  const frame = useCurrentFrame();

  const opacity = Math.min(1, frame / ANIMATION_FRAMES);
  const translateY = 20 * (1 - Math.min(1, frame / ANIMATION_FRAMES));
  const charsPerFrame = 1 / 3;
  const visibleText = title.slice(0, Math.floor(frame * charsPerFrame));

  const titleStyle: React.CSSProperties = {
    fontSize: 48,
    fontWeight: "bold",
    color: "#fff",
    textAlign: "center",
    ...(animation === "fadeIn" ? { opacity } : {}),
    ...(animation === "slideUp" ? { opacity, transform: `translateY(${translateY}px)` } : {}),
  };

  const subtitleStyle: React.CSSProperties = {
    fontSize: 24,
    color: "#ccc",
    textAlign: "center",
    marginTop: 16,
    opacity,
  };

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "#1a1a2e",
        width: "100%",
        height: "100%",
      }}
    >
      <div style={titleStyle}>
        {animation === "typewriter" ? visibleText : title}
      </div>
      {subtitle && <div style={subtitleStyle}>{subtitle}</div>}
    </div>
  );
};
