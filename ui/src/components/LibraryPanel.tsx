import React, { useState, useEffect } from "react";
import { Database, Lightbulb, Package } from "lucide-react";
import { ipcClient } from "@/lib/ipc";
import { cn } from "@/lib/utils";
import { IdeasView } from "./IdeasView";
import { BundlesView } from "./BundlesView";

type LibraryTab = "ideas" | "bundles";

interface LibraryStats {
  ideas_count: number;
  bundles_count: number;
}

interface LibraryPanelProps {
  onBuildBundle?: (ideaId: string) => void;
  onGenerateAssets?: (bundleId: string) => void;
}

export function LibraryPanel({ onBuildBundle, onGenerateAssets }: LibraryPanelProps) {
  const [activeTab, setActiveTab] = useState<LibraryTab>("ideas");
  const [stats, setStats] = useState<LibraryStats>({ ideas_count: 0, bundles_count: 0 });

  useEffect(() => {
    // Fetch library stats on mount
    const unsubscribe = ipcClient.subscribe((event) => {
      if (event.event === "library_stats") {
        setStats(event.stats as LibraryStats);
      }
    });

    // Request stats
    ipcClient.sendCommand({ cmd: "get_library_stats" });

    return unsubscribe;
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-xl border border-border bg-gradient-to-b from-white to-slate-50 dark:from-slate-900 dark:to-slate-950 p-6 shadow-sm hover:shadow-md transition-shadow duration-200 border-l-4 border-l-primary">
        <div className="flex items-center gap-3 mb-4">
          <Database className="h-6 w-6 text-primary" />
          <div>
            <h2 className="text-lg md:text-xl font-semibold">Library</h2>
            <p className="text-sm text-muted-foreground/90">
              Active inventory - ideas and bundles waiting to be processed
            </p>
          </div>
        </div>

        {/* Stats Bar */}
        <div className="flex gap-4 mt-4 p-4 bg-slate-100 dark:bg-slate-800/50 rounded-lg">
          <div className="flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            <span className="text-sm font-medium">
              {stats.ideas_count} {stats.ideas_count === 1 ? 'Idea' : 'Ideas'} Available
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Package className="h-4 w-4 text-purple-600 dark:text-purple-400" />
            <span className="text-sm font-medium">
              {stats.bundles_count} {stats.bundles_count === 1 ? 'Bundle' : 'Bundles'}
            </span>
          </div>
        </div>

        {/* Sub-tabs */}
        <div className="flex gap-2 mt-4 border-b border-border">
          <button
            onClick={() => setActiveTab("ideas")}
            className={cn(
              "flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-t-md transition-colors",
              "hover:bg-accent hover:text-accent-foreground",
              activeTab === "ideas" && "bg-primary text-primary-foreground"
            )}
          >
            <Lightbulb className="h-4 w-4" />
            Ideas
          </button>
          <button
            onClick={() => setActiveTab("bundles")}
            className={cn(
              "flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-t-md transition-colors",
              "hover:bg-accent hover:text-accent-foreground",
              activeTab === "bundles" && "bg-primary text-primary-foreground"
            )}
          >
            <Package className="h-4 w-4" />
            Bundles
          </button>
        </div>
      </div>

      {/* Content */}
      <div>
        {activeTab === "ideas" && <IdeasView onBuildBundle={onBuildBundle} />}
        {activeTab === "bundles" && <BundlesView onGenerateAssets={onGenerateAssets} />}
      </div>
    </div>
  );
}
