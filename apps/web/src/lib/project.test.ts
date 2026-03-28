import { describe, expect, it } from "vitest";

import { currentFocus, priorities } from "./project";

describe("project focus", () => {
  it("keeps QA automation as the first priority", () => {
    expect(currentFocus).toBe("QA automation feasibility research");
  });
});
