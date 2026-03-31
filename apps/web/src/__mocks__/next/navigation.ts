import { vi } from "vitest";

export const refreshMock = vi.fn();

export function useRouter() {
  return {
    refresh: refreshMock,
  };
}
