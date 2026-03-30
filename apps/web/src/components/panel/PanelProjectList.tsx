import type { PanelProject } from "@/src/lib/panel";

import { PanelProjectCard } from "./PanelProjectCard";

type PanelProjectListProps = {
  projects: PanelProject[];
};

export function PanelProjectList({ projects }: PanelProjectListProps) {
  if (projects.length === 0) {
    return (
      <section
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "20px",
          padding: "24px",
          color: "var(--muted)",
        }}
      >
        No panel projects returned by `GET /api/v1/panel/projects`.
      </section>
    );
  }

  return (
    <section style={{ display: "grid", gap: "10px" }}>
      {projects.map((project) => (
        <PanelProjectCard key={project.project_key} project={project} />
      ))}
    </section>
  );
}
