import React, { useState } from "react";
import { Package, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { getDisplayStatus } from "@/lib/bundle-status";
import { BundleDetailsDialog } from "./BundleDetailsDialog";

interface BundleCardProps {
  bundle: {
    bundle_id: string;
    idea_id: string;
    created_at: string;
    updated_at: string;
    current_step: string;
    status: string;
    error_message: string | null;
    planner_output: string;
  };
  onGenerateAssets?: (bundleId: string) => void;
  onPackageBundle?: (bundleId: string) => void;
  onDelete?: (bundleId: string) => Promise<void>;
}

export function BundleCard({ bundle, onGenerateAssets, onPackageBundle, onDelete }: BundleCardProps) {
  const [showDetails, setShowDetails] = useState(false);

  // Parse title from planner_output
  let title = "Untitled Bundle";
  try {
    const plannerData = JSON.parse(bundle.planner_output);
    title = plannerData.title || title;
  } catch (e) {
    // Keep default title if parsing fails
  }

  // Get display status based on workflow state
  const displayStatus = getDisplayStatus(bundle.current_step, bundle.status);
  const statusLabel = displayStatus.label;
  const statusColor = displayStatus.color;
  const statusIcon = displayStatus.icon;

  // Format date
  const formattedDate = new Date(bundle.created_at).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });

  return (
    <>
      <button
        onClick={() => setShowDetails(true)}
        className={cn(
          "w-full text-left rounded-lg border border-border bg-card p-4",
          "hover:shadow-md hover:border-primary/50 transition-all duration-200",
          "focus:outline-none focus:ring-2 focus:ring-ring"
        )}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="flex items-start gap-2 flex-1 min-w-0">
            <Package className="h-5 w-5 text-purple-600 dark:text-purple-400 flex-shrink-0 mt-0.5" />
            <h3 className="font-semibold text-sm leading-tight line-clamp-2">
              {title}
            </h3>
          </div>
          <span
            className={cn(
              "px-2 py-0.5 text-xs font-bold rounded-full border flex-shrink-0 flex items-center gap-1",
              statusColor
            )}
          >
            {statusIcon}
            {statusLabel}
          </span>
        </div>

        {/* Bundle ID, Step and Date */}
        <div className="mb-3">
          <p className="text-xs text-muted-foreground">
            {bundle.bundle_id}
          </p>
          <p className="text-xs text-muted-foreground">
            Step: {bundle.current_step.charAt(0).toUpperCase() + bundle.current_step.slice(1)} • {formattedDate}
          </p>
        </div>

        {/* Error message if failed */}
        {bundle.status === 'failed' && bundle.error_message && (
          <div className="mb-3 p-2 bg-red-50 dark:bg-red-900/20 rounded text-xs text-red-600 dark:text-red-400 line-clamp-2">
            {bundle.error_message}
          </div>
        )}

        {/* View Details */}
        <div className="flex items-center justify-end gap-1 text-xs text-muted-foreground group-hover:text-foreground">
          <span>View Details</span>
          <ChevronRight className="h-3 w-3" />
        </div>
      </button>

      {/* Details Dialog */}
      <BundleDetailsDialog
        bundle={bundle}
        open={showDetails}
        onOpenChange={setShowDetails}
        onGenerateAssets={onGenerateAssets}
        onPackageBundle={onPackageBundle}
        onDelete={onDelete}
      />
    </>
  );
}
