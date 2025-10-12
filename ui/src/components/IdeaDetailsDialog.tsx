import React from "react";
import { X, TrendingUp, Target, AlertCircle, Package } from "lucide-react";
import { cn } from "@/lib/utils";

interface IdeaDetailsDialogProps {
  idea: {
    idea_id: string;
    research_session_id: string;
    created_at: string;
    title: string;
    niche: string;
    sub_niche: string;
    priority: string;
    roi_estimate: number;
    idea_json: string;
  };
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onBuildBundle?: (ideaId: string) => void;
}

export function IdeaDetailsDialog({ idea, open, onOpenChange, onBuildBundle }: IdeaDetailsDialogProps) {
  if (!open) return null;

  const handleBuildBundle = () => {
    if (onBuildBundle) {
      onBuildBundle(idea.idea_id);
      onOpenChange(false); // Close dialog after starting build
    }
  };

  // Parse idea JSON
  let ideaData: any = {};
  try {
    ideaData = JSON.parse(idea.idea_json);
  } catch (e) {
    console.error("Failed to parse idea JSON:", e);
  }

  // Priority colors
  const priorityColors = {
    A: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    B: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
    C: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400",
  };

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
              <h2 className="text-xl font-semibold">{idea.title}</h2>
              <span
                className={cn(
                  "px-2.5 py-0.5 text-xs font-bold rounded-full",
                  priorityColors[idea.priority as keyof typeof priorityColors] || priorityColors.C
                )}
              >
                Priority {idea.priority}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              {idea.niche} • {idea.sub_niche}
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
          {/* One-liner */}
          {ideaData.one_liner && (
            <div>
              <h3 className="text-sm font-semibold mb-2">One-Liner</h3>
              <p className="text-sm text-muted-foreground">{ideaData.one_liner}</p>
            </div>
          )}

          {/* Value Proposition */}
          {ideaData.value_prop && (
            <div>
              <h3 className="text-sm font-semibold mb-2">Value Proposition</h3>
              <p className="text-sm text-muted-foreground">{ideaData.value_prop}</p>
            </div>
          )}

          {/* Differentiation */}
          {ideaData.differentiation_angle && (
            <div>
              <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
                <Target className="h-4 w-4" />
                Differentiation Angle
              </h3>
              <p className="text-sm text-muted-foreground">{ideaData.differentiation_angle}</p>
            </div>
          )}

          {/* Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="rounded-lg border border-border p-3">
              <div className="flex items-center gap-2 mb-1">
                <TrendingUp className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                <span className="text-xs font-medium text-muted-foreground">ROI Estimate</span>
              </div>
              <p className="text-lg font-semibold">{idea.roi_estimate.toFixed(2)}</p>
            </div>
            {ideaData.reach && (
              <div className="rounded-lg border border-border p-3">
                <span className="text-xs font-medium text-muted-foreground block mb-1">Reach</span>
                <p className="text-lg font-semibold">{ideaData.reach}/5</p>
              </div>
            )}
            {ideaData.impact && (
              <div className="rounded-lg border border-border p-3">
                <span className="text-xs font-medium text-muted-foreground block mb-1">Impact</span>
                <p className="text-lg font-semibold">{ideaData.impact}/5</p>
              </div>
            )}
            {ideaData.confidence && (
              <div className="rounded-lg border border-border p-3">
                <span className="text-xs font-medium text-muted-foreground block mb-1">Confidence</span>
                <p className="text-lg font-semibold">{(ideaData.confidence * 100).toFixed(0)}%</p>
              </div>
            )}
          </div>

          {/* Demand Signals */}
          {ideaData.demand_signals && ideaData.demand_signals.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-2">Demand Signals</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                {ideaData.demand_signals.map((signal: string, i: number) => (
                  <li key={i}>{signal}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Pricing */}
          {ideaData.suggested_price_band && (
            <div>
              <h3 className="text-sm font-semibold mb-2">Suggested Pricing</h3>
              <p className="text-sm text-muted-foreground">
                ${ideaData.suggested_price_band.low} - ${ideaData.suggested_price_band.high}
              </p>
            </div>
          )}

          {/* Counterpoints */}
          {ideaData.counterpoints && ideaData.counterpoints.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                Counterpoints / Risks
              </h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                {ideaData.counterpoints.map((point: string, i: number) => (
                  <li key={i}>{point}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Why Now */}
          {ideaData.why_now && (
            <div>
              <h3 className="text-sm font-semibold mb-2">Why Now?</h3>
              <p className="text-sm text-muted-foreground">{ideaData.why_now}</p>
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
          {onBuildBundle && (
            <button
              onClick={handleBuildBundle}
              className="px-4 py-2 text-sm font-medium rounded-md bg-primary text-white hover:bg-primary/80 transition-all hover:shadow-md flex items-center gap-2"
            >
              <Package className="h-4 w-4" />
              <div className="flex flex-col items-start">
                <span>Create Bundle Plan</span>
                <span className="text-xs font-normal text-white/90">Design bundle structure & pricing</span>
              </div>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
