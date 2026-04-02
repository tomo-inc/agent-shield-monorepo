import type { PanelHealth, PanelOnboardingStatus, PanelRunStatus } from "@/src/lib/panel";

export function formatDateTime(value: string | null | undefined): string {
  if (value == null) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(date);
}

export function formatDuration(value: number | null | undefined): string {
  if (value == null) {
    return "-";
  }

  return `${value}s`;
}

export function formatPercent(value: number | null | undefined): string {
  if (value == null) {
    return "-";
  }

  return `${value.toFixed(1)}%`;
}

export function getStatusTone(
  status: PanelRunStatus | "skip",
): "pass" | "fail" | "blocked" | "neutral" {
  if (status === "pass") {
    return "pass";
  }

  if (status === "fail") {
    return "fail";
  }

  if (status === "blocked" || status === "timeout") {
    return "blocked";
  }

  return "neutral";
}

export function getHealthTone(health: PanelHealth): "pass" | "fail" | "blocked" | "neutral" {
  if (health === "healthy") {
    return "pass";
  }

  if (health === "failing") {
    return "fail";
  }

  if (health === "warning") {
    return "blocked";
  }

  return "neutral";
}

export function getOnboardingTone(
  onboardingStatus: PanelOnboardingStatus,
): "ready" | "pending" | "blocked" | "neutral" {
  if (onboardingStatus === "ready") {
    return "ready";
  }

  if (onboardingStatus === "pending") {
    return "pending";
  }

  if (onboardingStatus === "blocked") {
    return "blocked";
  }

  return "neutral";
}
