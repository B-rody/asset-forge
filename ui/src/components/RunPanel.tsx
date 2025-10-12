import React, { useState, useEffect } from "react";
import { Zap, FolderOpen, Target, Search } from "lucide-react";
import { open } from "@tauri-apps/api/dialog";
import { open as openPath } from "@tauri-apps/api/shell";
import { ipcClient } from "@/lib/ipc";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

type TabId = "one-click" | "history";

interface RunPanelProps {
  activeTab: TabId;
  onResearchOnly?: () => void;
  onAutoGenerate?: () => void;
  isRunning: boolean;
  runningMode?: "research" | "auto" | "plan" | null;
}

export function RunPanel({ activeTab, onResearchOnly, onAutoGenerate, isRunning, runningMode }: RunPanelProps) {
  const [useFocusedMode, setUseFocusedMode] = useState(false);
  const [keyword, setKeyword] = useState("");
  const [outputFolder, setOutputFolder] = useState("");
  const [defaultOutputFolder, setDefaultOutputFolder] = useState("");
  const [isCustomPath, setIsCustomPath] = useState(false);
  const [mockMode, setMockMode] = useState(false);

  // Load output folder on mount
  useEffect(() => {
    const loadOutputFolder = async () => {
      const unsubscribe = ipcClient.subscribe((event) => {
        if (event.event === "output_folder_status") {
          unsubscribe();
          const currentPath = event.current_path || "";
          const defaultPath = event.default_path || "";
          setOutputFolder(currentPath);
          setDefaultOutputFolder(defaultPath);
          setIsCustomPath(event.is_custom === true);
        }
      });

      await ipcClient.sendCommand({ cmd: "get_output_folder" });

      setTimeout(() => {
        unsubscribe();
      }, 2000);
    };

    loadOutputFolder();
  }, []);

  const handleBrowseFolder = async () => {
    try {
      const selected = await open({
        directory: true,
        multiple: false,
        title: "Select Output Folder",
      });

      if (selected && typeof selected === "string") {
        // Subscribe to save result
        const unsubscribe = ipcClient.subscribe((event) => {
          if (event.event === "output_folder_saved") {
            unsubscribe();
            if (event.success) {
              setOutputFolder(event.path || selected);
              setIsCustomPath(event.path !== defaultOutputFolder);
            }
          } else if (event.event === "error") {
            unsubscribe();
            alert(`Failed to save output folder: ${event.message}`);
          }
        });

        // Save to backend
        await ipcClient.sendCommand({
          cmd: "save_output_folder",
          params: { folder_path: selected }
        });

        setTimeout(() => {
          unsubscribe();
        }, 2000);
      }
    } catch (error) {
      console.error("Failed to open folder dialog:", error);
    }
  };

  const handleResetToDefault = async () => {
    try {
      const unsubscribe = ipcClient.subscribe((event) => {
        if (event.event === "output_folder_reset") {
          unsubscribe();
          if (event.success) {
            setOutputFolder(event.path || defaultOutputFolder);
            setIsCustomPath(false);
          }
        } else if (event.event === "error") {
          unsubscribe();
          alert(`Failed to reset output folder: ${event.message}`);
        }
      });

      await ipcClient.sendCommand({ cmd: "reset_output_folder" });

      setTimeout(() => {
        unsubscribe();
      }, 2000);
    } catch (error) {
      console.error("Failed to reset output folder:", error);
    }
  };

  const handleOpenOutputDir = async () => {
    if (!outputFolder) {
      alert("No output folder set");
      return;
    }

    try {
      await openPath(outputFolder);
    } catch (error) {
      console.error("Failed to open output directory:", error);
      const errorMsg = error instanceof Error ? error.message : String(error);
      alert(`Failed to open folder: ${errorMsg}\n\nPath: ${outputFolder}`);
    }
  };

  const handleRun = async () => {
    // If not in mock mode, check for API key first
    if (!mockMode) {
      try {
        // Check if API key exists
        const hasKey = await checkApiKey();
        if (!hasKey) {
          alert("Please add your OpenAI API key in Settings before running the pipeline.");
          return;
        }
      } catch (error) {
        console.error("Failed to check API key:", error);
        alert("Failed to verify API key. Please check your settings.");
        return;
      }
    }

    if (onAutoGenerate) {
      onAutoGenerate();
    }

    if (useFocusedMode) {
      await ipcClient.sendCommand({
        cmd: "run_pipeline",
        mode: "focused",
        params: { keyword, mockMode },
      });
    } else {
      await ipcClient.sendCommand({
        cmd: "run_pipeline",
        mode: "one_click",
        params: { mockMode },
      });
    }
  };

  const handleResearchRun = async () => {
    // If not in mock mode, check for API key first
    if (!mockMode) {
      try {
        // Check if API key exists
        const hasKey = await checkApiKey();
        if (!hasKey) {
          alert("Please add your OpenAI API key in Settings before running the pipeline.");
          return;
        }
      } catch (error) {
        console.error("Failed to check API key:", error);
        alert("Failed to verify API key. Please check your settings.");
        return;
      }
    }

    if (onResearchOnly) {
      onResearchOnly();
    }

    // Send research-only command
    if (useFocusedMode) {
      await ipcClient.sendCommand({
        cmd: "run_pipeline",
        mode: "research_only_focused",
        params: { keyword, mockMode },
      });
    } else {
      await ipcClient.sendCommand({
        cmd: "run_pipeline",
        mode: "research_only",
        params: { mockMode },
      });
    }
  };

  const checkApiKey = async (): Promise<boolean> => {
    return new Promise((resolve) => {
      let resolved = false;

      // Subscribe to API key status event
      const unsubscribe = ipcClient.subscribe((event) => {
        if (event.event === "api_key_status") {
          if (!resolved) {
            resolved = true;
            unsubscribe();
            console.log("API key check result:", event.has_key);
            resolve(event.has_key === true);
          }
        }
      });

      // Send command to check
      console.log("Checking API key...");
      ipcClient.sendCommand({ cmd: "get_api_key" });

      // Timeout after 5 seconds (increased from 2)
      setTimeout(() => {
        if (!resolved) {
          resolved = true;
          unsubscribe();
          console.warn("API key check timed out");
          resolve(false);
        }
      }, 5000);
    });
  };

  // Keyboard shortcut listener (Ctrl+Enter or Cmd+Enter) - triggers auto-generate
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        if (!isRunning && (!useFocusedMode || keyword)) {
          handleRun();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isRunning, useFocusedMode, keyword, runningMode]);

  return (
    <div className="rounded-xl border border-border bg-gradient-to-b from-white to-slate-50 dark:from-slate-900 dark:to-slate-950 p-6 shadow-sm hover:shadow-md transition-shadow duration-200 border-l-4 border-l-primary">
      {activeTab === "history" ? (
        <>
          <h2 className="mb-2 text-lg font-semibold">Previous Runs</h2>
          <div className="text-sm text-muted-foreground">
            <p>No previous runs yet. Start a generation to see history.</p>
          </div>
        </>
      ) : (
        <div className="space-y-6">
          {/* Header */}
          <div>
            <h2 className="text-lg md:text-xl font-semibold">
              One-Click Generation
            </h2>
            <p className="mt-1 text-sm text-muted-foreground/90">
              Autonomously research, design, and generate a complete digital product bundle
            </p>
          </div>

          {/* Focus on specific niche toggle */}
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="focus-mode"
              checked={useFocusedMode}
              onChange={(e) => setUseFocusedMode(e.target.checked)}
              className="h-4 w-4 rounded border-input"
            />
            <Label htmlFor="focus-mode" className="font-normal flex items-center gap-2">
              <Target className="h-4 w-4" />
              Focus on specific niche
            </Label>
          </div>

          {/* Focused mode keyword input (conditional) */}
          {useFocusedMode && (
            <div className="space-y-2">
              <Label htmlFor="keyword">Keyword or Niche</Label>
              <input
                id="keyword"
                type="text"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="e.g., notion templates, wedding invitations"
                className={cn(
                  "w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
                  "placeholder:text-muted-foreground",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                )}
              />
            </div>
          )}

          {/* Settings Panel */}
          <div className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-slate-900/60
                          divide-y divide-slate-300/50 dark:divide-slate-700/50">
            {/* Output Location */}
            <div className="p-4 space-y-3">
              <div>
                <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-200">
                  Output Location
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  All generated bundles will be saved here.
                </p>
              </div>

              {/* Buttons */}
              <div className="flex items-center gap-2 pt-1">
                <button
                  type="button"
                  onClick={handleBrowseFolder}
                  className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white
                             dark:border-slate-600 dark:bg-slate-800 px-3 py-2 text-sm
                             hover:border-blue-400 dark:hover:border-blue-500 transition-colors"
                >
                  <FolderOpen className="h-4 w-4" />
                  Browse…
                </button>

                {isCustomPath && (
                  <button
                    type="button"
                    onClick={handleResetToDefault}
                    className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white
                               dark:border-slate-600 dark:bg-slate-800 px-3 py-2 text-sm
                               hover:border-amber-400 dark:hover:border-amber-500 transition-colors"
                    title="Reset to default location"
                  >
                    Reset to Default
                  </button>
                )}

                <button
                  type="button"
                  onClick={handleOpenOutputDir}
                  disabled={!outputFolder}
                  className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white
                             dark:border-slate-600 dark:bg-slate-800 px-3 py-2 text-sm
                             hover:border-blue-400 dark:hover:border-blue-500 transition-colors
                             disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Open folder in file explorer"
                >
                  <FolderOpen className="h-4 w-4" />
                  Open
                </button>
              </div>

              {/* Path Display */}
              {outputFolder && (
                <div className={cn(
                  "mt-2 rounded-md border px-3 py-2 text-xs font-mono break-all",
                  isCustomPath
                    ? "border-blue-300 bg-blue-50 text-blue-900 dark:border-blue-700 dark:bg-blue-950 dark:text-blue-200"
                    : "border-slate-300 bg-slate-100 text-slate-700 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300"
                )}>
                  {outputFolder}
                </div>
              )}
            </div>

            {/* Mock Mode */}
            <div className="p-4 space-y-2">
              <div className="flex items-center gap-3">
                <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-200">
                  Mock Mode (demo)
                </h3>
                <label className="relative inline-flex cursor-pointer items-center">
                  <input
                    type="checkbox"
                    className="peer sr-only"
                    checked={mockMode}
                    onChange={(e) => setMockMode(e.target.checked)}
                    aria-describedby="mock-desc"
                  />
                  <span className="h-4 w-8 rounded-full bg-slate-300 dark:bg-slate-700
                                   peer-checked:bg-blue-500 dark:peer-checked:bg-blue-600
                                   transition-colors
                                   after:absolute after:left-0.5 after:top-0.5
                                   after:h-3 after:w-3 after:rounded-full after:bg-white
                                   after:transition-transform peer-checked:after:translate-x-3.5" />
                </label>
              </div>
              <p id="mock-desc" className="text-xs text-slate-500 dark:text-slate-400">
                {mockMode
                  ? "ON — Generates sample bundle; skips API calls."
                  : "OFF — Runs full AI pipeline."}
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            {/* Research Ideas Button */}
            <button
              type="button"
              onClick={isRunning ? undefined : handleResearchRun}
              disabled={isRunning && runningMode !== "research"}
              className={cn(
                "w-full flex items-center gap-3 p-4 rounded-lg border-2 transition-all",
                runningMode === "research"
                  ? "border-blue-400 bg-blue-50 dark:bg-blue-950/30 animate-pulse pointer-events-none"
                  : "border-border bg-card hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/30",
                "disabled:opacity-50 disabled:cursor-not-allowed"
              )}
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/30">
                <Search className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="flex-1 text-left">
                <div className="font-semibold">
                  {runningMode === "research" ? "Researching…" : "Research Ideas"}
                </div>
                <div className="text-xs text-muted-foreground">Find opportunities, review & pick</div>
              </div>
            </button>

            {/* Generate Bundle (Auto) Button */}
            <button
              type="button"
              onClick={isRunning ? undefined : handleRun}
              disabled={isRunning && runningMode !== "auto"}
              className={cn(
                "w-full relative overflow-hidden p-4 rounded-lg",
                "transition-all duration-[250ms] ease-in-out",
                "focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:ring-offset-2",
                "dark:focus-visible:ring-offset-slate-900",
                "bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500",
                // Hover state (when not running)
                !isRunning && "hover:brightness-110 hover:shadow-[0_0_12px_#2563eb80]",
                // Active/Generating state (only when this button is running)
                runningMode === "auto" && [
                  "animate-gradient-shift",
                  "brightness-125",
                  "shadow-[0_0_24px_rgba(37,99,235,1)]",
                  "scale-[1.02]",
                  "pointer-events-none",
                  "cursor-not-allowed"
                ],
                // Disabled state
                "disabled:opacity-50 disabled:cursor-not-allowed"
              )}
            >
              {/* Pulsing inner glow when generating */}
              {runningMode === "auto" && (
                <span className="absolute inset-0 bg-[radial-gradient(circle,_rgba(59,130,246,0.5)_0%,_transparent_70%)] animate-pulse rounded-lg" />
              )}

              <div className={cn(
                "relative flex items-center gap-3 text-white"
              )}>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/20">
                  <Zap className="h-5 w-5" />
                </div>
                <div className="flex-1 text-left">
                  <div className="font-semibold">
                    {runningMode === "auto" ? "Generating…" : "Generate Bundle (Auto)"}
                  </div>
                  <div className="text-xs opacity-90">Full pipeline, AI picks best idea</div>
                </div>
              </div>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
