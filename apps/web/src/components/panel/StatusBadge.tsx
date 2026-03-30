type StatusBadgeProps = {
  label: string;
  tone: "ready" | "pending" | "pass" | "fail" | "blocked" | "neutral";
};

const toneStyles: Record<StatusBadgeProps["tone"], { background: string; color: string; borderColor: string }> = {
  ready: {
    background: "rgba(42, 157, 143, 0.14)",
    color: "#1f6f66",
    borderColor: "rgba(42, 157, 143, 0.3)",
  },
  pending: {
    background: "rgba(233, 196, 106, 0.18)",
    color: "#8d6708",
    borderColor: "rgba(233, 196, 106, 0.35)",
  },
  pass: {
    background: "rgba(42, 157, 143, 0.14)",
    color: "#1f6f66",
    borderColor: "rgba(42, 157, 143, 0.3)",
  },
  fail: {
    background: "rgba(231, 111, 81, 0.16)",
    color: "#a33d22",
    borderColor: "rgba(231, 111, 81, 0.34)",
  },
  blocked: {
    background: "rgba(20, 33, 61, 0.12)",
    color: "#14213d",
    borderColor: "rgba(20, 33, 61, 0.24)",
  },
  neutral: {
    background: "rgba(92, 103, 125, 0.12)",
    color: "#5c677d",
    borderColor: "rgba(92, 103, 125, 0.24)",
  },
};

export function StatusBadge({ label, tone }: StatusBadgeProps) {
  const style = toneStyles[tone];

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "28px",
        padding: "4px 10px",
        borderRadius: "999px",
        border: `1px solid ${style.borderColor}`,
        background: style.background,
        color: style.color,
        fontSize: "0.85rem",
        fontWeight: 600,
        textTransform: "capitalize",
      }}
    >
      {label}
    </span>
  );
}
