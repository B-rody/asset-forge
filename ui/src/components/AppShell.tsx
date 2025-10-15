import React, { useState, useEffect } from "react";
import { HeaderBar } from "./HeaderBar";
import { Sidebar } from "./Sidebar";
import { RunPanel } from "./RunPanel";
import { ResultPanel } from "./ResultPanel";
import { StepChips } from "./StepChips";
import { LogStream } from "./LogStream";
import { LibraryPanel } from "./LibraryPanel";
import { HistoryPanel } from "./HistoryPanel";
import { ipcClient, IPCEvent } from "@/lib/ipc";

type TabId = "one-click" | "library" | "history";

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
  const [pipelineStartTime, setPipelineStartTime] = useState<number | null>(null);
  const [runningMode, setRunningMode] = useState<"research" | "auto" | "plan" | "maker" | "packager" | null>(null);

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
          setSteps((prev) => {
            const newSteps = prev.map((s) => {
              if (s.name === event.step) {
                return { ...s, status: "running" as const };
              } else if (s.status === "running") {
                // Mark previous running step as complete
                return { ...s, status: "success" as const };
              }
              return s;
            });

            // Set start time if this is the first step to run
            if (prev.every((s) => s.status === "pending")) {
              setPipelineStartTime(Date.now());
            }

            return newSteps;
          });
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
        const researchOnly = event.research_only === true;
        const wasPlanMode = runningMode === "plan"; // Capture before clearing
        const wasMakerMode = runningMode === "maker";
        const wasPackagerMode = runningMode === "packager";
        const wasSingleStep = wasPlanMode || wasMakerMode || wasPackagerMode;

        // Calculate actual runtime
        let runtime: string | undefined;
        if (pipelineStartTime) {
          const elapsedSeconds = Math.floor((Date.now() - pipelineStartTime) / 1000);
          const minutes = Math.floor(elapsedSeconds / 60);
          const seconds = elapsedSeconds % 60;
          runtime = minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;
        }

        setLogs((prev) => [
          ...prev,
          {
            timestamp: now,
            message: success
              ? event.result?.message || (researchOnly
                ? "Research completed! Navigating to Library..."
                : wasPlanMode
                ? "Bundle plan created successfully! Navigating to Library..."
                : wasMakerMode
                ? "Asset generation completed successfully! Navigating to Library..."
                : wasPackagerMode
                ? "Bundle packaging completed successfully!"
                : "Pipeline completed successfully!")
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

        // Set result data with actual values from backend
        if (success) {
          setResult({
            bundle_id: event.result?.bundle_id || "unknown",
            bundle_title: event.result?.bundle_title,
            output_path: event.result?.output_path,
            file_count: event.result?.file_count,
            ideas_count: event.result?.ideas_count,
            store_title: event.result?.store_title,
            store_description: event.result?.store_description,
            converted_pdfs: event.result?.converted_pdfs,
            message: event.result?.message,
            status: "success",
            runtime,
            mode: runningMode, // Pass the mode so ResultPanel knows context
          });
        } else {
          setResult({
            bundle_id: "failed",
            output_path: "N/A",
            status: "error",
            runtime,
            mode: runningMode,
          });
        }

        // Clear pipeline start time and running mode
        setPipelineStartTime(null);
        setRunningMode(null);

        // If any single-step mode completed successfully, navigate to Library tab
        if (success && (researchOnly || wasSingleStep)) {
          setTimeout(() => {
            setActiveTab("library");
          }, 1500); // Brief delay to let user see success message
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

        // Clear pipeline start time and running mode on error
        setPipelineStartTime(null);
        setRunningMode(null);
      }
    });

    return unsubscribe;
  }, []);

  const handleRunStart = (stepsToShow?: StepChip[]) => {
    // Reset state
    const defaultSteps = [
      { name: "Researcher", status: "pending" as const },
      { name: "Planner", status: "pending" as const },
      { name: "Maker", status: "pending" as const },
      { name: "Packager", status: "pending" as const },
    ];

    setSteps(stepsToShow || defaultSteps);
    setStepProgress({});
    setLogs([]);
    setResult(null);
    setPipelineStartTime(null);
  };

  const handleCreatePlanFromIdea = (ideaId: string) => {
    // Reset state for new pipeline run - only show Planner step
    handleRunStart([
      { name: "Planner", status: "pending" },
    ]);
    setRunningMode("plan");

    // Switch to Generate tab to show pipeline progress
    setActiveTab("one-click");

    // Send IPC command to create bundle plan from idea
    ipcClient.sendCommand({
      cmd: "build_from_idea",
      params: { idea_id: ideaId }
    });
  };

  const handleGenerateAssets = (bundleId: string) => {
    // Reset state for new pipeline run - only show Maker step
    handleRunStart([
      { name: "Maker", status: "pending" },
    ]);
    setRunningMode("maker");

    // Switch to Generate tab to show pipeline progress
    setActiveTab("one-click");

    // Send IPC command to generate assets from bundle
    ipcClient.sendCommand({
      cmd: "generate_assets_from_bundle",
      params: { bundle_id: bundleId }
    });
  };

  const handlePackageBundle = (bundleId: string) => {
    // Reset state for new pipeline run - only show Packager step
    handleRunStart([
      { name: "Packager", status: "pending" },
    ]);
    setRunningMode("packager");

    // Switch to Generate tab to show pipeline progress
    setActiveTab("one-click");

    // Send IPC command to package bundle
    ipcClient.sendCommand({
      cmd: "package_bundle",
      params: { bundle_id: bundleId }
    });
  };

  const handleResearchOnly = () => {
    // Reset state for research-only mode - only show Researcher step
    handleRunStart([
      { name: "Researcher", status: "pending" },
    ]);
    setRunningMode("research");
  };

  const handleAutoGenerate = () => {
    // Reset state for full pipeline
    handleRunStart();
    setRunningMode("auto");
  };

  const handleOpenFolder = (path: string) => {
    // Send IPC command to open folder in file explorer
    ipcClient.sendCommand({
      cmd: "open_folder",
      params: { path }
    });
  };

  return (
    <div className="flex h-screen flex-col">
      <HeaderBar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
        <main className="flex-1 overflow-y-auto p-6">
          <div className="mx-auto max-w-5xl xl:max-w-6xl 2xl:max-w-7xl space-y-6">
            {activeTab === "library" ? (
              <LibraryPanel
                onBuildBundle={handleCreatePlanFromIdea}
                onGenerateAssets={handleGenerateAssets}
                onPackageBundle={handlePackageBundle}
              />
            ) : activeTab === "history" ? (
              <HistoryPanel onOpenFolder={handleOpenFolder} />
            ) : (
              <>
                <RunPanel
                  activeTab={activeTab}
                  onResearchOnly={handleResearchOnly}
                  onAutoGenerate={handleAutoGenerate}
                  isRunning={isPipelineRunning}
                  runningMode={runningMode}
                />

                <div className="rounded-lg border border-border bg-card p-6">
                  <h2 className="mb-4 text-lg font-semibold">Pipeline Status</h2>
                  <StepChips steps={steps} stepProgress={stepProgress} />
                </div>

                <div className="grid gap-6 lg:grid-cols-2">
                  <div className="rounded-lg border border-border bg-card p-6">
                    <h2 className="mb-4 text-lg font-semibold">Logs</h2>
                    <div className="h-64">
                      <LogStream
                        logs={logs}
                        isProcessing={isPipelineRunning}
                        startTime={pipelineStartTime}
                      />
                    </div>
                  </div>

                  <ResultPanel
                    result={result}
                    onGenerateAssets={handleGenerateAssets}
                    onPackageBundle={handlePackageBundle}
                    onNavigateToLibrary={() => setActiveTab("library")}
                  />
                </div>
              </>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
