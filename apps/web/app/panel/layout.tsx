import type { ReactNode } from "react";

function PanelTopbar() {
  return (
    <header
      className="panel-topbar"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "16px",
        background: "rgba(255,255,255,0.86)",
        backdropFilter: "blur(12px)",
        border: "1px solid rgba(229,231,235,0.9)",
        boxShadow: "var(--shadow)",
        borderRadius: "22px",
        padding: "16px 20px",
        position: "sticky",
        top: "16px",
        zIndex: 10,
        flexWrap: "wrap",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "14px", minWidth: "240px" }}>
        <div
          style={{
            width: "40px",
            height: "40px",
            borderRadius: "12px",
            background: "linear-gradient(135deg, #2563eb, #7c3aed)",
            display: "grid",
            placeItems: "center",
            color: "white",
            fontWeight: 800,
            letterSpacing: "0.04em",
          }}
        >
          AS
        </div>
        <div>
          <h1 style={{ margin: 0, fontSize: 18 }}>AgentShield Panel</h1>
          <p style={{ margin: "4px 0 0", fontSize: 12, color: "var(--muted)" }}>Project risk, health, and latest test signals</p>
        </div>
      </div>

      <div
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          background: "var(--surface-soft)",
          border: "1px solid var(--border)",
          borderRadius: "14px",
          padding: "12px 14px",
          color: "var(--muted)",
          minWidth: "240px",
        }}
      >
        Search projects, modules, or run keys…
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
        <span className="btn-ghost" style={{ gap: "6px" }}>
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" style={{ flexShrink: 0 }}>
            <circle cx="6.5" cy="6.5" r="4.5" stroke="currentColor" strokeWidth="1.6" />
            <path d="M10.5 10.5L14 14" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
          </svg>
          Search
        </span>
      </div>
    </header>
  );
}

export default function PanelLayout(props: { children?: ReactNode }) {
  const { children } = props;
  return (
    <div className="panel-shell" style={{ maxWidth: "1440px", margin: "0 auto", padding: "24px" }}>
      <PanelTopbar />
      <main
        style={{
          display: "grid",
          gap: "18px",
          paddingTop: "24px",
        }}
      >
        {children}
      </main>
    </div>
  );
}
