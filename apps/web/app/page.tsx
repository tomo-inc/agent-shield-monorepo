import Link from "next/link";

import { currentFocus, priorities } from "@/src/lib/project";

const governanceFiles = ["AGENTS.md", "CLAUDE.md", "skillscloud.md"];

export default function Home() {
  return (
    <main
      style={{
        display: "grid",
        gap: "24px",
        padding: "48px 24px 64px",
        maxWidth: "960px",
        margin: "0 auto",
      }}
    >
      <section
        style={{
          background: "rgba(255, 253, 250, 0.92)",
          border: "1px solid var(--border)",
          borderRadius: "24px",
          padding: "28px",
          boxShadow: "0 18px 40px rgba(20, 33, 61, 0.08)",
        }}
      >
        <p style={{ letterSpacing: "0.18em", textTransform: "uppercase", color: "var(--accent)" }}>
          AgentShield Phase 1
        </p>
        <h1 style={{ margin: "12px 0", fontSize: "clamp(2.4rem, 6vw, 4.4rem)" }}>
          QA automation first, security work later
        </h1>
        <p style={{ maxWidth: "680px", color: "var(--muted)", fontSize: "1.05rem" }}>
          This repository is scaffolded as an AI-agent-friendly monorepo, with QA automation set as the only top priority for the current phase.
        </p>
      </section>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: "16px",
        }}
      >
        <article
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "20px",
            padding: "20px",
          }}
        >
          <h2>Current Focus</h2>
          <p style={{ color: "var(--muted)" }}>{currentFocus}</p>
        </article>

        <article
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "20px",
            padding: "20px",
          }}
        >
          <h2>Required Governance Files</h2>
          <ul style={{ margin: 0, paddingLeft: "20px", color: "var(--muted)" }}>
            {governanceFiles.map((file) => (
              <li key={file}>{file}</li>
            ))}
          </ul>
        </article>
      </section>

      <section
        style={{
          background: "rgba(20, 33, 61, 0.96)",
          color: "#fff7ef",
          borderRadius: "24px",
          padding: "24px",
        }}
      >
        <h2 style={{ marginTop: 0 }}>Current Phase Priorities</h2>
        <ol style={{ margin: 0, paddingLeft: "20px", display: "grid", gap: "10px" }}>
          {priorities.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ol>
      </section>

      <section
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "20px",
          padding: "20px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "16px",
          flexWrap: "wrap",
        }}
      >
        <div>
          <h2 style={{ margin: "0 0 8px" }}>Panel</h2>
          <p style={{ margin: 0, color: "var(--muted)" }}>
            Open the project overview page backed by the mock panel API.
          </p>
        </div>
        <Link
          href="/panel"
          style={{
            padding: "10px 16px",
            borderRadius: "999px",
            background: "var(--accent)",
            color: "#fff",
            fontWeight: 600,
          }}
        >
          Open panel
        </Link>
      </section>
    </main>
  );
}
