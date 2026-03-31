"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";

const GATE_STEPS = [
  { key: "build", label: "build", desc: "Verifies the project builds successfully (e.g. pnpm run build, cargo build)." },
  { key: "lint", label: "lint", desc: "Module-level static analysis (e.g. Biome, pnpm lint, Clippy—see config)." },
  { key: "typecheck", label: "typecheck", desc: "Module-level type checking (TypeScript or cargo check, etc.)." },
  { key: "test", label: "test", desc: "Module unit tests." },
  { key: "coverage", label: "coverage", desc: "Runs tests and collects line_coverage (e.g. Vitest; Rust only if configured)." },
];

type PanelHeroProps = {
  generatedAt: string;
};

export function PanelHero({ generatedAt }: PanelHeroProps) {
  const router = useRouter();
  const [open, setOpen] = useState(false);

  return (
    <section
      className="panel-card"
      style={{
        padding: "32px",
        background: "radial-gradient(circle at top right, rgba(37,99,235,0.12), transparent 26%), white",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: "18px", alignItems: "flex-start", flexWrap: "wrap" }}>
        <div style={{ flex: 1 }}>
          <h2
            style={{
              margin: 0,
              fontSize: "clamp(26px, 3vw, 40px)",
              lineHeight: 1.02,
              letterSpacing: "-0.04em",
              maxWidth: "860px",
            }}
          >
            See project risk and test health at a glance.
          </h2>
          <p style={{ margin: "16px 0 0", maxWidth: "760px", color: "var(--muted)", fontSize: "15px", lineHeight: 1.7 }}>
            AgentShield runs a full quality gate against your codebase—build, static checks, tests, and coverage—then rolls up the results and syncs them to the Panel, so everyone can see pass/fail status and where things are blocked.{" "}
            <button
              type="button"
              onClick={() => setOpen((v) => !v)}
              aria-label="What does the quality gate check?"
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                verticalAlign: "middle",
                marginBottom: "2px",
                width: "18px",
                height: "18px",
                borderRadius: "50%",
                border: open ? "1.5px solid var(--primary)" : "1.5px solid var(--border)",
                background: open ? "var(--primary-soft)" : "#f9fbff",
                color: open ? "var(--primary)" : "var(--muted)",
                cursor: "pointer",
                fontSize: "11px",
                fontWeight: 700,
                lineHeight: 1,
                transition: "all 0.15s",
              }}
            >
              i
            </button>
          </p>

          {open && (
            <div
              style={{
                marginTop: "14px",
                maxWidth: "620px",
                background: "var(--surface-soft)",
                border: "1px solid var(--border)",
                borderRadius: "16px",
                padding: "18px 20px",
                display: "grid",
                gap: "12px",
              }}
            >
              <p style={{ margin: 0, fontSize: "11px", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--muted)" }}>
                Quality gate checks
              </p>
              {GATE_STEPS.map((step) => (
                <div key={step.key} style={{ display: "flex", gap: "12px", alignItems: "baseline" }}>
                  <span
                    style={{
                      flexShrink: 0,
                      fontSize: "11px",
                      fontWeight: 700,
                      fontFamily: "ui-monospace, monospace",
                      color: "var(--primary)",
                      background: "var(--primary-soft)",
                      borderRadius: "6px",
                      padding: "2px 8px",
                      letterSpacing: "0.04em",
                      minWidth: "76px",
                      textAlign: "center",
                    }}
                  >
                    {step.label}
                  </span>
                  <span style={{ fontSize: "13px", color: "var(--muted)", lineHeight: 1.6 }}>{step.desc}</span>
                </div>
              ))}
            </div>
          )}

          <p style={{ margin: "10px 0 0", color: "var(--muted)", fontSize: "12px" }}>Generated at: {generatedAt}</p>
        </div>
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
          <button type="button" className="btn-primary" onClick={() => router.refresh()}>
            Refresh
          </button>
          <span className="btn-ghost">View Latest Run</span>
        </div>
      </div>
    </section>
  );
}
