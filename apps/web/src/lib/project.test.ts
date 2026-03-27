import { describe, expect, it } from "vitest";

import { currentFocus, priorities } from "./project";

describe("project focus", () => {
  it("keeps QA automation as the first priority", () => {
    expect(currentFocus()).toBe("QA 自动化功能可行性调研");
    expect(priorities).toHaveLength(3);
  });
});
