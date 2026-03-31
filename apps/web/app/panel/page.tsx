import { PanelHero } from "@/src/components/panel/PanelHero";
import { PanelOverviewStats } from "@/src/components/panel/PanelOverviewStats";
import { PanelProjectList } from "@/src/components/panel/PanelProjectList";
import type { PanelProject } from "@/src/lib/panel";
import { getPanelProjects } from "@/src/lib/panel";

type PanelPageProps = {
  searchParams?: Promise<{ status?: string }>;
};

function filterProjectsByStatus(projects: PanelProject[], status: string | undefined): PanelProject[] {
  if (status === "pass") {
    return projects.filter((project) => project.status === "pass");
  }
  if (status === "fail") {
    return projects.filter((project) => project.status === "fail");
  }
  if (status === "blocked") {
    return projects.filter((project) => project.status === "blocked");
  }
  return projects;
}

export default async function PanelPage({ searchParams }: PanelPageProps) {
  try {
    const data = await getPanelProjects();
    const resolvedSearchParams = await searchParams;
    const filteredProjects = filterProjectsByStatus(data.projects, resolvedSearchParams?.status);

    return (
      <>
        <PanelHero generatedAt={data.generated_at} />
        <PanelOverviewStats projects={data.projects} />
        <PanelProjectList projects={filteredProjects} />
      </>
    );
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
          Panel Overview
        </p>
        <h1 style={{ margin: 0, fontSize: "clamp(2rem, 5vw, 3.4rem)" }}>Panel API unavailable</h1>
        <p style={{ margin: 0, color: "var(--muted)" }}>
          The page calls <strong>GET /api/v1/panel/projects</strong> directly from the server component.
        </p>
        <p style={{ margin: 0, color: "var(--muted)" }}>{message}</p>
      </section>
    );
  }
}
