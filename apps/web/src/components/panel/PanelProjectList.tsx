import React from "react";
import Link from "next/link";

import type { PanelProject } from "@/src/lib/panel";

import { StatusBadge } from "./StatusBadge";
import { getHealthTone, getStatusTone } from "./panelPresentation";

type PanelProjectListProps = {
  projects: PanelProject[];
};

export function PanelProjectList({ projects }: PanelProjectListProps) {
  return (
    <section className="panel-card" style={{ marginTop: "18px", padding: "22px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px", gap: "12px", flexWrap: "wrap" }}>
        <h3 style={{ margin: 0, fontSize: "18px" }}>Project Overview</h3>
        <span style={{ color: "var(--muted)", fontSize: "12px" }}>Click any project to open detail</span>
      </div>

      <table className="panel-table">
        <thead>
          <tr>
            <th style={{ width: "28%" }}>Project</th>
            <th style={{ width: "14%", textAlign: "center" }}>Health</th>
            <th style={{ width: "16%", textAlign: "center" }}>Check Status</th>
            <th style={{ width: "10%", textAlign: "center" }}>Modules</th>
            <th style={{ width: "12%", textAlign: "center" }}>Coverage Avg</th>
            <th style={{ width: "20%" }}>Block Reason</th>
          </tr>
        </thead>
        <tbody>
          {projects.length === 0 ? (
            <tr>
              <td colSpan={6} style={{ color: "var(--muted)", padding: "24px", textAlign: "center" }}>
                No data
              </td>
            </tr>
          ) : (
            projects.map((project) => (
              <tr key={project.project_key} style={{ cursor: "pointer" }}>
                <td data-label="Project">
                  <Link href={`/panel/${project.project_key}`} style={{ display: "block" }}>
                    <strong style={{ display: "block", marginBottom: "4px", fontSize: "15px" }}>{project.project_name}</strong>
                    <span style={{ color: "var(--muted)", fontSize: "12px" }}>{project.project_key}</span>
                  </Link>
                </td>
                <td data-label="Health" style={{ textAlign: "center" }}>
                  <StatusBadge label={project.health} tone={getHealthTone(project.health)} />
                </td>
                <td data-label="Test Status" style={{ textAlign: "center" }}>
                  <StatusBadge label={project.status ?? "-"} tone={getStatusTone(project.status)} />
                </td>
                <td data-label="Modules" style={{ textAlign: "center", fontWeight: 700, fontSize: "15px" }}>
                  {project.module_count}
                </td>
                <td data-label="Coverage Avg" style={{ textAlign: "center", fontWeight: 600 }}>
                  {project.coverage_avg_pct === null ? <span style={{ color: "var(--muted)" }}>—</span> : `${project.coverage_avg_pct.toFixed(1)}%`}
                </td>
                <td data-label="Block Reason" style={{ color: "var(--muted)", fontSize: "12px" }}>
                  {project.block_reason ?? "—"}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </section>
  );
}
