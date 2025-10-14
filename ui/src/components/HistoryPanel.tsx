import React, { useState } from "react";
import { History, Activity, Package } from "lucide-react";
import { cn } from "@/lib/utils";
import { ActivityLogView } from "./ActivityLogView";
import { CompletedView } from "./CompletedView";

type HistoryTab = "activity" | "completed";

interface HistoryPanelProps {
  onOpenFolder?: (path: string) => void;
}

export function HistoryPanel({ onOpenFolder }: HistoryPanelProps) {
  const [activeTab, setActiveTab] = useState<HistoryTab>("completed");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-xl border border-border bg-gradient-to-b from-white to-slate-50 dark:from-slate-900 dark:to-slate-950 p-6 shadow-sm hover:shadow-md transition-shadow duration-200 border-l-4 border-l-primary">
        <div className="flex items-center gap-3 mb-4">
          <History className="h-6 w-6 text-primary" />
          <div>
            <h2 className="text-lg md:text-xl font-semibold">History</h2>
            <p className="text-sm text-muted-foreground/90">
              Pipeline activity logs and completed bundles ready to sell
            </p>
          </div>
        </div>

        {/* Sub-tabs */}
        <div className="flex gap-2 mt-4 border-b border-border">
          <button
            onClick={() => setActiveTab("completed")}
            className={cn(
              "flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-t-md transition-colors",
              "hover:bg-accent hover:text-accent-foreground",
              activeTab === "completed" && "bg-primary text-primary-foreground"
            )}
          >
            <Package className="h-4 w-4" />
            Completed
          </button>
          <button
            onClick={() => setActiveTab("activity")}
            className={cn(
              "flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-t-md transition-colors",
              "hover:bg-accent hover:text-accent-foreground",
              activeTab === "activity" && "bg-primary text-primary-foreground"
            )}
          >
            <Activity className="h-4 w-4" />
            Activity
          </button>
        </div>
      </div>

      {/* Content */}
      <div>
        {activeTab === "completed" && <CompletedView onOpenFolder={onOpenFolder} />}
        {activeTab === "activity" && <ActivityLogView />}
      </div>
    </div>
  );
}
