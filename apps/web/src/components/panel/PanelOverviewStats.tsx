import React from "react";
import Link from "next/link";

import type { PanelProject } from "@/src/lib/panel";

type PanelOverviewStatsProps = {
  projects: PanelProject[];
};

function countBy<T>(items: T[], matcher: (item: T) => boolean): number {
  return items.filter(matcher).length;
}

function StatCard({
  title,
  value,
  meta,
  tone,
  href,
}: {
  title: string;
  value: number;
  meta: string;
  tone?: "healthy" | "warning" | "failing";
  href: string;
}) {
  const color =
    tone === "healthy" ? "var(--healthy)" : tone === "warning" ? "var(--warning)" : tone === "failing" ? "var(--failing)" : "var(--text)";

  return (
    <Link href={href} style={{ display: "block" }}>
      <article className="panel-card" style={{ padding: "18px 20px", cursor: "pointer" }}>
        <div style={{ color: "var(--muted)", fontSize: "12px", marginBottom: "10px" }}>{title}</div>
        <div style={{ fontSize: "30px", fontWeight: 800, letterSpacing: "-0.03em", marginBottom: "6px", color }}>{value}</div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", color: "var(--muted)", fontSize: "11px" }}>
          <span>{meta}</span>
        </div>
        <div
          style={{
            marginTop: "12px",
            height: "30px",
            borderRadius: "10px",
            background: "linear-gradient(180deg, rgba(37,99,235,0.12), rgba(37,99,235,0.03))",
            position: "relative",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              position: "absolute",
              inset: "10px",
              borderBottom: "2px solid var(--primary)",
              borderRadius: "20px",
              transform: "skewX(-16deg)",
            }}
          />
        </div>
      </article>
    </Link>
  );
}

export function PanelOverviewStats({ projects }: PanelOverviewStatsProps) {
  const moduleCount = projects.reduce((total, project) => total + project.module_count, 0);
  const healthyCount = countBy(projects, (project) => project.health === "healthy");
  const blockedCount = countBy(projects, (project) => project.health === "warning" || project.status === "blocked");
  const failingCount = countBy(projects, (project) => project.health === "failing");

  return (
    <section
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        gap: "16px",
      }}
    >
      <StatCard title="Total Projects" value={projects.length} meta={`${moduleCount} modules in scope`} href="/panel?status=all" />
      <StatCard title="Pass Projects" value={healthyCount} meta={`${projects.length === 0 ? 0 : Math.round((healthyCount / projects.length) * 100)}% of total`} tone="healthy" href="/panel?status=pass" />
      <StatCard title="Failing Projects" value={failingCount} meta="Tests or checks failing" tone="failing" href="/panel?status=fail" />
      <StatCard title="Blocked Projects" value={blockedCount} meta="Needs attention" tone="warning" href="/panel?status=blocked" />
    </section>
  );
}
