import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { refreshMock } from "@/src/__mocks__/next/navigation";

import { PanelHero } from "./PanelHero";

describe("PanelHero", () => {
  it("toggles quality gate details and refreshes", () => {
    refreshMock.mockReset();

    render(<PanelHero generatedAt="2026-03-31T06:20:22Z" />);

    expect(screen.queryByText("Quality gate checks")).toBeNull();

    fireEvent.click(screen.getByLabelText("What does the quality gate check?"));
    expect(screen.getByText("Quality gate checks")).toBeTruthy();
    expect(screen.getByText("build")).toBeTruthy();

    fireEvent.click(screen.getByLabelText("What does the quality gate check?"));
    expect(screen.queryByText("Quality gate checks")).toBeNull();

    fireEvent.click(screen.getByText("Refresh"));
    expect(refreshMock).toHaveBeenCalledTimes(1);
  });
});
