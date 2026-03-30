import { PanelProjectDetailView } from "@/src/components/panel/PanelProjectDetailView";
import { getPanelProject } from "@/src/lib/panel";

type PanelProjectDetailPageProps = {
  params: Promise<{
    projectKey: string;
  }>;
};

export default async function PanelProjectDetailPage({ params }: PanelProjectDetailPageProps) {
  const { projectKey } = await params;

  try {
    const data = await getPanelProject(projectKey);

    if (data === null) {
      return (
        <section
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "24px",
            padding: "28px",
            display: "grid",
            gap: "12px",
          }}
        >
          <p style={{ margin: 0, letterSpacing: "0.18em", textTransform: "uppercase", color: "var(--accent)" }}>
            Project Detail
          </p>
          <h1 style={{ margin: 0, fontSize: "clamp(2rem, 5vw, 3.4rem)" }}>Project not found</h1>
          <p style={{ margin: 0, color: "var(--muted)" }}>
            `GET /api/v1/panel/projects/{projectKey}` returned `404`.
          </p>
        </section>
      );
    }

    return <PanelProjectDetailView generatedAt={data.generated_at} project={data.project} />;
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown panel API error";

    return (
      <section
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "24px",
          padding: "28px",
          display: "grid",
          gap: "12px",
        }}
      >
        <p style={{ margin: 0, letterSpacing: "0.18em", textTransform: "uppercase", color: "var(--accent)" }}>
          Project Detail
        </p>
        <h1 style={{ margin: 0, fontSize: "clamp(2rem, 5vw, 3.4rem)" }}>Panel API unavailable</h1>
        <p style={{ margin: 0, color: "var(--muted)" }}>
          The page calls <strong>GET /api/v1/panel/projects/{projectKey}</strong> directly from the server
          component.
        </p>
        <p style={{ margin: 0, color: "var(--muted)" }}>{message}</p>
      </section>
    );
  }
}
