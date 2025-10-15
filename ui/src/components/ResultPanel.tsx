import React from "react";
import { CheckCircle2, XCircle, FolderOpen, Clock, FileText, Sparkles, Package, Lightbulb } from "lucide-react";
import { open as openPath } from "@tauri-apps/api/shell";
import { cn } from "@/lib/utils";

interface Result {
  bundle_id: string;
  bundle_title?: string;
  output_path?: string;
  file_count?: number;
  ideas_count?: number;
  store_title?: string;
  store_description?: string;
  converted_pdfs?: number;
  message?: string;
  status: "success" | "error" | "pending";
  runtime?: string;
  mode?: "research" | "auto" | "plan" | "maker" | "packager" | null;
}

interface ResultPanelProps {
  result: Result | null;
  onGenerateAssets?: (bundleId: string) => void;
  onPackageBundle?: (bundleId: string) => void;
  onNavigateToLibrary?: () => void;
}

export function ResultPanel({ result, onGenerateAssets, onPackageBundle, onNavigateToLibrary }: ResultPanelProps) {
  const handleOpenFolder = async () => {
    if (result?.output_path) {
      try {
        await openPath(result.output_path);
      } catch (error) {
        console.error("Failed to open folder:", error);
      }
    }
  };

  if (!result) {
    return (
      <div className="rounded-lg border border-border bg-card p-6">
        <h2 className="mb-4 text-lg font-semibold">Results</h2>
        <div className="text-sm text-muted-foreground">
          <p>Once your bundle is ready, it will appear here with next actions.</p>
        </div>
      </div>
    );
  }

  // Get appropriate icon and title based on mode
  const getModeInfo = () => {
    switch (result.mode) {
      case "research":
        return { icon: Lightbulb, title: "Research Complete", color: "text-blue-600 dark:text-blue-400" };
      case "plan":
        return { icon: Sparkles, title: "Bundle Plan Created", color: "text-purple-600 dark:text-purple-400" };
      case "maker":
        return { icon: FileText, title: "Assets Generated", color: "text-green-600 dark:text-green-400" };
      case "packager":
        return { icon: Package, title: "Bundle Packaged", color: "text-orange-600 dark:text-orange-400" };
      default:
        return { icon: CheckCircle2, title: "Complete", color: "text-green-600 dark:text-green-400" };
    }
  };

  const modeInfo = getModeInfo();
  const ModeIcon = result.status === "error" ? XCircle : modeInfo.icon;

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <h2 className="mb-4 text-lg font-semibold">Results</h2>

      <div className="space-y-4">
        {/* Status Header */}
        <div className="flex items-start gap-4">
          {result.status === "success" ? (
            <ModeIcon className={cn("h-6 w-6 mt-1", modeInfo.color)} />
          ) : (
            <XCircle className="h-6 w-6 text-destructive mt-1" />
          )}

          <div className="flex-1">
            <h3 className="font-semibold text-base">
              {result.status === "success" ? modeInfo.title : "Pipeline Failed"}
            </h3>
            <p className="text-sm text-muted-foreground mt-1">
              {result.message || (result.status === "error" ? "An error occurred during execution" : "Completed successfully")}
            </p>

            {/* Bundle Title */}
            {result.bundle_title && (
              <p className="text-sm font-medium mt-2">{result.bundle_title}</p>
            )}

            {/* Stats Row */}
            <div className="flex items-center gap-4 mt-3 text-sm text-muted-foreground">
              {result.runtime && (
                <div className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  <span>{result.runtime}</span>
                </div>
              )}
              {result.file_count !== undefined && (
                <div className="flex items-center gap-1">
                  <FileText className="h-4 w-4" />
                  <span>{result.file_count} {result.file_count === 1 ? 'file' : 'files'}</span>
                </div>
              )}
              {result.ideas_count !== undefined && (
                <div className="flex items-center gap-1">
                  <Lightbulb className="h-4 w-4" />
                  <span>{result.ideas_count} {result.ideas_count === 1 ? 'idea' : 'ideas'}</span>
                </div>
              )}
              {result.converted_pdfs !== undefined && (
                <div className="flex items-center gap-1">
                  <Package className="h-4 w-4" />
                  <span>{result.converted_pdfs} PDF{result.converted_pdfs !== 1 ? 's' : ''} converted</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Action Buttons - Context-Aware */}
        {result.status === "success" && (
          <div className="space-y-2">
            {/* Research Mode: View Ideas */}
            {result.mode === "research" && onNavigateToLibrary && (
              <button
                onClick={onNavigateToLibrary}
                className={cn(
                  "w-full flex items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium",
                  "bg-blue-600 text-white shadow hover:bg-blue-700",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500",
                  "transition-colors"
                )}
              >
                <Lightbulb className="h-4 w-4" />
                View Ideas in Library
              </button>
            )}

            {/* Planner Mode: View Bundle Plan + Generate Assets */}
            {result.mode === "plan" && (
              <div className="space-y-2">
                {onNavigateToLibrary && (
                  <button
                    onClick={onNavigateToLibrary}
                    className={cn(
                      "w-full flex items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium",
                      "border-2 border-purple-600 text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-950/30",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500",
                      "transition-colors"
                    )}
                  >
                    <Package className="h-4 w-4" />
                    View Bundle Plan
                  </button>
                )}
                {onGenerateAssets && result.bundle_id && (
                  <button
                    onClick={() => onGenerateAssets(result.bundle_id)}
                    className={cn(
                      "w-full flex items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium",
                      "bg-purple-600 text-white shadow hover:bg-purple-700",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500",
                      "transition-colors"
                    )}
                  >
                    <Sparkles className="h-4 w-4" />
                    Generate Assets
                  </button>
                )}
              </div>
            )}

            {/* Maker Mode: View Assets + Package Bundle */}
            {result.mode === "maker" && (
              <div className="space-y-2">
                {result.output_path && (
                  <button
                    onClick={handleOpenFolder}
                    className={cn(
                      "w-full flex items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium",
                      "border-2 border-green-600 text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-950/30",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green-500",
                      "transition-colors"
                    )}
                  >
                    <FolderOpen className="h-4 w-4" />
                    View Assets in Explorer
                  </button>
                )}
                {onPackageBundle && result.bundle_id && (
                  <button
                    onClick={() => onPackageBundle(result.bundle_id)}
                    className={cn(
                      "w-full flex items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium",
                      "bg-green-600 text-white shadow hover:bg-green-700",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green-500",
                      "transition-colors"
                    )}
                  >
                    <Package className="h-4 w-4" />
                    Package Bundle
                  </button>
                )}
              </div>
            )}

            {/* Packager Mode: Open in Explorer */}
            {result.mode === "packager" && result.output_path && (
              <button
                onClick={handleOpenFolder}
                className={cn(
                  "w-full flex items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium",
                  "bg-orange-600 text-white shadow hover:bg-orange-700",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500",
                  "transition-colors"
                )}
              >
                <FolderOpen className="h-4 w-4" />
                Open in Explorer
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
