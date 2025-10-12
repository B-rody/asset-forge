import React, { useState, useEffect } from "react";
import { Package, ArrowUpDown } from "lucide-react";
import { ipcClient } from "@/lib/ipc";
import { CompletedBundleCard } from "./CompletedBundleCard";

interface CompletedBundle {
  bundle_id: string;
  idea_id: string;
  created_at: string;
  completed_at: string;
  planner_output: string;
  maker_output: string;
  packager_output: string;
  title: string;
  niche: string;
  output_path: string;
}

type SortOption = "date_desc" | "date_asc" | "title";

interface CompletedViewProps {
  onOpenFolder?: (path: string) => void;
}

export function CompletedView({ onOpenFolder }: CompletedViewProps = {}) {
  const [bundles, setBundles] = useState<CompletedBundle[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<SortOption>("date_desc");

  useEffect(() => {
    // Fetch completed bundles on mount
    const unsubscribe = ipcClient.subscribe((event) => {
      if (event.event === "completed_bundles_list") {
        setBundles(event.bundles || []);
        setLoading(false);
      }
    });

    ipcClient.sendCommand({ cmd: "get_created_bundles", params: { limit: 100 } });

    return unsubscribe;
  }, []);

  // Sort bundles
  const sortedBundles = [...bundles].sort((a, b) => {
    switch (sortBy) {
      case "date_desc":
        return new Date(b.completed_at).getTime() - new Date(a.completed_at).getTime();
      case "date_asc":
        return new Date(a.completed_at).getTime() - new Date(b.completed_at).getTime();
      case "title":
        return a.title.localeCompare(b.title);
      default:
        return 0;
    }
  });

  if (loading) {
    return (
      <div className="rounded-lg border border-border bg-card p-12 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
        <p className="mt-4 text-sm text-muted-foreground">Loading completed bundles...</p>
      </div>
    );
  }

  if (bundles.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-card p-12 text-center">
        <Package className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">No Completed Bundles Yet</h3>
        <p className="text-sm text-muted-foreground max-w-md mx-auto">
          Complete a full pipeline run (Planner → Maker → Packager) to see finished bundles here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex flex-wrap gap-3 items-center justify-between">
        {/* Sort */}
        <div className="flex items-center gap-2">
          <ArrowUpDown className="h-4 w-4 text-muted-foreground" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortOption)}
            className="text-sm border border-input bg-background rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="date_desc">Newest First</option>
            <option value="date_asc">Oldest First</option>
            <option value="title">Title (A-Z)</option>
          </select>
        </div>

        {/* Count */}
        <div className="text-sm text-muted-foreground">
          {bundles.length} {bundles.length === 1 ? 'bundle' : 'bundles'} completed
        </div>
      </div>

      {/* Bundles Grid */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {sortedBundles.map((bundle) => (
          <CompletedBundleCard key={bundle.bundle_id} bundle={bundle} onOpenFolder={onOpenFolder} />
        ))}
      </div>
    </div>
  );
}
