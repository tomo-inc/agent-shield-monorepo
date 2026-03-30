import type { PanelProject } from "@/src/lib/panel";

import { StatusBadge } from "./StatusBadge";

type PanelOverviewStatsProps = {
  projects: PanelProject[];
};

function countBy<T>(items: T[], matcher: (item: T) => boolean): number {
  return items.filter(matcher).length;
}

export function PanelOverviewStats({ projects }: PanelOverviewStatsProps) {
  const moduleCount = projects.reduce((total, project) => total + project.module_count, 0);
  const readyCount = countBy(projects, (project) => project.onboarding_status === "ready");
  const pendingCount = countBy(projects, (project) => project.onboarding_status === "pending");
  const blockedCount = countBy(projects, (project) => project.onboarding_status === "blocked");
  const customNeededCount = countBy(projects, (project) => project.onboarding_status === "custom-needed");
  const healthyCount = countBy(projects, (project) => project.health === "healthy");
  const warningCount = countBy(projects, (project) => project.health === "warning");
  const failingCount = countBy(projects, (project) => project.health === "failing");
  const unknownCount = countBy(projects, (project) => project.health === "unknown");

  const statCardStyle = {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: "12px",
    padding: "14px 16px",
    display: "grid",
    gap: "6px",
  } as const;

  return (
    <section
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        gap: "10px",
      }}
    >
      <article style={statCardStyle}>
        <p style={{ margin: 0, color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
          Total Projects
        </p>
        <strong style={{ fontSize: "1.4rem" }}>{projects.length}</strong>
        <span style={{ color: "var(--muted)" }}>{moduleCount} modules in scope</span>
      </article>
      <article style={statCardStyle}>
        <p style={{ margin: 0, color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
          Onboarding
        </p>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          <StatusBadge label={`ready ${readyCount}`} tone="ready" />
          <StatusBadge label={`pending ${pendingCount}`} tone="pending" />
          <StatusBadge label={`blocked ${blockedCount}`} tone="blocked" />
          <StatusBadge label={`custom ${customNeededCount}`} tone="neutral" />
        </div>
      </article>
      <article style={statCardStyle}>
        <p style={{ margin: 0, color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
          Health
        </p>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          <StatusBadge label={`healthy ${healthyCount}`} tone="pass" />
          <StatusBadge label={`warning ${warningCount}`} tone="blocked" />
          <StatusBadge label={`failing ${failingCount}`} tone="fail" />
          <StatusBadge label={`unknown ${unknownCount}`} tone="neutral" />
        </div>
      </article>
    </section>
  );
}
