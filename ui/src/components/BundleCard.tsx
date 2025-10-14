import React, { useState } from "react";
import { Package, CheckCircle2, XCircle, Clock, ChevronRight, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
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
}

// Helper to determine display status based on workflow state
function getDisplayStatus(current_step: string, status: string) {
  if (status === "failed") {
    return {
      label: "Failed",
      color: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 border-red-200 dark:border-red-800",
      icon: <XCircle className="h-3 w-3" />
    };
  }

  if (status === "pending") {
    return {
      label: "Pending",
      color: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400 border-yellow-200 dark:border-yellow-800",
      icon: <Clock className="h-3 w-3" />
    };
  }

  // Completed states - distinguish by current_step
  if (current_step === "planner" && status === "completed") {
    return {
      label: "Ready to Make",
      color: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 border-blue-200 dark:border-blue-800",
      icon: <Sparkles className="h-3 w-3" />
    };
  }

  if (current_step === "maker" && status === "completed") {
    return {
      label: "Ready to Package",
      color: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400 border-orange-200 dark:border-orange-800",
      icon: <Package className="h-3 w-3" />
    };
  }

  // Default fallback
  return {
    label: "In Progress",
    color: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400 border-yellow-200 dark:border-yellow-800",
    icon: <Clock className="h-3 w-3" />
  };
}

export function BundleCard({ bundle, onGenerateAssets, onPackageBundle }: BundleCardProps) {
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

        {/* Step and Date */}
        <div className="mb-3">
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
      />
    </>
  );
}
