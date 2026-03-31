import React from "react";

type StatusBadgeProps = {
  label: string;
  tone: "ready" | "pending" | "pass" | "fail" | "blocked" | "neutral";
};

const toneStyles: Record<StatusBadgeProps["tone"], { background: string; color: string; borderColor: string }> = {
  ready: {
    background: "var(--healthy-soft)",
    color: "var(--healthy)",
    borderColor: "rgba(22, 163, 74, 0.3)",
  },
  pending: {
    background: "var(--warning-soft)",
    color: "var(--warning)",
    borderColor: "rgba(217, 119, 6, 0.35)",
  },
  pass: {
    background: "var(--healthy-soft)",
    color: "var(--healthy)",
    borderColor: "rgba(22, 163, 74, 0.3)",
  },
  fail: {
    background: "var(--failing-soft)",
    color: "var(--failing)",
    borderColor: "rgba(220, 38, 38, 0.34)",
  },
  blocked: {
    background: "var(--warning-soft)",
    color: "var(--warning)",
    borderColor: "rgba(217, 119, 6, 0.3)",
  },
  neutral: {
    background: "var(--unknown-soft)",
    color: "var(--unknown)",
    borderColor: "rgba(100, 116, 139, 0.3)",
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
