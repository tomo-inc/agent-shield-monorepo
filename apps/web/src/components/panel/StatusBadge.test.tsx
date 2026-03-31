import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it("renders every supported tone", () => {
    const tones = ["ready", "pending", "pass", "fail", "blocked", "neutral"] as const;

    tones.forEach((tone) => {
      const { unmount } = render(<StatusBadge label={tone} tone={tone} />);
      expect(screen.getByText(tone)).toBeTruthy();
      unmount();
    });
  });
});
