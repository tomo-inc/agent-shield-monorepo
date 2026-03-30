import Link from "next/link";

import type { PanelProject } from "@/src/lib/panel";

import { StatusBadge } from "./StatusBadge";
import { getHealthTone, getOnboardingTone, getStatusTone } from "./panelPresentation";

type PanelProjectCardProps = {
  project: PanelProject;
};

const labelStyle = {
  margin: 0,
  fontSize: "0.78rem",
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  color: "var(--muted)",
} as const;

function getSignalPanelStyle(tone: "ready" | "pending" | "pass" | "fail" | "blocked" | "neutral") {
  if (tone === "pass" || tone === "ready") {
    return {
      background: "linear-gradient(135deg, rgba(42, 157, 143, 0.16), rgba(42, 157, 143, 0.24))",
      border: "1px solid rgba(42, 157, 143, 0.28)",
      accent: "#1f6f66",
    } as const;
  }

  if (tone === "pending") {
    return {
      background: "linear-gradient(135deg, rgba(233, 196, 106, 0.18), rgba(233, 196, 106, 0.28))",
      border: "1px solid rgba(233, 196, 106, 0.3)",
      accent: "#8d6708",
    } as const;
  }

  if (tone === "fail") {
    return {
      background: "linear-gradient(135deg, rgba(231, 111, 81, 0.18), rgba(231, 111, 81, 0.28))",
      border: "1px solid rgba(231, 111, 81, 0.32)",
      accent: "#a33d22",
    } as const;
  }

  if (tone === "blocked") {
    return {
      background: "linear-gradient(135deg, rgba(20, 33, 61, 0.1), rgba(20, 33, 61, 0.18))",
      border: "1px solid rgba(20, 33, 61, 0.22)",
      accent: "#14213d",
    } as const;
  }

  return {
    background: "linear-gradient(135deg, rgba(92, 103, 125, 0.12), rgba(92, 103, 125, 0.18))",
    border: "1px solid rgba(92, 103, 125, 0.22)",
    accent: "#5c677d",
  } as const;
}

export function PanelProjectCard({ project }: PanelProjectCardProps) {
  const onboardingTone = getOnboardingTone(project.onboarding_status);
  const healthTone = getHealthTone(project.health);
  const statusTone = getStatusTone(project.status);
  const healthPanel = getSignalPanelStyle(healthTone);
  const statusPanel = getSignalPanelStyle(statusTone);

  return (
    <article
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "14px",
        padding: "16px",
        display: "grid",
        gap: "12px",
        boxShadow: "0 4px 12px rgba(20, 33, 61, 0.05)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", flexWrap: "wrap" }}>
        <div style={{ display: "grid", gap: "6px" }}>
          <strong style={{ fontSize: "1.1rem", lineHeight: 1.1 }}>{project.project_name}</strong>
          <span style={{ color: "var(--muted)", fontSize: "0.88rem" }}>{project.project_key}</span>
        </div>
        <Link
          href={`/panel/${project.project_key}`}
          style={{
            color: "var(--accent)",
            fontWeight: 700,
            alignSelf: "start",
            padding: "6px 12px",
            borderRadius: "999px",
            border: "1px solid rgba(231, 111, 81, 0.24)",
            background: "rgba(231, 111, 81, 0.08)",
          }}
        >
          View detail
        </Link>
      </div>

      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
        <StatusBadge label={project.onboarding_status} tone={onboardingTone} />
        <StatusBadge label={project.health} tone={healthTone} />
        <StatusBadge label={project.status ?? "-"} tone={statusTone} />
      </div>

      <div
        style={{
          display: "grid",
          gap: "10px",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        }}
      >
        <section
          style={{
            borderRadius: "10px",
            padding: "12px",
            background: healthPanel.background,
            border: healthPanel.border,
            display: "grid",
            gap: "6px",
          }}
        >
          <p style={labelStyle}>Health</p>
          <strong style={{ fontSize: "1.1rem", color: healthPanel.accent, textTransform: "capitalize" }}>
            {project.health}
          </strong>
          <span style={{ color: "var(--muted)" }}>Overall project health signal</span>
        </section>

        <section
          style={{
            borderRadius: "10px",
            padding: "12px",
            background: statusPanel.background,
            border: statusPanel.border,
            display: "grid",
            gap: "6px",
          }}
        >
          <p style={labelStyle}>Status</p>
          <strong style={{ fontSize: "1.1rem", color: statusPanel.accent, textTransform: "capitalize" }}>
            {project.status ?? "-"}
          </strong>
          <span style={{ color: "var(--muted)" }}>Latest run execution status</span>
        </section>
      </div>

      <div
        style={{
          display: "grid",
          gap: "10px",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
        }}
      >
        <div>
          <p style={labelStyle}>Onboarding Status</p>
          <span>{project.onboarding_status}</span>
        </div>
        <div>
          <p style={labelStyle}>Module Count</p>
          <strong style={{ fontSize: "1.2rem" }}>{project.module_count}</strong>
        </div>
      </div>

      <div
        style={{
          borderTop: "1px solid var(--border)",
          paddingTop: "10px",
          display: "grid",
          gap: "8px",
          borderLeft: project.block_reason ? "4px solid var(--accent)" : "4px solid transparent",
          paddingLeft: "14px",
        }}
      >
        <p style={labelStyle}>Block Reason</p>
        <span style={{ color: project.block_reason ? "var(--ink)" : "var(--muted)", fontWeight: 500 }}>
          {project.block_reason ?? "-"}
        </span>
      </div>
    </article>
  );
}
