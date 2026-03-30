import type { ReactNode } from "react";

export default function PanelLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <main
      style={{
        display: "grid",
        gap: "16px",
        padding: "24px 20px 32px",
        maxWidth: "1200px",
        margin: "0 auto",
      }}
    >
      {children}
    </main>
  );
}
