import { useState, useEffect } from "react";
import { X, FolderOpen, Copy, CheckCircle2, FileText, DollarSign, Package, Trash2, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

interface CompletedBundleDetailsDialogProps {
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
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onOpenFolder?: (path: string) => void;
  onDelete?: (bundleId: string) => Promise<void>;
}

export function CompletedBundleDetailsDialog({ bundle, open, onOpenChange, onOpenFolder, onDelete }: CompletedBundleDetailsDialogProps) {
  const [copied, setCopied] = useState(false);
  const [pendingDelete, setPendingDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Reset state when dialog opens/closes
  useEffect(() => {
    if (open) {
      setPendingDelete(false);
      setDeleting(false);
      setCopied(false);
    }
  }, [open]);

  if (!open) return null;

  // Parse all outputs
  let plannerData: any = {};
  let makerData: any = {};
  let packagerData: any = {};

  try {
    plannerData = JSON.parse(bundle.planner_output);
  } catch (e) {
    console.error("Failed to parse planner output:", e);
  }

  try {
    makerData = JSON.parse(bundle.maker_output);
  } catch (e) {
    console.error("Failed to parse maker output:", e);
  }

  try {
    packagerData = JSON.parse(bundle.packager_output);
  } catch (e) {
    console.error("Failed to parse packager output:", e);
  }

  const handleCopyPath = () => {
    navigator.clipboard.writeText(bundle.output_path);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleOpenFolder = () => {
    if (onOpenFolder) {
      onOpenFolder(bundle.output_path);
    }
  };

  const handleDeleteClick = () => {
    setPendingDelete(true);
  };

  const handleConfirmDelete = async () => {
    if (onDelete && pendingDelete) {
      setDeleting(true);
      try {
        await onDelete(bundle.bundle_id);
        onOpenChange(false); // Close dialog after successful deletion
      } catch (error) {
        console.error("Failed to delete completed bundle:", error);
        setDeleting(false);
        setPendingDelete(false);
      }
    }
  };

  // Calculate duration
  const startTime = new Date(bundle.created_at).getTime();
  const endTime = new Date(bundle.completed_at).getTime();
  const durationMinutes = Math.round((endTime - startTime) / 1000 / 60);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={() => onOpenChange(false)}>
      <div
        className="bg-white dark:bg-slate-900 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-border">
          <div className="flex-1 pr-4">
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-xl font-semibold">{bundle.title}</h2>
              <span className="px-2.5 py-0.5 text-xs font-bold rounded-full bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 flex items-center gap-1.5">
                <CheckCircle2 className="h-3 w-3" />
                Completed
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              {bundle.niche} • Completed {new Date(bundle.completed_at).toLocaleDateString()} • {durationMinutes}m
            </p>
          </div>
          <button
            onClick={() => onOpenChange(false)}
            className="p-2 hover:bg-accent rounded-md transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Output Path */}
          <div className="rounded-lg border border-border bg-muted/30 p-4">
            <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
              <FolderOpen className="h-4 w-4" />
              Output Location
            </h3>
            <div className="flex items-center gap-2">
              <code className="flex-1 text-xs bg-background px-3 py-2 rounded border border-border overflow-x-auto">
                {bundle.output_path}
              </code>
              <button
                onClick={handleCopyPath}
                className="p-2 hover:bg-accent rounded transition-colors"
                title="Copy path"
              >
                {copied ? (
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>

          {/* Description */}
          {plannerData.description && (
            <div>
              <h3 className="text-sm font-semibold mb-2">Description</h3>
              <p className="text-sm text-muted-foreground">{plannerData.description}</p>
            </div>
          )}

          {/* Assets */}
          {makerData.assets && makerData.assets.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Generated Assets ({makerData.assets.length})
              </h3>
              <div className="space-y-2">
                {makerData.assets.map((asset: any, i: number) => (
                  <div key={i} className="rounded-lg border border-border p-3 hover:bg-accent/50 transition-colors">
                    <div className="flex items-start justify-between mb-1">
                      <h4 className="text-sm font-medium">{asset.name || asset.asset_id}</h4>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                        {asset.format || asset.type}
                      </span>
                    </div>
                    {asset.file_path && (
                      <p className="text-xs text-muted-foreground font-mono">{asset.file_path}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Pricing */}
          {plannerData.pricing && (
            <div>
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <DollarSign className="h-4 w-4" />
                Pricing
              </h3>
              <div className="rounded-lg border border-border p-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-xs font-medium text-muted-foreground block mb-1">Strategy</span>
                    <p className="text-sm font-semibold capitalize">{plannerData.pricing.strategy}</p>
                  </div>
                  <div>
                    <span className="text-xs font-medium text-muted-foreground block mb-1">Recommended Price</span>
                    <p className="text-sm font-semibold">${plannerData.pricing.recommended_price_usd}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Package Summary */}
          {packagerData.bundle_summary && (
            <div>
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Package className="h-4 w-4" />
                Package Summary
              </h3>
              <div className="rounded-lg border border-border p-4 bg-muted/30">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  {packagerData.bundle_summary.total_files && (
                    <div>
                      <span className="text-xs font-medium text-muted-foreground block mb-1">Total Files</span>
                      <p className="font-semibold">{packagerData.bundle_summary.total_files}</p>
                    </div>
                  )}
                  {packagerData.bundle_summary.bundle_size_mb && (
                    <div>
                      <span className="text-xs font-medium text-muted-foreground block mb-1">Bundle Size</span>
                      <p className="font-semibold">{packagerData.bundle_summary.bundle_size_mb} MB</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-border p-4">
          {/* Warning message when pending delete */}
          {pendingDelete && (
            <div className="mb-3 flex items-center gap-2 rounded-md border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
              <AlertTriangle className="h-4 w-4 flex-shrink-0" />
              <span>Are you sure you want to delete this completed bundle? This action cannot be undone.</span>
            </div>
          )}

          <div className="flex justify-between items-center">
            <div className="flex gap-2">
              <button
                onClick={() => onOpenChange(false)}
                disabled={deleting}
                className={cn(
                  "px-4 py-2 text-sm font-medium rounded-md border border-border hover:bg-accent transition-colors",
                  "disabled:pointer-events-none disabled:opacity-50"
                )}
              >
                Close
              </button>
              {onDelete && !pendingDelete && (
                <button
                  onClick={handleDeleteClick}
                  disabled={deleting}
                  className={cn(
                    "px-3 py-2 text-sm font-medium rounded-md border border-border hover:bg-destructive/10 hover:border-destructive transition-colors",
                    "flex items-center gap-2 disabled:pointer-events-none disabled:opacity-50"
                  )}
                  title="Delete completed bundle"
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                  <span className="text-destructive">Delete</span>
                </button>
              )}
              {onDelete && pendingDelete && (
                <button
                  onClick={handleConfirmDelete}
                  disabled={deleting}
                  className={cn(
                    "px-4 py-2 text-sm font-medium rounded-md bg-destructive text-destructive-foreground hover:bg-destructive/90 transition-colors shadow",
                    "flex items-center gap-2 disabled:pointer-events-none disabled:opacity-50"
                  )}
                >
                  <Trash2 className="h-4 w-4" />
                  {deleting ? "Deleting..." : "Confirm Delete"}
                </button>
              )}
            </div>
            {!pendingDelete && (
              <button
                onClick={handleOpenFolder}
                disabled={deleting}
                className={cn(
                  "px-4 py-2 text-sm font-medium rounded-md bg-primary text-white hover:bg-primary/80 transition-all hover:shadow-md",
                  "flex items-center gap-2 disabled:pointer-events-none disabled:opacity-50"
                )}
              >
                <FolderOpen className="h-4 w-4" />
                Open Folder
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
