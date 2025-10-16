import { useState, useEffect, useRef } from "react";
import { HeaderBar } from "./HeaderBar";
import { Sidebar } from "./Sidebar";
import { RunPanel } from "./RunPanel";
import { ResultPanel } from "./ResultPanel";
import { StepChips } from "./StepChips";
import { LogStream } from "./LogStream";
import { LibraryPanel, LibraryTab } from "./LibraryPanel";
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

// Backend now sends normalized step names directly (e.g., "Packager", "Maker", "Planner", "Researcher")
// No normalization needed - just pass through the step name
const normalizeStepName = (backendStepName: string | undefined): string | undefined => {
  return backendStepName;
};

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
  const [libraryDefaultTab, setLibraryDefaultTab] = useState<LibraryTab | undefined>(undefined);

  // Use refs to avoid resubscription race condition
  const runningModeRef = useRef(runningMode);
  const pipelineStartTimeRef = useRef(pipelineStartTime);

  // Update refs when state changes
  useEffect(() => {
    runningModeRef.current = runningMode;
  }, [runningMode]);

  useEffect(() => {
    pipelineStartTimeRef.current = pipelineStartTime;
  }, [pipelineStartTime]);

  // Determine if pipeline is running
  const isPipelineRunning = steps.some((s) => s.status === "running");

  // Debug log when isPipelineRunning changes
  useEffect(() => {
    console.log("🔴 [AppShell] isPipelineRunning changed:", isPipelineRunning, "| steps:", JSON.stringify(steps.map(s => ({ name: s.name, status: s.status }))));
  }, [isPipelineRunning, steps]);

  useEffect(() => {
    // Subscribe to IPC events
    const unsubscribe = ipcClient.subscribe((event: IPCEvent) => {
      console.log("🔵 [AppShell] Received event:", event);
      const now = new Date().toLocaleTimeString();

      if (event.event === "log") {
        const normalizedStep = normalizeStepName(event.step);
        console.log(`🟢 [AppShell] Normalized step: "${event.step}" → "${normalizedStep}"`);

        setLogs((prev) => [
          ...prev,
          {
            timestamp: now,
            step: normalizedStep,
            message: event.message || "",
            type: "info",
          },
        ]);

        // Update step status: mark previous running step as complete, start new step
        if (normalizedStep) {
          setSteps((prev) => {
            console.log("🟡 [AppShell] Before setSteps:", JSON.stringify(prev.map(s => ({ name: s.name, status: s.status }))));
            const newSteps = prev.map((s) => {
              if (s.name === normalizedStep) {
                return { ...s, status: "running" as const };
              } else if (s.status === "running") {
                // Mark previous running step as complete
                return { ...s, status: "success" as const };
              }
              return s;
            });
            console.log("🟡 [AppShell] After setSteps:", JSON.stringify(newSteps.map(s => ({ name: s.name, status: s.status }))));

            // Set start time if this is the first step to run
            if (prev.every((s) => s.status === "pending")) {
              setPipelineStartTime(Date.now());
              console.log("⏱️ [AppShell] Set pipeline start time");
            }

            return newSteps;
          });
          // Reset progress for new step
          setStepProgress((prev) => ({ ...prev, [normalizedStep]: 0 }));
        }
      } else if (event.event === "progress") {
        const normalizedStep = normalizeStepName(event.step);

        setLogs((prev) => [
          ...prev,
          {
            timestamp: now,
            step: normalizedStep,
            message: `Progress: ${event.pct}%`,
            type: "progress",
          },
        ]);

        // Update step progress
        if (normalizedStep && typeof event.pct === 'number') {
          const pct = event.pct; // Capture value for type narrowing
          setStepProgress((prev) => ({ ...prev, [normalizedStep]: pct }));
        }
      } else if (event.event === "done") {
        const success = event.success !== false; // Default to true if not specified
        const researchOnly = event.research_only === true;
        const wasPlanMode = runningModeRef.current === "plan"; // Use ref for current value
        const wasMakerMode = runningModeRef.current === "maker";
        const wasPackagerMode = runningModeRef.current === "packager";
        const wasSingleStep = wasPlanMode || wasMakerMode || wasPackagerMode;

        // Calculate actual runtime
        let runtime: string | undefined;
        if (pipelineStartTimeRef.current) {
          const elapsedSeconds = Math.floor((Date.now() - pipelineStartTimeRef.current) / 1000);
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
            mode: runningModeRef.current, // Use ref for current value
          });
        } else {
          setResult({
            bundle_id: "failed",
            output_path: "N/A",
            status: "error",
            runtime,
            mode: runningModeRef.current,
          });
        }

        // Clear pipeline start time and running mode
        setPipelineStartTime(null);
        setRunningMode(null);

        // If any single-step mode completed successfully, navigate to Library tab
        if (success && (researchOnly || wasSingleStep)) {
          // Determine which Library sub-tab to show
          let targetTab: LibraryTab | undefined;
          if (researchOnly) {
            targetTab = "ideas";
          } else if (wasPlanMode) {
            targetTab = "ready";
          } else if (wasMakerMode) {
            targetTab = "generated";
          }
          // Note: wasPackagerMode doesn't navigate to Library

          if (!wasPackagerMode) {
            setLibraryDefaultTab(targetTab);
            setTimeout(() => {
              setActiveTab("library");
            }, 1500); // Brief delay to let user see success message
          }
        }
      } else if (event.event === "error") {
        const normalizedStep = normalizeStepName(event.step);

        setLogs((prev) => [
          ...prev,
          {
            timestamp: now,
            step: normalizedStep,
            message: event.message || "Unknown error",
            type: "error",
          },
        ]);

        if (normalizedStep) {
          setSteps((prev) =>
            prev.map((s) =>
              s.name === normalizedStep ? { ...s, status: "error" } : s
            )
          );
        }

        // Clear pipeline start time and running mode on error
        setPipelineStartTime(null);
        setRunningMode(null);
      }
    });

    return unsubscribe;
  }, []); // Empty array - subscribe once on mount, never resubscribe

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

  const handleBuildFullFromIdea = (ideaId: string) => {
    // Reset state for full pipeline run - show Planner, Maker, Packager steps
    handleRunStart([
      { name: "Planner", status: "pending" },
      { name: "Maker", status: "pending" },
      { name: "Packager", status: "pending" },
    ]);
    setRunningMode("auto");

    // Switch to Generate tab to show pipeline progress
    setActiveTab("one-click");

    // Send IPC command to build full bundle from idea
    ipcClient.sendCommand({
      cmd: "build_full_from_idea",
      params: { idea_id: ideaId }
    });
  };

  const handleNavigateToIdeasLibrary = () => {
    // Navigate to Library tab with Ideas sub-tab active
    setLibraryDefaultTab("ideas");
    setActiveTab("library");
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

  const handleQuickBuild = () => {
    // Reset state for quick build pipeline - skip Researcher
    handleRunStart([
      { name: "Planner", status: "pending" },
      { name: "Maker", status: "pending" },
      { name: "Packager", status: "pending" },
    ]);
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
                onBuildFullBundle={handleBuildFullFromIdea}
                onGenerateAssets={handleGenerateAssets}
                onPackageBundle={handlePackageBundle}
                defaultTab={libraryDefaultTab}
              />
            ) : activeTab === "history" ? (
              <HistoryPanel onOpenFolder={handleOpenFolder} />
            ) : (
              <>
                <RunPanel
                  activeTab={activeTab}
                  onResearchOnly={handleResearchOnly}
                  onAutoGenerate={handleAutoGenerate}
                  onQuickBuild={handleQuickBuild}
                  onNavigateToLibrary={handleNavigateToIdeasLibrary}
                  isRunning={isPipelineRunning}
                  runningMode={runningMode === "maker" || runningMode === "packager" ? null : runningMode}
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
