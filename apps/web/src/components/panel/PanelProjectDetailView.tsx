import Link from "next/link";

import type { PanelProjectDetail } from "@/src/lib/panel";

import { StatusBadge } from "./StatusBadge";
import { formatDateTime, formatPercent, getStatusTone } from "./panelPresentation";

type PanelProjectDetailViewProps = {
  generatedAt: string;
  project: PanelProjectDetail;
};

function averageCoverage(project: PanelProjectDetail): number | null {
  const values = project.modules.flatMap((module) => (module.coverage_pct === null ? [] : [module.coverage_pct]));
  if (values.length === 0) {
    return null;
  }
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function averageCoverageDelta(project: PanelProjectDetail): number | null {
  const values = project.modules.flatMap((module) => (module.coverage_delta_pct === null ? [] : [module.coverage_delta_pct]));
  if (values.length === 0) {
    return null;
  }
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function blockedModuleCount(project: PanelProjectDetail): number {
  return project.modules.filter((module) => module.block_reason !== null).length;
}

function statValueColor(tone: ReturnType<typeof getStatusTone>): string {
  if (tone === "pass") return "var(--healthy)";
  if (tone === "blocked") return "var(--warning)";
  if (tone === "fail") return "var(--failing)";
  return "var(--unknown)";
}

function checkerPillStyle(tone: ReturnType<typeof getStatusTone>) {
  if (tone === "pass") {
    return { background: "var(--healthy-soft)", color: "var(--healthy)" };
  }
  if (tone === "blocked") {
    return { background: "var(--warning-soft)", color: "var(--warning)" };
  }
  if (tone === "fail") {
    return { background: "var(--failing-soft)", color: "var(--failing)" };
  }
  return { background: "var(--unknown-soft)", color: "var(--unknown)" };
}

function DetailStatCard({ title, value, note, tone }: { title: string; value: string | number; note: string; tone?: ReturnType<typeof getStatusTone> }) {
  return (
    <article className="panel-card" style={{ padding: "22px" }}>
      <div style={{ color: "var(--muted)", fontSize: "13px", marginBottom: "14px" }}>{title}</div>
      <div style={{ fontSize: "34px", fontWeight: 800, letterSpacing: "-0.03em", color: tone ? statValueColor(tone) : "var(--text)" }}>{value}</div>
      <div style={{ marginTop: "8px", color: "var(--muted)", fontSize: "12px" }}>{note}</div>
    </article>
  );
}

export function PanelProjectDetailView({ generatedAt, project }: PanelProjectDetailViewProps) {
  const statusTone = getStatusTone(project.latest_run.status);
  const coverageAvg = averageCoverage(project);
  const coverageDeltaAvg = averageCoverageDelta(project);
  const blockedCount = blockedModuleCount(project);

  return (
    <>
      <div style={{ margin: "22px 2px 14px", color: "var(--muted)", fontSize: "13px" }}>
        <Link href="/panel">Projects</Link> / {project.project_name}
      </div>

      <section
        className="panel-card"
        style={{
          padding: "28px",
          background: "radial-gradient(circle at top right, rgba(37,99,235,0.12), transparent 26%), white",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", gap: "18px", alignItems: "flex-start", flexWrap: "wrap" }}>
          <div>
            <h2 style={{ margin: 0, fontSize: "40px", letterSpacing: "-0.04em" }}>{project.project_name}</h2>
            <p style={{ margin: "10px 0 0", maxWidth: "760px", color: "var(--muted)", fontSize: "15px", lineHeight: 1.7 }}>
              Dedicated project detail view focused only on the most important layer: module health, coverage movement, checker results, and blocking reasons.
            </p>
            <p style={{ margin: "10px 0 0", color: "var(--muted)", fontSize: "12px" }}>Generated at: {generatedAt}</p>
          </div>
          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
            <span className="btn-primary">Run check</span>
            <span className="btn-ghost">View logs</span>
          </div>
        </div>
      </section>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "16px",
          marginTop: "20px",
        }}
      >
        <DetailStatCard
          title="Latest Run Status"
          value={String(project.latest_run.status).toUpperCase()}
          note={`Finished ${formatDateTime(project.latest_run.finished_at)}`}
          tone={statusTone}
        />
        <DetailStatCard
          title="Coverage Avg"
          value={formatPercent(coverageAvg)}
          note={coverageDeltaAvg === null ? "No baseline delta" : `${coverageDeltaAvg >= 0 ? "+" : ""}${formatPercent(coverageDeltaAvg)} from baseline`}
        />
        <DetailStatCard title="Module Count" value={project.modules.length} note={`${blockedCount} module(s) blocked`} />
        <DetailStatCard title="Blocked Modules" value={blockedCount} note={blockedCount === 0 ? "No blocking reasons reported" : "Modules need attention"} tone={blockedCount > 0 ? "blocked" : "pass"} />
      </section>

      <section className="panel-card" style={{ marginTop: "18px", padding: "22px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px", gap: "12px", flexWrap: "wrap" }}>
          <h3 style={{ margin: 0, fontSize: "18px" }}>Module Health Board</h3>
          <span style={{ color: "var(--muted)", fontSize: "12px" }}>Coverage, gates, and checker results at module level</span>
        </div>

        <table className="panel-table">
          <thead>
            <tr>
              <th style={{ width: "24%" }}>Module</th>
              <th style={{ width: "12%" }}>Status</th>
              <th style={{ width: "12%" }}>Coverage</th>
              <th style={{ width: "12%" }}>Coverage Gate</th>
              <th style={{ width: "20%" }}>Checkers</th>
              <th style={{ width: "20%" }}>Block Reason</th>
            </tr>
          </thead>
          <tbody>
            {project.modules.map((module) => (
              <tr key={module.module_name}>
                <td data-label="Module">
                  <strong style={{ display: "block", marginBottom: "4px" }}>{module.module_name}</strong>
                  <span style={{ color: "var(--muted)", fontSize: "12px" }}>{[module.stack, module.language].filter(Boolean).join(" / ") || "-"}</span>
                </td>
                <td data-label="Status">
                  <StatusBadge label={module.status} tone={getStatusTone(module.status)} />
                </td>
                <td data-label="Coverage" style={{ fontWeight: 700 }}>
                  {formatPercent(module.coverage_pct)}
                </td>
                <td data-label="Coverage Gate" style={{ fontWeight: 700 }}>
                  {formatPercent(module.coverage_gate_pct)}
                </td>
                <td data-label="Checkers">
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                    {module.checker_results.map((checker) => {
                      const tone = getStatusTone(checker.status);
                      const style = checkerPillStyle(tone);
                      return (
                        <span
                          key={`${module.module_name}-${checker.checker}`}
                          style={{
                            padding: "5px 8px",
                            borderRadius: "999px",
                            fontSize: "11px",
                            fontWeight: 700,
                            background: style.background,
                            color: style.color,
                          }}
                        >
                          {checker.checker}
                        </span>
                      );
                    })}
                  </div>
                </td>
                <td data-label="Block Reason" style={{ color: "var(--muted)", fontSize: "12px" }}>
                  {module.block_reason ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
