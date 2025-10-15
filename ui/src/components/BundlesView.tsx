import React, { useState, useEffect } from "react";
import { Package, Filter, ArrowUpDown, CheckSquare, Trash2 } from "lucide-react";
import { ipcClient } from "@/lib/ipc";
import { BundleCard } from "./BundleCard";
import { BulkDeleteDialog } from "./BulkDeleteDialog";
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
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  useEffect(() => {
    // Fetch bundles on mount and listen for deletion events
    const unsubscribe = ipcClient.subscribe((event) => {
      // Listen for the specified event name
      if (event.event === eventName ||
          event.event === "bundles_list" ||
          event.event === "ready_bundles_list" ||
          event.event === "generated_bundles_list") {
        setBundles(event.bundles || []);
        setLoading(false);
      } else if (event.event === "bundle_deleted" && event.success) {
        // Remove deleted bundle from list
        setBundles((prev) => prev.filter((bundle) => bundle.bundle_id !== event.bundle_id));
        setSelectedIds((prev) => {
          const newSet = new Set(prev);
          newSet.delete(event.bundle_id);
          return newSet;
        });
      }
    });

    ipcClient.sendCommand({ cmd: fetchCommand, params: { limit: 100 } });

    return unsubscribe;
  }, [fetchCommand, eventName]);

  const toggleSelectionMode = () => {
    setSelectionMode(!selectionMode);
    setSelectedIds(new Set());
  };

  const toggleSelectBundle = (bundleId: string) => {
    setSelectedIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(bundleId)) {
        newSet.delete(bundleId);
      } else {
        newSet.add(bundleId);
      }
      return newSet;
    });
  };

  const selectAll = () => {
    setSelectedIds(new Set(sortedBundles.map((bundle) => bundle.bundle_id)));
  };

  const deselectAll = () => {
    setSelectedIds(new Set());
  };

  const handleBulkDelete = async () => {
    // Delete each selected bundle sequentially
    for (const bundleId of selectedIds) {
      try {
        await ipcClient.sendCommand({
          cmd: "delete_bundle",
          params: { bundle_id: bundleId },
        });
      } catch (error) {
        console.error(`Failed to delete bundle ${bundleId}:`, error);
      }
    }

    // Exit selection mode after deletion
    setSelectionMode(false);
    setSelectedIds(new Set());
  };

  const handleSingleDelete = async (bundleId: string) => {
    try {
      await ipcClient.sendCommand({
        cmd: "delete_bundle",
        params: { bundle_id: bundleId },
      });
    } catch (error) {
      console.error(`Failed to delete bundle ${bundleId}:`, error);
      throw error;
    }
  };

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
      <div className="flex flex-wrap gap-3 items-center">
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

        {/* Selection Mode Button */}
        <button
          onClick={toggleSelectionMode}
          className={cn(
            "flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md border transition-colors",
            selectionMode
              ? "bg-primary text-primary-foreground border-primary"
              : "bg-background text-foreground border-input hover:bg-accent"
          )}
        >
          <CheckSquare className="h-4 w-4" />
          {selectionMode ? "Cancel" : "Select"}
        </button>

        {/* Count */}
        <div className="ml-auto text-sm text-muted-foreground">
          {selectionMode && selectedIds.size > 0 ? (
            <span>{selectedIds.size} selected</span>
          ) : (
            <span>Showing {sortedBundles.length} of {bundles.length} bundles</span>
          )}
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
            <div key={bundle.bundle_id} className="relative">
              {selectionMode ? (
                <div
                  onClick={() => toggleSelectBundle(bundle.bundle_id)}
                  className="cursor-pointer"
                >
                  <div className="absolute top-2 left-2 z-10 pointer-events-none">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(bundle.bundle_id)}
                      onChange={() => {}}
                      className="h-5 w-5 rounded border-border pointer-events-none"
                    />
                  </div>
                  <div className="pointer-events-none">
                    <BundleCard
                      bundle={bundle}
                      onGenerateAssets={undefined}
                      onPackageBundle={undefined}
                      onDelete={undefined}
                    />
                  </div>
                </div>
              ) : (
                <BundleCard
                  bundle={bundle}
                  onGenerateAssets={onGenerateAssets}
                  onPackageBundle={onPackageBundle}
                  onDelete={handleSingleDelete}
                />
              )}
            </div>
          ))}
        </div>
      )}

      {/* Floating Action Bar */}
      {selectionMode && selectedIds.size > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-card border border-border rounded-lg shadow-lg p-4 flex items-center gap-4">
          <span className="text-sm font-medium">
            {selectedIds.size} bundle{selectedIds.size !== 1 ? "s" : ""} selected
          </span>
          <div className="flex gap-2">
            <button
              onClick={selectAll}
              className="px-3 py-1.5 text-sm font-medium rounded-md border border-input bg-background hover:bg-accent transition-colors"
            >
              Select All
            </button>
            <button
              onClick={deselectAll}
              className="px-3 py-1.5 text-sm font-medium rounded-md border border-input bg-background hover:bg-accent transition-colors"
            >
              Deselect All
            </button>
            <button
              onClick={() => setShowDeleteDialog(true)}
              className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md bg-destructive text-destructive-foreground hover:bg-destructive/90 transition-colors shadow"
            >
              <Trash2 className="h-4 w-4" />
              Delete
            </button>
          </div>
        </div>
      )}

      {/* Bulk Delete Dialog */}
      <BulkDeleteDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        itemType="bundles"
        selectedCount={selectedIds.size}
        onConfirm={handleBulkDelete}
      />
    </div>
  );
}
