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
          QA 自动化先行，安全能力后置
        </h1>
        <p style={{ maxWidth: "680px", color: "var(--muted)", fontSize: "1.05rem" }}>
          当前仓库按 AI Agent 友好型开发指南落成 monorepo，并把 QA 自动化能力作为唯一第一优先级。
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
          <h2>当前焦点</h2>
          <p style={{ color: "var(--muted)" }}>{currentFocus()}</p>
        </article>

        <article
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "20px",
            padding: "20px",
          }}
        >
          <h2>必备治理文件</h2>
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
        <h2 style={{ marginTop: 0 }}>本阶段优先级</h2>
        <ol style={{ margin: 0, paddingLeft: "20px", display: "grid", gap: "10px" }}>
          {priorities.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ol>
      </section>
    </main>
  );
}
