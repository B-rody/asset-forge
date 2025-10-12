import React from "react";
import { X, Package, DollarSign, Tag, FileText, CheckCircle2, XCircle, Clock, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

interface BundleDetailsDialogProps {
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
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onGenerateAssets?: (bundleId: string) => void;
}

export function BundleDetailsDialog({ bundle, open, onOpenChange, onGenerateAssets }: BundleDetailsDialogProps) {
  if (!open) return null;

  const handleGenerateAssets = () => {
    if (onGenerateAssets) {
      onGenerateAssets(bundle.bundle_id);
      onOpenChange(false); // Close dialog after starting generation
    }
  };

  // Parse planner output
  let plannerData: any = {};
  try {
    plannerData = JSON.parse(bundle.planner_output);
  } catch (e) {
    console.error("Failed to parse planner output:", e);
  }

  // Status colors
  const statusColors = {
    completed: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    failed: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
    pending: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
  };

  const statusIcons = {
    completed: <CheckCircle2 className="h-4 w-4" />,
    failed: <XCircle className="h-4 w-4" />,
    pending: <Clock className="h-4 w-4" />,
  };

  const statusLabel = bundle.status.charAt(0).toUpperCase() + bundle.status.slice(1);
  const statusColor = statusColors[bundle.status as keyof typeof statusColors] || statusColors.pending;
  const statusIcon = statusIcons[bundle.status as keyof typeof statusIcons] || statusIcons.pending;

  // Can generate assets if status is completed and current step is planner
  const canGenerateAssets = bundle.status === 'completed' && bundle.current_step === 'planner';

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
              <h2 className="text-xl font-semibold">{plannerData.title || "Untitled Bundle"}</h2>
              <span
                className={cn(
                  "px-2.5 py-0.5 text-xs font-bold rounded-full flex items-center gap-1.5",
                  statusColor
                )}
              >
                {statusIcon}
                {statusLabel}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              Step: {bundle.current_step.charAt(0).toUpperCase() + bundle.current_step.slice(1)}
              {' • '}
              Created: {new Date(bundle.created_at).toLocaleDateString()}
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
          {/* Error Message */}
          {bundle.status === 'failed' && bundle.error_message && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
              <h3 className="text-sm font-semibold text-red-800 dark:text-red-400 mb-2 flex items-center gap-2">
                <XCircle className="h-4 w-4" />
                Error
              </h3>
              <p className="text-sm text-red-600 dark:text-red-400">{bundle.error_message}</p>
            </div>
          )}

          {/* Description */}
          {plannerData.description && (
            <div>
              <h3 className="text-sm font-semibold mb-2">Description</h3>
              <p className="text-sm text-muted-foreground">{plannerData.description}</p>
            </div>
          )}

          {/* One-liner */}
          {plannerData.one_liner && (
            <div>
              <h3 className="text-sm font-semibold mb-2">One-Liner</h3>
              <p className="text-sm text-muted-foreground">{plannerData.one_liner}</p>
            </div>
          )}

          {/* Assets */}
          {plannerData.assets && plannerData.assets.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Assets ({plannerData.assets.length})
              </h3>
              <div className="space-y-2">
                {plannerData.assets.map((asset: any, i: number) => (
                  <div key={i} className="rounded-lg border border-border p-3 hover:bg-accent/50 transition-colors">
                    <div className="flex items-start justify-between mb-1">
                      <h4 className="text-sm font-medium">{asset.name}</h4>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                        {asset.type}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">{asset.description}</p>
                    <div className="flex gap-3 mt-2 text-xs text-muted-foreground">
                      <span>Format: {asset.format}</span>
                      {asset.content_specs?.page_count && (
                        <span>• Pages: {asset.content_specs.page_count}</span>
                      )}
                    </div>
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
                <div className="grid grid-cols-2 gap-4 mb-3">
                  <div>
                    <span className="text-xs font-medium text-muted-foreground block mb-1">Strategy</span>
                    <p className="text-sm font-semibold capitalize">{plannerData.pricing.strategy}</p>
                  </div>
                  <div>
                    <span className="text-xs font-medium text-muted-foreground block mb-1">Recommended Price</span>
                    <p className="text-sm font-semibold">${plannerData.pricing.recommended_price_usd}</p>
                  </div>
                </div>
                {plannerData.pricing.price_rationale && (
                  <div>
                    <span className="text-xs font-medium text-muted-foreground block mb-1">Rationale</span>
                    <p className="text-xs text-muted-foreground">{plannerData.pricing.price_rationale}</p>
                  </div>
                )}
                {plannerData.pricing.observed_price_range && (
                  <div className="mt-3 pt-3 border-t border-border">
                    <span className="text-xs font-medium text-muted-foreground block mb-1">Market Range</span>
                    <p className="text-xs text-muted-foreground">
                      ${plannerData.pricing.observed_price_range.low} - ${plannerData.pricing.observed_price_range.high}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Marketplace Metadata */}
          {plannerData.marketplace_metadata && (
            <div>
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Tag className="h-4 w-4" />
                Marketplace Listings
              </h3>
              <div className="space-y-3">
                {/* Etsy */}
                {plannerData.marketplace_metadata.etsy && (
                  <div className="rounded-lg border border-border p-4">
                    <h4 className="text-sm font-medium mb-2">Etsy</h4>
                    <div className="space-y-2 text-xs">
                      <div>
                        <span className="font-medium text-muted-foreground">Title:</span>
                        <p className="mt-0.5">{plannerData.marketplace_metadata.etsy.title}</p>
                      </div>
                      <div>
                        <span className="font-medium text-muted-foreground">Price:</span>
                        <p className="mt-0.5">${plannerData.marketplace_metadata.etsy.price_usd}</p>
                      </div>
                      {plannerData.marketplace_metadata.etsy.tags && (
                        <div>
                          <span className="font-medium text-muted-foreground">Tags:</span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {plannerData.marketplace_metadata.etsy.tags.map((tag: string, i: number) => (
                              <span key={i} className="px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">
                                {tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Gumroad */}
                {plannerData.marketplace_metadata.gumroad && (
                  <div className="rounded-lg border border-border p-4">
                    <h4 className="text-sm font-medium mb-2">Gumroad</h4>
                    <div className="space-y-2 text-xs">
                      <div>
                        <span className="font-medium text-muted-foreground">Name:</span>
                        <p className="mt-0.5">{plannerData.marketplace_metadata.gumroad.name}</p>
                      </div>
                      <div>
                        <span className="font-medium text-muted-foreground">Price:</span>
                        <p className="mt-0.5">${plannerData.marketplace_metadata.gumroad.price_usd}</p>
                      </div>
                      {plannerData.marketplace_metadata.gumroad.short_url_slug && (
                        <div>
                          <span className="font-medium text-muted-foreground">URL Slug:</span>
                          <p className="mt-0.5 font-mono">{plannerData.marketplace_metadata.gumroad.short_url_slug}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Niche */}
          {(plannerData.niche || plannerData.sub_niche) && (
            <div>
              <h3 className="text-sm font-semibold mb-2">Market</h3>
              <p className="text-sm text-muted-foreground">
                {plannerData.niche}
                {plannerData.sub_niche && ` • ${plannerData.sub_niche}`}
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-border p-4 flex justify-between items-center">
          <button
            onClick={() => onOpenChange(false)}
            className="px-4 py-2 text-sm font-medium rounded-md border border-border hover:bg-accent transition-colors"
          >
            Close
          </button>
          {onGenerateAssets && canGenerateAssets && (
            <button
              onClick={handleGenerateAssets}
              className="px-4 py-2 text-sm font-medium rounded-md bg-primary text-white hover:bg-primary/80 transition-all hover:shadow-md flex items-center gap-2"
            >
              <Sparkles className="h-4 w-4" />
              <div className="flex flex-col items-start">
                <span>Generate Assets</span>
                <span className="text-xs font-normal text-white/90">Create the digital product files</span>
              </div>
            </button>
          )}
          {bundle.status === 'failed' && (
            <div className="text-xs text-muted-foreground">
              This bundle cannot be processed due to errors
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
