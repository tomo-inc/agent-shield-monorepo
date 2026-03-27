export const priorities = [
  "QA 自动化功能可行性调研",
  "Analyzer / Generator / Runner / Tracker 契约沉淀",
  "安全类 Agent Shield 需求延后到 Phase 2",
];

export function currentFocus(): string {
  return priorities[0];
}
