import { describe, expect, it } from "vitest";

import { formatDateTime, formatDuration, formatPercent, getHealthTone, getOnboardingTone, getStatusTone } from "./panelPresentation";

describe("panelPresentation", () => {
  it("formats date time values and handles null or invalid input", () => {
    expect(formatDateTime(null)).toBe("-");
    expect(formatDateTime("not-a-date")).toBe("not-a-date");
    expect(formatDateTime("2026-03-31T06:20:00Z")).toBeTruthy();
  });

  it("formats duration values", () => {
    expect(formatDuration(null)).toBe("-");
    expect(formatDuration(12.5)).toBe("12.5s");
  });

  it("formats percent values", () => {
    expect(formatPercent(null)).toBe("-");
    expect(formatPercent(81.234)).toBe("81.2%");
  });

  it("maps run status values to tones", () => {
    expect(getStatusTone("pass")).toBe("pass");
    expect(getStatusTone("fail")).toBe("fail");
    expect(getStatusTone("blocked")).toBe("blocked");
    expect(getStatusTone("timeout")).toBe("blocked");
    expect(getStatusTone("skip")).toBe("neutral");
    expect(getStatusTone("not-run")).toBe("neutral");
    expect(getStatusTone(null)).toBe("neutral");
  });

  it("maps health values to tones", () => {
    expect(getHealthTone("healthy")).toBe("pass");
    expect(getHealthTone("failing")).toBe("fail");
    expect(getHealthTone("warning")).toBe("blocked");
    expect(getHealthTone("unknown")).toBe("neutral");
  });

  it("maps onboarding status values to tones", () => {
    expect(getOnboardingTone("ready")).toBe("ready");
    expect(getOnboardingTone("pending")).toBe("pending");
    expect(getOnboardingTone("blocked")).toBe("blocked");
    expect(getOnboardingTone("custom-needed")).toBe("neutral");
  });
});
