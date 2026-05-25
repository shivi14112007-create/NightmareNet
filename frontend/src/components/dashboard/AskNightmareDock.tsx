"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "../ui/Button";
import { IconCommand, IconRunning, IconWand } from "./icons";
import type { DashboardSectionKey } from "./Sidebar";

interface Suggestion {
  id: string;
  label: string;
  detail: string;
  action: () => void;
}

interface ContextualAnswer {
  hint: string;
  next: Suggestion[];
}

/**
 * Context-aware copilot dock.
 *
 * For v1 this is a heuristic-driven hint surface — it inspects the current
 * dashboard section and proposes the next most useful action. The contract is
 * deliberately small so we can swap the heuristic backend for a streaming LLM
 * call (Azure OpenAI / Anthropic) without changing any consumer.
 *
 * Roadmap (tracked in docs/product-improvement-backlog.md):
 * - wire to /api/v1/copilot streaming endpoint
 * - per-user memory of dismissed suggestions
 * - voice / push-to-talk
 */
function buildAnswer(
  section: DashboardSectionKey,
  navigate: (s: DashboardSectionKey) => void
): ContextualAnswer {
  switch (section) {
    case "command-center":
      return {
        hint: "Welcome back. Your last cycle improved robustness by +13.6% — keep going with the next benchmark or stress-test an unseen attack.",
        next: [
          {
            id: "run-bench",
            label: "Run standard benchmark",
            detail: "DistilBERT · SST-2 · 4-phase cycle",
            action: () => navigate("benchmarks"),
          },
          {
            id: "stress",
            label: "Stress test current model",
            detail: "Sweep dream + nightmare 0.1-0.9",
            action: () => navigate("distortions"),
          },
        ],
      };
    case "experiments":
      return {
        hint: "Compare your two most recent runs side-by-side to see which configuration is converging fastest.",
        next: [
          {
            id: "compare",
            label: "Open Model Comparison",
            detail: "A/B overlay of latest two runs",
            action: () => navigate("compare"),
          },
        ],
      };
    case "run-detail":
      return {
        hint: "This run is in the Nightmare phase. Open the radar to see which attack family it's least robust against — that's where the next cycle should focus.",
        next: [
          {
            id: "radar",
            label: "Inspect robustness radar",
            detail: "5-axis weakness map",
            action: () => navigate("robustness"),
          },
        ],
      };
    case "distortions":
      return {
        hint: "Try the same input across strengths 0.1, 0.5, and 0.9 to see how nightmare distortion escalates — and where your model's decision boundary breaks.",
        next: [
          {
            id: "metrics",
            label: "Watch live metrics",
            detail: "Loss + robustness curves",
            action: () => navigate("metrics"),
          },
        ],
      };
    case "robustness":
      return {
        hint: "Your weakest axis is semantic distortion at high strength. Schedule a Nightmare-heavy cycle to harden it.",
        next: [
          {
            id: "phases",
            label: "Open Phase Visualizer",
            detail: "Tune nightmare strength schedule",
            action: () => navigate("phases"),
          },
        ],
      };
    case "ci":
      return {
        hint: "The robustness-check Action is wired. Set your threshold to your model's current avg distorted accuracy minus 0.02 to catch regressions without false alarms.",
        next: [
          {
            id: "settings",
            label: "Open Settings",
            detail: "Manage API keys + thresholds",
            action: () => navigate("settings"),
          },
        ],
      };
    case "audit":
      return {
        hint: "Filter by error events to triage failures faster — most regressions cluster in the first two cycles after a config change.",
        next: [],
      };
    default:
      return {
        hint: "Tip: press Cmd+K to jump anywhere, or ? to see every shortcut.",
        next: [],
      };
  }
}

interface AskNightmareDockProps {
  section: DashboardSectionKey;
  onNavigate: (s: DashboardSectionKey) => void;
}

export function AskNightmareDock({ section, onNavigate }: AskNightmareDockProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const answer = useMemo(() => buildAnswer(section, onNavigate), [section, onNavigate]);

  useEffect(() => {
    if (!open) return;
    const t = setTimeout(() => inputRef.current?.focus(), 50);
    return () => clearTimeout(t);
  }, [open]);

  const handleAsk = () => {
    // Heuristic: route the question to the closest suggestion if any keyword matches.
    const q = query.trim().toLowerCase();
    if (!q) return;
    const hit = answer.next.find((s) => s.label.toLowerCase().includes(q));
    if (hit) {
      hit.action();
      setOpen(false);
      setQuery("");
    }
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label="Ask NightmareNet copilot"
        aria-expanded={open}
        className="fixed bottom-5 right-5 z-[45] flex h-12 w-12 cursor-pointer items-center justify-center rounded-full border border-white/10 bg-gradient-to-br from-neural/30 to-dream/20 text-neural shadow-[0_8px_28px_rgba(6,182,212,0.32)] transition-transform hover:scale-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neural/60"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
          <path
            d="M3 14V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1H6.5L3 14Z"
            stroke="currentColor"
            strokeWidth="1.4"
            strokeLinejoin="round"
          />
          <circle cx="6.8" cy="7.5" r="0.8" fill="currentColor" />
          <circle cx="9" cy="7.5" r="0.8" fill="currentColor" />
          <circle cx="11.2" cy="7.5" r="0.8" fill="currentColor" />
        </svg>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, x: 24, y: 8 }}
            animate={{ opacity: 1, x: 0, y: 0 }}
            exit={{ opacity: 0, x: 24, y: 8 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
            className="fixed bottom-20 right-5 z-[46] w-full max-w-sm overflow-hidden rounded-2xl border border-white/[0.08] bg-abyss/95 shadow-[0_24px_60px_rgba(0,0,0,0.6)] backdrop-blur-xl"
            role="region"
            aria-label="NightmareNet copilot"
          >
            <div className="flex items-center justify-between border-b border-white/[0.06] px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="flex h-6 w-6 items-center justify-center rounded-md bg-neural/[0.15] text-neural">
                  <IconCommand size={12} />
                </span>
                <span className="text-sm font-semibold text-slate-100">Ask NightmareNet</span>
              </div>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close copilot"
                className="cursor-pointer rounded-md px-1.5 py-0.5 text-[11px] text-slate-500 hover:bg-white/5 hover:text-slate-300"
              >
                Esc
              </button>
            </div>

            <div className="space-y-3 px-4 py-4">
              <div className="rounded-lg border border-white/[0.05] bg-white/[0.02] px-3 py-2.5 text-[13px] leading-relaxed text-slate-300">
                <p className="mb-1 text-[10px] font-semibold uppercase tracking-widest text-neural">
                  Context · {section}
                </p>
                {answer.hint}
              </div>

              {answer.next.length > 0 && (
                <div className="space-y-1.5">
                  <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-600">
                    Suggested next steps
                  </p>
                  {answer.next.map((s) => (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => {
                        s.action();
                        setOpen(false);
                      }}
                      className="group flex w-full cursor-pointer items-center gap-3 rounded-md border border-white/[0.05] bg-white/[0.02] px-3 py-2 text-left transition-colors hover:border-neural/30 hover:bg-neural/[0.05]"
                    >
                      <span className="flex h-7 w-7 items-center justify-center rounded-md bg-white/[0.04] text-slate-400 group-hover:bg-neural/[0.12] group-hover:text-neural">
                        {s.id.includes("bench") || s.id.includes("metrics") ? (
                          <IconRunning size={13} />
                        ) : (
                          <IconWand size={13} />
                        )}
                      </span>
                      <span className="flex-1">
                        <span className="block text-[13px] text-slate-200">{s.label}</span>
                        <span className="block text-[11px] text-slate-500">{s.detail}</span>
                      </span>
                    </button>
                  ))}
                </div>
              )}

              <div>
                <p className="pb-1.5 text-[10px] font-semibold uppercase tracking-widest text-slate-600">
                  Ask anything
                </p>
                <div className="flex items-center gap-2 rounded-md border border-white/[0.06] bg-white/[0.02] px-2.5 py-2">
                  <input
                    ref={inputRef}
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleAsk();
                    }}
                    placeholder="e.g. compare last two runs"
                    className="flex-1 bg-transparent text-[13px] text-slate-200 placeholder:text-slate-600 focus:outline-none"
                  />
                  <Button size="sm" variant="ghost" onClick={handleAsk}>
                    Ask
                  </Button>
                </div>
                <p className="pt-1.5 text-[10px] text-slate-600">
                  v1 routes to the closest suggestion. Streaming LLM backend coming next.
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
