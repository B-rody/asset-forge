import React, { useState, useEffect } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { Zap, Loader2, FolderOpen, ChevronDown, Target } from "lucide-react";
import { open } from "@tauri-apps/api/dialog";
import { open as openPath } from "@tauri-apps/api/shell";
import { ipcClient } from "@/lib/ipc";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

type TabId = "one-click" | "history";

interface RunPanelProps {
  activeTab: TabId;
  onRunStart: () => void;
  isRunning: boolean;
}

export function RunPanel({ activeTab, onRunStart, isRunning }: RunPanelProps) {
  const [useFocusedMode, setUseFocusedMode] = useState(false);
  const [keyword, setKeyword] = useState("");
  const [model, setModel] = useState("gpt-4o");
  const [reasoning, setReasoning] = useState("normal");
  const [outputFolder, setOutputFolder] = useState("");
  const [mockMode, setMockMode] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(false);

  const reduceMotion = useReducedMotion();

  const handleBrowseFolder = async () => {
    try {
      const selected = await open({
        directory: true,
        multiple: false,
        title: "Select Output Folder",
      });
      if (selected && typeof selected === "string") {
        setOutputFolder(selected);
      }
    } catch (error) {
      console.error("Failed to open folder dialog:", error);
    }
  };

  const handleOpenOutputDir = async () => {
    if (outputFolder) {
      try {
        await openPath(outputFolder);
      } catch (error) {
        console.error("Failed to open output directory:", error);
      }
    }
  };

  const handleRun = async () => {
    onRunStart();

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
        params: { model, reasoning, mockMode },
      });
    }
  };

  // Keyboard shortcut listener (Ctrl+Enter or Cmd+Enter)
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
  }, [isRunning, useFocusedMode, keyword]);

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

          {/* AI Model select */}
          <div className="space-y-2">
            <Label htmlFor="model" className="font-medium text-sm">AI Model</Label>
            <Select value={model} onValueChange={setModel}>
              <SelectTrigger id="model">
                <SelectValue placeholder="Select a model" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="gpt-4o">
                  <span className="font-medium">GPT-4o</span>
                  <span className="ml-2 text-xs text-muted-foreground">
                    Recommended
                  </span>
                </SelectItem>
                <SelectItem value="gpt-4o-mini">GPT-4o Mini (Faster)</SelectItem>
                <SelectItem value="gpt-4-turbo">GPT-4 Turbo</SelectItem>
              </SelectContent>
            </Select>
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

          {/* Advanced Settings (collapsible panel) */}
          <div className="w-full">
            {/* Header */}
            <button
              type="button"
              onClick={() => setAdvancedOpen((v) => !v)}
              aria-expanded={advancedOpen}
              className="w-full flex items-center justify-between rounded-lg border border-slate-300 bg-white
                         hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800/90 dark:hover:bg-slate-700/90
                         transition-colors px-4 py-3 text-left focus:outline-none
                         focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-slate-900"
            >
              <div className="min-w-0">
                <div className="text-sm font-semibold text-slate-900 dark:text-slate-200">
                  Advanced Settings
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 truncate">
                  Adjust reasoning depth and choose your output folder
                </div>
              </div>
              <ChevronDown
                className={cn(
                  "h-4 w-4 text-slate-400 transition-transform duration-150 flex-shrink-0 ml-3",
                  advancedOpen && "rotate-180 text-blue-400"
                )}
                aria-hidden="true"
              />
            </button>

            {/* Animated body */}
            <AnimatePresence initial={false}>
              {advancedOpen && (
                <motion.div
                  key="adv-body"
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={
                    reduceMotion
                      ? { duration: 0 }
                      : { duration: 0.22, ease: [0.22, 1, 0.36, 1] }
                  }
                  style={{ overflow: "hidden" }}
                >
                  <div className="mt-2 rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-slate-900/60
                                  divide-y divide-slate-300/50 dark:divide-slate-700/50">
                    {/* Reasoning Level */}
                    <div className="p-4 space-y-2">
                      <div>
                        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-200">
                          Reasoning Level
                        </h3>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                          High is slower but more thorough.
                        </p>
                      </div>
                      <fieldset className="flex items-center gap-4 pt-1">
                        <label className="inline-flex items-center gap-2 cursor-pointer">
                          <input
                            type="radio"
                            name="reasoning"
                            className="accent-blue-500"
                            checked={reasoning === "normal"}
                            onChange={() => setReasoning("normal")}
                          />
                          <span className="text-sm text-slate-700 dark:text-slate-300">Normal</span>
                        </label>
                        <label className="inline-flex items-center gap-2 cursor-pointer">
                          <input
                            type="radio"
                            name="reasoning"
                            className="accent-blue-500"
                            checked={reasoning === "high"}
                            onChange={() => setReasoning("high")}
                          />
                          <span className="text-sm text-slate-700 dark:text-slate-300">
                            High <span className="text-slate-500 dark:text-slate-400">(slower, more thorough)</span>
                          </span>
                        </label>
                      </fieldset>
                    </div>

                    {/* Output Folder */}
                    <div className="p-4 space-y-2">
                      <div>
                        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-200">
                          Output Folder
                        </h3>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                          Overrides the default for this run only.
                        </p>
                      </div>
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
                        <span className="text-xs text-slate-500 dark:text-slate-400 truncate">
                          {outputFolder ? (
                            <>
                              Using <span className="text-slate-700 dark:text-slate-300 font-medium">{outputFolder}</span>
                            </>
                          ) : (
                            <>
                              Using default <span className="text-slate-700 dark:text-slate-300 font-medium">/data</span>
                            </>
                          )}
                        </span>
                        {outputFolder && (
                          <button
                            type="button"
                            onClick={handleOpenOutputDir}
                            title="Open folder"
                            className="rounded-md border border-slate-300 bg-white dark:border-slate-600 dark:bg-slate-800
                                       px-2 py-2 hover:border-blue-400 dark:hover:border-blue-500 transition-colors"
                          >
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              className="h-4 w-4 text-slate-700 dark:text-slate-300"
                              fill="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path d="M19 20H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2z" />
                            </svg>
                          </button>
                        )}
                      </div>
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
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Contextual Hint */}
          <div className="text-center">
            <p className="text-xs text-slate-500 dark:text-slate-500 italic">
              Your bundle includes research, planning, generation, and packaging — all automated.
            </p>
          </div>

          {/* Generate Button */}
          <div className="relative">
            <Button
              onClick={isRunning ? undefined : handleRun}
              aria-busy={isRunning}
              aria-disabled={isRunning}
              className={cn(
                "w-full relative overflow-hidden",
                "transition-all duration-[250ms] ease-in-out",
                "focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:ring-offset-2",
                "dark:focus-visible:ring-offset-slate-900",
                // Hover state (when not running)
                !isRunning && [
                  "bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500",
                  "hover:brightness-110",
                  "hover:shadow-[0_0_12px_#2563eb80]",
                  "hover:animate-gradient-shift"
                ],
                // Active/Generating state - Amplified hover effects
                isRunning && [
                  "bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500",
                  "animate-gradient-shift",
                  "brightness-125",
                  "shadow-[0_0_24px_rgba(37,99,235,1)]",
                  "scale-[1.02]",
                  "pointer-events-none",
                  "cursor-not-allowed"
                ]
              )}
              size="lg"
            >
              {/* Pulsing inner glow when generating */}
              {isRunning && (
                <span className="absolute inset-0 bg-[radial-gradient(circle,_rgba(59,130,246,0.5)_0%,_transparent_70%)] animate-pulse rounded-lg" />
              )}

              <span className={cn(
                "relative flex items-center justify-center",
                isRunning && "text-white"
              )}>
                {isRunning ? (
                  <>
                    <Zap className="mr-2 h-4 w-4" />
                    Generating…
                  </>
                ) : (
                  <>
                    <Zap className="mr-2 h-4 w-4" />
                    Generate Bundle
                  </>
                )}
              </span>
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
