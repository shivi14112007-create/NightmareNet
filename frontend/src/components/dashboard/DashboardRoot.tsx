"use client";

import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AppShell } from "./AppShell";
import type { DashboardSectionKey } from "./Sidebar";
import { CommandCenter } from "./CommandCenter";
import { ExperimentList } from "./ExperimentList";
import { RunDetail } from "./RunDetail";
import { PhaseVisualizer } from "./PhaseVisualizer";
import { LiveMetrics } from "./LiveMetrics";
import { RobustnessRadar } from "./RobustnessRadar";
import { ModelComparison } from "./ModelComparison";
import { DistortionPreview } from "./DistortionPreview";
import { AuditTrail } from "./AuditTrail";
import { BenchmarkSuite } from "./BenchmarkSuite";
import { CIIntegration } from "./CIIntegration";
import { SettingsPanel } from "./SettingsPanel";

type SectionMeta = {
  title: string;
  breadcrumb: { label: string }[];
};

const SECTION_META: Record<DashboardSectionKey, SectionMeta> = {
  "command-center": { title: "Command Center", breadcrumb: [{ label: "Overview" }, { label: "Command Center" }] },
  experiments: { title: "Experiments", breadcrumb: [{ label: "Overview" }, { label: "Experiments" }] },
  "run-detail": { title: "Run Detail", breadcrumb: [{ label: "Overview" }, { label: "Run · wikitext-resilient-v3" }] },
  phases: { title: "Phase Visualizer", breadcrumb: [{ label: "Analytics" }, { label: "Phases" }] },
  metrics: { title: "Live Metrics", breadcrumb: [{ label: "Analytics" }, { label: "Metrics" }] },
  robustness: { title: "Robustness Radar", breadcrumb: [{ label: "Analytics" }, { label: "Radar" }] },
  compare: { title: "Model Comparison", breadcrumb: [{ label: "Analytics" }, { label: "Compare" }] },
  distortions: { title: "Distortion Preview", breadcrumb: [{ label: "Analytics" }, { label: "Distortions" }] },
  audit: { title: "Audit Trail", breadcrumb: [{ label: "Operations" }, { label: "Audit" }] },
  benchmarks: { title: "Benchmark Suite", breadcrumb: [{ label: "Operations" }, { label: "Benchmarks" }] },
  ci: { title: "CI Integration", breadcrumb: [{ label: "Operations" }, { label: "CI" }] },
  settings: { title: "Settings", breadcrumb: [{ label: "Operations" }, { label: "Settings" }] },
};

const stagger = {
  initial: {},
  animate: { transition: { staggerChildren: 0.06, delayChildren: 0.05 } },
};

const fadeIn = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.25, ease: "easeOut" as const } },
};

export function DashboardRoot() {
  const [section, setSection] = useState<DashboardSectionKey>("command-center");
  const meta = useMemo(() => SECTION_META[section], [section]);

  return (
    <AppShell
      activeSection={section}
      onSectionChange={setSection}
      title={meta.title}
      breadcrumb={meta.breadcrumb}
      apiStatus="online"
      onPaletteAction={(a) => {
        if (a === "new-run") setSection("experiments");
        if (a === "bench-mr") setSection("benchmarks");
        if (a === "export") setSection("run-detail");
        if (a === "cancel-run") setSection("run-detail");
      }}
    >
      <AnimatePresence mode="wait">
        <motion.div
          key={section}
          variants={stagger}
          initial="initial"
          animate="animate"
          exit={{ opacity: 0 }}
          className="space-y-4"
        >
          {section === "command-center" && (
            <>
              <motion.div variants={fadeIn}>
                <CommandCenter />
              </motion.div>
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <motion.div variants={fadeIn}>
                  <PhaseVisualizer activePhase={2} />
                </motion.div>
                <motion.div variants={fadeIn}>
                  <RobustnessRadar />
                </motion.div>
              </div>
              <motion.div variants={fadeIn}>
                <LiveMetrics />
              </motion.div>
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <motion.div variants={fadeIn}>
                  <DistortionPreview />
                </motion.div>
                <motion.div variants={fadeIn}>
                  <AuditTrail />
                </motion.div>
              </div>
            </>
          )}

          {section === "experiments" && (
            <motion.div variants={fadeIn}>
              <ExperimentList />
            </motion.div>
          )}

          {section === "run-detail" && (
            <>
              <motion.div variants={fadeIn}>
                <RunDetail />
              </motion.div>
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <motion.div variants={fadeIn}>
                  <LiveMetrics />
                </motion.div>
                <motion.div variants={fadeIn}>
                  <RobustnessRadar />
                </motion.div>
              </div>
            </>
          )}

          {section === "phases" && (
            <motion.div variants={fadeIn}>
              <PhaseVisualizer activePhase={1} />
            </motion.div>
          )}

          {section === "metrics" && (
            <motion.div variants={fadeIn}>
              <LiveMetrics />
            </motion.div>
          )}

          {section === "robustness" && (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
              <motion.div className="lg:col-span-2" variants={fadeIn}>
                <RobustnessRadar />
              </motion.div>
              <motion.div variants={fadeIn}>
                <ModelComparison />
              </motion.div>
            </div>
          )}

          {section === "compare" && (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <motion.div variants={fadeIn}>
                <ModelComparison />
              </motion.div>
              <motion.div variants={fadeIn}>
                <RobustnessRadar />
              </motion.div>
            </div>
          )}

          {section === "distortions" && (
            <motion.div variants={fadeIn}>
              <DistortionPreview />
            </motion.div>
          )}

          {section === "audit" && (
            <motion.div variants={fadeIn}>
              <AuditTrail />
            </motion.div>
          )}

          {section === "benchmarks" && (
            <motion.div variants={fadeIn}>
              <BenchmarkSuite />
            </motion.div>
          )}

          {section === "ci" && (
            <motion.div variants={fadeIn}>
              <CIIntegration />
            </motion.div>
          )}

          {section === "settings" && (
            <motion.div variants={fadeIn}>
              <SettingsPanel />
            </motion.div>
          )}
        </motion.div>
      </AnimatePresence>
    </AppShell>
  );
}
