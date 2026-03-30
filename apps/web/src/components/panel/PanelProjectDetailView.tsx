import type { PanelProjectDetail } from "@/src/lib/panel";

import { StatusBadge } from "./StatusBadge";
import {
  formatDateTime,
  formatDuration,
  formatPercent,
  getOnboardingTone,
  getStatusTone,
} from "./panelPresentation";

type PanelProjectDetailViewProps = {
  generatedAt: string;
  project: PanelProjectDetail;
};

const labelStyle = {
  margin: 0,
  fontSize: "0.78rem",
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  color: "var(--muted)",
} as const;

const cardStyle = {
  background: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: "10px",
  padding: "14px",
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

export function PanelProjectDetailView({ generatedAt, project }: PanelProjectDetailViewProps) {
  return (
    <>
      <section
        style={{
          background: "rgba(255, 253, 250, 0.92)",
          border: "1px solid var(--border)",
          borderRadius: "14px",
          padding: "18px 20px",
          boxShadow: "0 4px 12px rgba(20, 33, 61, 0.08)",
          display: "grid",
          gap: "10px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", flexWrap: "wrap" }}>
          <div style={{ display: "grid", gap: "8px" }}>
            <p style={{ margin: 0, letterSpacing: "0.18em", textTransform: "uppercase", color: "var(--accent)" }}>
              Project Detail
            </p>
            <h1 style={{ margin: 0, fontSize: "clamp(1.4rem, 3.5vw, 2.2rem)" }}>{project.project_name}</h1>
            <span style={{ color: "var(--muted)" }}>{project.project_key}</span>
          </div>
          <div style={{ display: "grid", gap: "8px", alignContent: "start", justifyItems: "end" }}>
            <span style={{ color: "var(--muted)", fontSize: "0.95rem" }}>Generated at: {generatedAt}</span>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", justifyContent: "flex-end" }}>
              <StatusBadge
                label={project.onboarding_status}
                tone={getOnboardingTone(project.onboarding_status)}
              />
              <StatusBadge label={project.latest_run.status} tone={getStatusTone(project.latest_run.status)} />
            </div>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gap: "10px",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          }}
        >
          <div>
            <p style={labelStyle}>Repo Path</p>
            <span>{project.repo_path}</span>
          </div>
          <div>
            <p style={labelStyle}>Preset</p>
            <span>{project.preset}</span>
          </div>
          <div>
            <p style={labelStyle}>Modules</p>
            <span>{project.modules.length}</span>
          </div>
          <div>
            <p style={labelStyle}>Run Key</p>
            <span>{project.latest_run.run_key}</span>
          </div>
        </div>
      </section>

      <section style={{ display: "grid", gap: "10px" }}>
        <div>
          <p style={{ margin: 0, letterSpacing: "0.16em", textTransform: "uppercase", color: "var(--accent)" }}>
            Modules
          </p>
          <h2 style={{ margin: "6px 0 2px", fontSize: "1.2rem" }}>Module execution board</h2>
          <p style={{ margin: 0, color: "var(--muted)" }}>
            Coverage and checker execution are shown first so you can scan all module results without excessive scrolling.
          </p>
        </div>

        {project.modules.map((module) => (
          (() => {
            const statusTone = getStatusTone(module.status);
            const coverageTone =
              module.coverage_delta_pct !== null && module.coverage_delta_pct < 0 ? "fail" : statusTone;
            const coveragePanel = getSignalPanelStyle(coverageTone);

            return (
              <article
                key={module.module_name}
                style={{
                  background: "var(--surface)",
                  border: "1px solid var(--border)",
                  borderRadius: "12px",
                  padding: "14px",
                  display: "grid",
                  gap: "10px",
                  boxShadow: "0 4px 12px rgba(20, 33, 61, 0.05)",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", flexWrap: "wrap" }}>
                  <div style={{ display: "grid", gap: "6px" }}>
                    <strong style={{ fontSize: "1rem" }}>{module.module_name}</strong>
                    <span style={{ color: "var(--muted)" }}>
                      {[module.stack, module.language].filter(Boolean).join(" / ") || "-"}
                    </span>
                  </div>
                  <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                    <StatusBadge label={module.status} tone={statusTone} />
                    <StatusBadge
                      label={module.block_reason ? "blocked" : "clear"}
                      tone={module.block_reason ? "blocked" : "ready"}
                    />
                  </div>
                </div>

                <div
                  style={{
                    display: "grid",
                    gap: "10px",
                    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                    alignItems: "start",
                  }}
                >
                  <section
                    style={{
                      borderRadius: "10px",
                      padding: "12px",
                      background: coveragePanel.background,
                      border: coveragePanel.border,
                      display: "grid",
                      gap: "6px",
                    }}
                  >
                    <p style={labelStyle}>Coverage</p>
                    <strong style={{ fontSize: "1.4rem", color: coveragePanel.accent }}>
                      {formatPercent(module.coverage_pct)}
                    </strong>
                    <div
                      style={{
                        display: "grid",
                        gap: "6px",
                        gridTemplateColumns: "repeat(auto-fit, minmax(88px, 1fr))",
                      }}
                    >
                      <div>
                        <p style={labelStyle}>Baseline</p>
                        <span>{formatPercent(module.baseline_pct)}</span>
                      </div>
                      <div>
                        <p style={labelStyle}>Gate</p>
                        <span>{formatPercent(module.coverage_gate_pct)}</span>
                      </div>
                      <div>
                        <p style={labelStyle}>Delta</p>
                        <span>{formatPercent(module.coverage_delta_pct)}</span>
                      </div>
                    </div>
                    <span style={{ color: "var(--muted)" }}>{module.coverage_parser ?? "-"}</span>
                  </section>

                  <section style={{ display: "grid", gap: "10px" }}>
                    <div style={{ display: "grid", gap: "6px" }}>
                      {module.checker_results.map((checker) => (
                        <div
                          key={`${module.module_name}-${checker.checker}`}
                          style={{
                            border: "1px solid var(--border)",
                            borderRadius: "8px",
                            padding: "8px 12px",
                            display: "grid",
                            gap: "6px",
                          }}
                        >
                          <div
                            style={{
                              display: "grid",
                              gap: "10px",
                              gridTemplateColumns: "minmax(88px, 120px) minmax(92px, 110px) minmax(64px, 84px) minmax(0, 1fr)",
                              alignItems: "center",
                            }}
                          >
                            <strong style={{ textTransform: "capitalize", fontSize: "0.96rem" }}>
                              {checker.checker}
                            </strong>
                            <StatusBadge label={checker.status} tone={getStatusTone(checker.status)} />
                            <span style={{ color: "var(--muted)", fontSize: "0.82rem", fontWeight: 600 }}>
                              {formatDuration(checker.duration_sec)}
                            </span>
                            <span
                              style={{
                                color: "var(--muted)",
                                fontSize: "0.86rem",
                                lineHeight: 1.35,
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                whiteSpace: "nowrap",
                              }}
                            >
                              {checker.detail || "-"}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div
                      style={{
                        display: "grid",
                        gap: "10px",
                        gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
                      }}
                    >
                      <div>
                        <p style={labelStyle}>Block Reason</p>
                        <span>{module.block_reason ?? "-"}</span>
                      </div>
                    </div>
                  </section>
                </div>
              </article>
            );
          })()
        ))}
      </section>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "16px",
        }}
      >
        <article style={cardStyle}>
          <p style={labelStyle}>Latest Run</p>
          <div style={{ display: "grid", gap: "10px", marginTop: "8px" }}>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <StatusBadge label={project.latest_run.status} tone={getStatusTone(project.latest_run.status)} />
              <StatusBadge label={project.latest_run.strict_mode ? "strict" : "non-strict"} tone="neutral" />
            </div>
            <span style={{ color: "var(--muted)" }}>{project.latest_run.block_reason ?? "No block reason"}</span>
          </div>
        </article>

        <article style={cardStyle}>
          <p style={labelStyle}>Source</p>
          <div style={{ display: "grid", gap: "6px", marginTop: "8px" }}>
            <span>{project.latest_run.source ?? "-"}</span>
            <span style={{ color: "var(--muted)" }}>Triggered by {project.latest_run.triggered_by ?? "-"}</span>
          </div>
        </article>

        <article style={cardStyle}>
          <p style={labelStyle}>Git</p>
          <div style={{ display: "grid", gap: "6px", marginTop: "8px" }}>
            <span>{project.latest_run.git_ref ?? "-"}</span>
            <span style={{ color: "var(--muted)" }}>{project.latest_run.git_sha ?? "-"}</span>
          </div>
        </article>

        <article style={cardStyle}>
          <p style={labelStyle}>Timing</p>
          <div style={{ display: "grid", gap: "6px", marginTop: "8px" }}>
            <span>Started {formatDateTime(project.latest_run.started_at)}</span>
            <span>Finished {formatDateTime(project.latest_run.finished_at)}</span>
            <span style={{ color: "var(--muted)" }}>Duration {formatDuration(project.latest_run.duration_sec)}</span>
          </div>
        </article>
      </section>
    </>
  );
}
