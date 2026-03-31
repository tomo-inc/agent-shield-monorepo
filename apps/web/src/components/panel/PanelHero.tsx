"use client";

import { useRouter } from "next/navigation";

type PanelHeroProps = {
  generatedAt: string;
};

export function PanelHero({ generatedAt }: PanelHeroProps) {
  const router = useRouter();

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
            A cleaner AgentShield dashboard focused on the signals that matter most: project health, test status, coverage average, and a clickable overview that leads directly into project detail.
          </p>
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
