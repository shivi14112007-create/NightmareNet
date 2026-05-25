"use client";

import { useEffect, useState, type ReactNode } from "react";
import { Sidebar, type DashboardSectionKey } from "./Sidebar";
import { Topbar } from "./Topbar";
import { CommandPalette } from "./CommandPalette";
import { ToastProvider } from "@/components/ui/Toast";

export interface AppShellProps {
  activeSection: DashboardSectionKey;
  onSectionChange: (key: DashboardSectionKey) => void;
  title: string;
  breadcrumb?: { label: string; onClick?: () => void }[];
  apiStatus?: "online" | "degraded" | "offline";
  onPaletteAction?: (action: string) => void;
  children: ReactNode;
}

export function AppShell({
  activeSection,
  onSectionChange,
  title,
  breadcrumb,
  apiStatus = "online",
  onPaletteAction,
  children,
}: AppShellProps) {
  const [paletteOpen, setPaletteOpen] = useState(false);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((s) => !s);
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);

  return (
    <ToastProvider>
      <div className="min-h-screen bg-void text-slate-100">
        <div className="flex">
          <Sidebar activeSection={activeSection} onSectionChange={onSectionChange} />
          <div className="flex min-w-0 flex-1 flex-col">
            <Topbar
              title={title}
              breadcrumb={breadcrumb}
              onOpenCommandPalette={() => setPaletteOpen(true)}
              apiStatus={apiStatus}
            />
            <main className="flex-1 overflow-x-hidden px-4 py-5 sm:px-6 sm:py-6">
              {children}
            </main>
          </div>
        </div>
        <CommandPalette
          open={paletteOpen}
          onClose={() => setPaletteOpen(false)}
          onNavigate={(key) => {
            onSectionChange(key);
            setPaletteOpen(false);
          }}
          onAction={onPaletteAction}
        />
      </div>
    </ToastProvider>
  );
}
