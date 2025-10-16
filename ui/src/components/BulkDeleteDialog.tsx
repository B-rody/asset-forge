import { useState } from "react";
import { X, Trash2, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

interface BulkDeleteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  itemType: "ideas" | "bundles" | "completed";
  selectedCount: number;
  onConfirm: () => Promise<void>;
}

export function BulkDeleteDialog({
  open,
  onOpenChange,
  itemType,
  selectedCount,
  onConfirm,
}: BulkDeleteDialogProps) {
  const [deleting, setDeleting] = useState(false);

  const getItemTypeLabel = () => {
    switch (itemType) {
      case "ideas":
        return selectedCount === 1 ? "idea" : "ideas";
      case "bundles":
        return selectedCount === 1 ? "bundle" : "bundles";
      case "completed":
        return selectedCount === 1 ? "completed bundle" : "completed bundles";
    }
  };

  const handleConfirm = async () => {
    setDeleting(true);
    try {
      await onConfirm();
      onOpenChange(false);
    } catch (error) {
      console.error("Failed to delete items:", error);
    } finally {
      setDeleting(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-background/80 backdrop-blur-sm"
        onClick={() => !deleting && onOpenChange(false)}
      />

      {/* Dialog */}
      <div className="relative z-50 w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-destructive" />
            <h2 className="text-lg font-semibold">Confirm Deletion</h2>
          </div>
          <button
            onClick={() => !deleting && onOpenChange(false)}
            disabled={deleting}
            className={cn(
              "inline-flex h-8 w-8 items-center justify-center rounded-md",
              "hover:bg-accent hover:text-accent-foreground",
              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
              "disabled:pointer-events-none disabled:opacity-50"
            )}
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Are you sure you want to delete <strong>{selectedCount}</strong>{" "}
            {getItemTypeLabel()}? This action cannot be undone.
          </p>

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => onOpenChange(false)}
              disabled={deleting}
              className={cn(
                "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium",
                "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
                "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                "disabled:pointer-events-none disabled:opacity-50"
              )}
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleConfirm}
              disabled={deleting}
              className={cn(
                "inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium",
                "bg-destructive text-destructive-foreground hover:bg-destructive/90",
                "shadow focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                "disabled:pointer-events-none disabled:opacity-50"
              )}
            >
              {deleting ? (
                <>Deleting...</>
              ) : (
                <>
                  <Trash2 className="h-4 w-4" />
                  Delete {selectedCount} {getItemTypeLabel()}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
