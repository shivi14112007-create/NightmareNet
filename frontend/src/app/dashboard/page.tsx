import type { Metadata } from "next";
import { DashboardRoot } from "@/components/dashboard/DashboardRoot";

export const metadata: Metadata = {
  title: "NightmareNet · Dashboard",
  description:
    "Mission control for NightmareNet — experiments, robustness, distortions, benchmarks, and CI in a single workspace.",
};

export default function DashboardPage() {
  return <DashboardRoot />;
}
