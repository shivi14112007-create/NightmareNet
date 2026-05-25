"use client";

import { motion } from "framer-motion";
import {
  IconActivity,
  IconBeaker,
  IconBenchmark,
  IconGit,
  IconHistory,
  IconHome,
  IconLayers,
  IconRadar,
  IconRunning,
  IconSettings,
  IconShield,
  IconSparkle,
  IconTrend,
  IconWand,
} from "./icons";

export type DashboardSectionKey =
  | "command-center"
  | "experiments"
  | "run-detail"
  | "phases"
  | "metrics"
  | "robustness"
  | "compare"
  | "distortions"
  | "audit"
  | "benchmarks"
  | "ci"
  | "settings";

interface NavGroup {
  label: string;
  items: { key: DashboardSectionKey; label: string; icon: React.ReactNode; badge?: string }[];
}

const NAV: NavGroup[] = [
  {
    label: "Overview",
    items: [
      { key: "command-center", label: "Command Center", icon: <IconHome size={15} /> },
      { key: "experiments", label: "Experiments", icon: <IconBeaker size={15} />, badge: "12" },
      { key: "run-detail", label: "Run Detail", icon: <IconRunning size={15} /> },
    ],
  },
  {
    label: "Analytics",
    items: [
      { key: "phases", label: "Phase Visualizer", icon: <IconLayers size={15} /> },
      { key: "metrics", label: "Live Metrics", icon: <IconActivity size={15} /> },
      { key: "robustness", label: "Robustness Radar", icon: <IconRadar size={15} /> },
      { key: "compare", label: "Model Compare", icon: <IconTrend size={15} /> },
      { key: "distortions", label: "Distortions", icon: <IconWand size={15} /> },
    ],
  },
  {
    label: "Operations",
    items: [
      { key: "audit", label: "Audit Trail", icon: <IconHistory size={15} /> },
      { key: "benchmarks", label: "Benchmarks", icon: <IconBenchmark size={15} /> },
      { key: "ci", label: "CI Integration", icon: <IconGit size={15} /> },
      { key: "settings", label: "Settings", icon: <IconSettings size={15} /> },
    ],
  },
];

export interface SidebarProps {
  activeSection: DashboardSectionKey;
  onSectionChange: (key: DashboardSectionKey) => void;
  collapsed?: boolean;
}

export function Sidebar({
  activeSection,
  onSectionChange,
  collapsed = false,
}: SidebarProps) {
  return (
    <aside
      className={[
        "sticky top-0 hidden h-screen shrink-0 border-r border-white/[0.05] bg-void/80 backdrop-blur-xl md:flex md:flex-col",
        collapsed ? "w-[68px]" : "w-[232px]",
        "transition-[width] duration-200",
      ].join(" ")}
    >
      <div className="flex h-14 items-center gap-2 border-b border-white/[0.05] px-4">
        <motion.span
          initial={{ scale: 0.85, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.4 }}
          className="relative flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br from-dream to-neural shadow-[0_0_16px_rgba(34,211,238,0.4)]"
          aria-hidden="true"
        >
          <IconShield size={14} />
        </motion.span>
        {!collapsed && (
          <div className="min-w-0">
            <p className="text-sm font-semibold tracking-tight text-slate-100">NightmareNet</p>
            <p className="text-[10px] uppercase tracking-widest text-slate-500">Sprint · 03</p>
          </div>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto px-2 py-3">
        {NAV.map((group, gi) => (
          <div key={group.label} className={gi > 0 ? "mt-4" : ""}>
            {!collapsed && (
              <p className="mb-1 px-2 text-[10px] font-semibold uppercase tracking-widest text-slate-600">
                {group.label}
              </p>
            )}
            <ul className="space-y-0.5">
              {group.items.map((item) => {
                const active = activeSection === item.key;
                return (
                  <li key={item.key}>
                    <button
                      type="button"
                      onClick={() => onSectionChange(item.key)}
                      className={[
                        "group relative flex w-full items-center gap-2.5 rounded-md px-2 py-1.5 text-left text-[13px] cursor-pointer",
                        "transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neural/50",
                        active
                          ? "bg-neural/[0.08] text-neural"
                          : "text-slate-400 hover:bg-white/[0.04] hover:text-slate-200",
                      ].join(" ")}
                      aria-current={active ? "page" : undefined}
                      title={collapsed ? item.label : undefined}
                    >
                      {active && (
                        <motion.span
                          layoutId="sidebar-active"
                          className="absolute left-0 top-1.5 h-5 w-0.5 rounded-r bg-neural shadow-[0_0_8px_var(--color-neural)]"
                        />
                      )}
                      <span className="flex h-5 w-5 items-center justify-center">{item.icon}</span>
                      {!collapsed && (
                        <>
                          <span className="flex-1 truncate">{item.label}</span>
                          {item.badge && (
                            <span className="rounded-full bg-white/[0.06] px-1.5 py-0.5 text-[10px] font-mono text-slate-400">
                              {item.badge}
                            </span>
                          )}
                        </>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-white/[0.05] px-2 py-3">
        {!collapsed ? (
          <div className="rounded-lg border border-dream/20 bg-dream/[0.04] p-3">
            <div className="mb-1.5 flex items-center gap-1.5">
              <IconSparkle size={12} />
              <span className="text-[10px] font-semibold uppercase tracking-widest text-dream-soft">
                Robustness
              </span>
            </div>
            <p className="font-mono text-lg text-slate-100">82.4</p>
            <p className="text-[10px] text-slate-500">+4.1 vs last cycle</p>
          </div>
        ) : (
          <div className="flex h-9 items-center justify-center rounded-md bg-dream/[0.06] text-dream-soft">
            <IconSparkle size={14} />
          </div>
        )}
      </div>
    </aside>
  );
}
