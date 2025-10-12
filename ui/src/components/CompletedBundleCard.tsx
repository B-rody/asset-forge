import React, { useState } from "react";
import { Package, FolderOpen, ChevronRight, Calendar } from "lucide-react";
import { cn } from "@/lib/utils";
import { CompletedBundleDetailsDialog } from "./CompletedBundleDetailsDialog";

interface CompletedBundleCardProps {
  bundle: {
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
  };
  onOpenFolder?: (path: string) => void;
}

export function CompletedBundleCard({ bundle, onOpenFolder }: CompletedBundleCardProps) {
  const [showDetails, setShowDetails] = useState(false);

  const handleOpenFolder = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent dialog from opening
    if (onOpenFolder) {
      onOpenFolder(bundle.output_path);
    }
  };

  // Calculate duration
  const startTime = new Date(bundle.created_at).getTime();
  const endTime = new Date(bundle.completed_at).getTime();
  const durationMinutes = Math.round((endTime - startTime) / 1000 / 60);

  // Format completed date
  const completedDate = new Date(bundle.completed_at).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });

  // Parse asset count from maker output
  let assetCount = 0;
  try {
    const makerData = JSON.parse(bundle.maker_output);
    assetCount = makerData.assets?.length || 0;
  } catch (e) {
    // Ignore parsing errors
  }

  return (
    <>
      <div className="rounded-lg border border-border bg-card hover:shadow-md hover:border-primary/50 transition-all duration-200 overflow-hidden">
        {/* Clickable card area */}
        <button
          onClick={() => setShowDetails(true)}
          className="w-full text-left p-4 focus:outline-none focus:ring-2 focus:ring-ring"
        >
          {/* Header */}
          <div className="flex items-start gap-2 mb-3">
            <Package className="h-5 w-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-sm leading-tight line-clamp-2 mb-1">
                {bundle.title}
              </h3>
              <p className="text-xs text-muted-foreground">
                {bundle.niche}
              </p>
            </div>
          </div>

          {/* Metadata */}
          <div className="space-y-2 mb-3">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Calendar className="h-3 w-3" />
              <span>{completedDate}</span>
            </div>
            <div className="flex gap-3 text-xs text-muted-foreground">
              <span>{assetCount} assets</span>
              <span>•</span>
              <span>{durationMinutes}m to complete</span>
            </div>
          </div>

          {/* Footer - View Details */}
          <div className="flex items-center justify-end gap-1 text-xs text-muted-foreground group-hover:text-foreground">
            <span>View Details</span>
            <ChevronRight className="h-3 w-3" />
          </div>
        </button>

        {/* Action bar */}
        <div className="border-t border-border bg-muted/30 px-4 py-2">
          <button
            onClick={handleOpenFolder}
            className={cn(
              "flex items-center gap-2 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
            )}
          >
            <FolderOpen className="h-3.5 w-3.5" />
            Open Folder
          </button>
        </div>
      </div>

      {/* Details Dialog */}
      <CompletedBundleDetailsDialog
        bundle={bundle}
        open={showDetails}
        onOpenChange={setShowDetails}
        onOpenFolder={onOpenFolder}
      />
    </>
  );
}
