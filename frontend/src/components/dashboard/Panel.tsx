"use client";

import { motion } from "framer-motion";
import type { ReactNode } from "react";

export interface PanelProps {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  toolbar?: ReactNode;
  footer?: ReactNode;
  glow?: "neural" | "dream" | "nightmare" | "none";
  className?: string;
  bodyClassName?: string;
  children: ReactNode;
  delayMs?: number;
}

const glowMap = {
  neural: "shadow-[0_0_24px_rgba(34,211,238,0.06)] hover:border-neural/20",
  dream: "shadow-[0_0_24px_rgba(129,140,248,0.06)] hover:border-dream/20",
  nightmare: "shadow-[0_0_24px_rgba(248,113,113,0.05)] hover:border-nightmare/20",
  none: "",
};

export function Panel({
  title,
  subtitle,
  icon,
  toolbar,
  footer,
  glow = "none",
  className = "",
  bodyClassName = "",
  children,
  delayMs = 0,
}: PanelProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut", delay: delayMs / 1000 }}
      className={[
        "flex h-full flex-col overflow-hidden rounded-xl border border-white/[0.06] bg-abyss/40 backdrop-blur-md",
        "transition-colors",
        glowMap[glow],
        className,
      ].join(" ")}
    >
      <header className="flex items-start justify-between gap-3 border-b border-white/[0.04] px-4 py-3">
        <div className="flex min-w-0 items-start gap-2.5">
          {icon && (
            <span className="mt-0.5 flex h-7 w-7 items-center justify-center rounded-md bg-white/[0.04] text-slate-300">
              {icon}
            </span>
          )}
          <div className="min-w-0">
            <h3 className="truncate text-[13px] font-semibold tracking-wide text-slate-100">
              {title}
            </h3>
            {subtitle && (
              <p className="mt-0.5 truncate text-[11px] text-slate-500">{subtitle}</p>
            )}
          </div>
        </div>
        {toolbar && <div className="flex shrink-0 items-center gap-1.5">{toolbar}</div>}
      </header>
      <div className={["flex-1 px-4 py-3.5", bodyClassName].join(" ")}>{children}</div>
      {footer && (
        <footer className="flex items-center justify-end gap-2 border-t border-white/[0.04] px-4 py-2.5">
          {footer}
        </footer>
      )}
    </motion.section>
  );
}
