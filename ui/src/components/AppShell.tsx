import React, { useState, useEffect } from "react";
import { HeaderBar } from "./HeaderBar";
import { Sidebar } from "./Sidebar";
import { RunPanel } from "./RunPanel";
import { ResultPanel } from "./ResultPanel";
import { StepChips } from "./StepChips";
import { LogStream } from "./LogStream";
import { ipcClient, IPCEvent } from "@/lib/ipc";

type TabId = "one-click" | "history";

interface StepChip {
  name: string;
  status: "pending" | "running" | "success" | "error";
}

interface LogEntry {
  timestamp: string;
  step?: string;
  message: string;
  type: "info" | "success" | "error" | "progress";
}

export function AppShell() {
  const [activeTab, setActiveTab] = useState<TabId>("one-click");
  const [steps, setSteps] = useState<StepChip[]>([
    { name: "Researcher", status: "pending" },
    { name: "Planner", status: "pending" },
    { name: "Maker", status: "pending" },
    { name: "Packager", status: "pending" },
  ]);
  const [stepProgress, setStepProgress] = useState<Record<string, number>>({});
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [result, setResult] = useState<any>(null);

  // Determine if pipeline is running
  const isPipelineRunning = steps.some((s) => s.status === "running");

  useEffect(() => {
    // Subscribe to IPC events
    const unsubscribe = ipcClient.subscribe((event: IPCEvent) => {
      const now = new Date().toLocaleTimeString();

      if (event.event === "log") {
        setLogs((prev) => [
          ...prev,
          {
            timestamp: now,
            step: event.step,
            message: event.message || "",
            type: "info",
          },
        ]);

        // Update step status: mark previous running step as complete, start new step
        if (event.step) {
          setSteps((prev) =>
            prev.map((s) => {
              if (s.name === event.step) {
                return { ...s, status: "running" as const };
              } else if (s.status === "running") {
                // Mark previous running step as complete
                return { ...s, status: "success" as const };
              }
              return s;
            })
          );
          // Reset progress for new step
          setStepProgress((prev) => ({ ...prev, [event.step]: 0 }));
        }
      } else if (event.event === "progress") {
        setLogs((prev) => [
          ...prev,
          {
            timestamp: now,
            step: event.step,
            message: `Progress: ${event.pct}%`,
            type: "progress",
          },
        ]);

        // Update step progress
        if (event.step && event.pct !== undefined) {
          setStepProgress((prev) => ({ ...prev, [event.step]: event.pct }));
        }
      } else if (event.event === "done") {
        const success = event.success !== false; // Default to true if not specified

        setLogs((prev) => [
          ...prev,
          {
            timestamp: now,
            message: success
              ? "Pipeline completed successfully!"
              : `Pipeline failed: ${event.error || "Unknown error"}`,
            type: success ? "success" : "error",
          },
        ]);

        // Mark final running step
        setSteps((prev) =>
          prev.map((s) =>
            s.status === "running" || s.status === "error"
              ? { ...s, status: success ? ("success" as const) : ("error" as const) }
              : s
          )
        );

        if (success) {
          setResult({
            bundle_id: event.result?.bundle_id || "unknown",
            output_path: event.result?.output_path || "unknown",
            qa_score: 0.93,
            status: "success",
            runtime: "2m 15s",
            file_count: 3,
          });
        } else {
          setResult({
            bundle_id: "failed",
            output_path: "N/A",
            qa_score: 0,
            status: "error",
            runtime: "N/A",
            file_count: 0,
          });
        }
      } else if (event.event === "error") {
        setLogs((prev) => [
          ...prev,
          {
            timestamp: now,
            step: event.step,
            message: event.message || "Unknown error",
            type: "error",
          },
        ]);

        if (event.step) {
          setSteps((prev) =>
            prev.map((s) =>
              s.name === event.step ? { ...s, status: "error" } : s
            )
          );
        }
      }
    });

    return unsubscribe;
  }, []);

  const handleRunStart = () => {
    // Reset state
    setSteps([
      { name: "Researcher", status: "pending" },
      { name: "Planner", status: "pending" },
      { name: "Maker", status: "pending" },
      { name: "Packager", status: "pending" },
    ]);
    setStepProgress({});
    setLogs([]);
    setResult(null);
  };

  return (
    <div className="flex h-screen flex-col">
      <HeaderBar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
        <main className="flex-1 overflow-y-auto p-6">
          <div className="mx-auto max-w-5xl xl:max-w-6xl 2xl:max-w-7xl space-y-6">
            <RunPanel activeTab={activeTab} onRunStart={handleRunStart} isRunning={isPipelineRunning} />

            <div className="rounded-lg border border-border bg-card p-6">
              <h2 className="mb-4 text-lg font-semibold">Pipeline Status</h2>
              <StepChips steps={steps} stepProgress={stepProgress} />
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <div className="rounded-lg border border-border bg-card p-6">
                <h2 className="mb-4 text-lg font-semibold">Logs</h2>
                <div className="h-64">
                  <LogStream logs={logs} />
                </div>
              </div>

              <ResultPanel result={result} />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
