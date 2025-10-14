import React, { useState, useEffect } from "react";
import { Package, Filter, ArrowUpDown } from "lucide-react";
import { ipcClient } from "@/lib/ipc";
import { BundleCard } from "./BundleCard";
import { cn } from "@/lib/utils";

interface Bundle {
  bundle_id: string;
  idea_id: string;
  created_at: string;
  updated_at: string;
  current_step: string;
  status: string;
  error_message: string | null;
  planner_output: string;
}

type SortOption = "date_desc" | "date_asc" | "status";
type FilterOption = "all" | "completed" | "failed" | "pending";

interface BundlesViewProps {
  fetchCommand?: string;  // Command to fetch bundles (defaults to "get_bundles")
  eventName?: string;     // Event name to listen for (defaults to "bundles_list")
  onGenerateAssets?: (bundleId: string) => void;
  onPackageBundle?: (bundleId: string) => void;
}

export function BundlesView({
  fetchCommand = "get_bundles",
  eventName = "bundles_list",
  onGenerateAssets,
  onPackageBundle
}: BundlesViewProps) {
  const [bundles, setBundles] = useState<Bundle[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<SortOption>("date_desc");
  const [filterStatus, setFilterStatus] = useState<FilterOption>("all");

  useEffect(() => {
    // Fetch bundles on mount
    const unsubscribe = ipcClient.subscribe((event) => {
      // Listen for the specified event name
      if (event.event === eventName ||
          event.event === "bundles_list" ||
          event.event === "ready_bundles_list" ||
          event.event === "generated_bundles_list") {
        setBundles(event.bundles || []);
        setLoading(false);
      }
    });

    ipcClient.sendCommand({ cmd: fetchCommand, params: { limit: 100 } });

    return unsubscribe;
  }, [fetchCommand, eventName]);

  // Filter bundles by status
  const filteredBundles = bundles.filter((bundle) => {
    if (filterStatus === "all") return true;
    return bundle.status === filterStatus;
  });

  // Sort bundles
  const sortedBundles = [...filteredBundles].sort((a, b) => {
    switch (sortBy) {
      case "date_desc":
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      case "date_asc":
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      case "status":
        const statusOrder = { completed: 1, pending: 2, failed: 3 };
        return statusOrder[a.status as keyof typeof statusOrder] - statusOrder[b.status as keyof typeof statusOrder];
      default:
        return 0;
    }
  });

  if (loading) {
    return (
      <div className="rounded-lg border border-border bg-card p-12 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
        <p className="mt-4 text-sm text-muted-foreground">Loading bundles...</p>
      </div>
    );
  }

  if (bundles.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-card p-12 text-center">
        <Package className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">No Bundles Yet</h3>
        <p className="text-sm text-muted-foreground max-w-md mx-auto">
          Create a bundle plan from an idea in the Ideas tab. Completed plans will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex flex-wrap gap-3">
        {/* Status Filter */}
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as FilterOption)}
            className="text-sm border border-input bg-background rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="all">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="pending">Pending</option>
            <option value="failed">Failed</option>
          </select>
        </div>

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
            <option value="status">By Status</option>
          </select>
        </div>

        {/* Count */}
        <div className="ml-auto text-sm text-muted-foreground">
          Showing {sortedBundles.length} of {bundles.length} bundles
        </div>
      </div>

      {/* Bundles Grid */}
      {sortedBundles.length === 0 ? (
        <div className="rounded-lg border border-border bg-card p-8 text-center">
          <p className="text-sm text-muted-foreground">
            No bundles match the selected filter.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {sortedBundles.map((bundle) => (
            <BundleCard
              key={bundle.bundle_id}
              bundle={bundle}
              onGenerateAssets={onGenerateAssets}
              onPackageBundle={onPackageBundle}
            />
          ))}
        </div>
      )}
    </div>
  );
}
