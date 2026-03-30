import Link from "next/link";

type PanelHeroProps = {
  generatedAt: string;
};

export function PanelHero({ generatedAt }: PanelHeroProps) {
  return (
    <section
      style={{
        background:
          "linear-gradient(135deg, rgba(20, 33, 61, 0.96) 0%, rgba(34, 56, 92, 0.96) 52%, rgba(231, 111, 81, 0.92) 100%)",
        border: "1px solid rgba(20, 33, 61, 0.12)",
        borderRadius: "16px",
        padding: "20px 24px",
        boxShadow: "0 8px 20px rgba(20, 33, 61, 0.18)",
        display: "grid",
        gap: "10px",
        color: "#fff7ef",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", flexWrap: "wrap" }}>
        <div>
          <p
            style={{
              margin: 0,
              letterSpacing: "0.24em",
              textTransform: "uppercase",
              color: "rgba(255, 247, 239, 0.72)",
              fontSize: "0.78rem",
            }}
          >
            All Projects
          </p>
          <h1 style={{ margin: "8px 0 6px", fontSize: "clamp(1.6rem, 4vw, 2.6rem)", lineHeight: 1 }}>
            Project Health Board
          </h1>
          <p style={{ margin: 0, color: "rgba(255, 247, 239, 0.82)", maxWidth: "720px", fontSize: "1.02rem" }}>
            Focus on each project&apos;s onboarding progress, module scope, health, status, and blocking reason from
            <strong> GET /api/v1/panel/projects</strong>.
          </p>
        </div>
        <div style={{ display: "grid", gap: "8px", alignContent: "start", justifyItems: "end" }}>
          <Link href="/" style={{ color: "#fff7ef", fontWeight: 700 }}>
            Back to home
          </Link>
          <span style={{ color: "rgba(255, 247, 239, 0.78)", fontSize: "0.95rem" }}>Generated at: {generatedAt}</span>
        </div>
      </div>
    </section>
  );
}
