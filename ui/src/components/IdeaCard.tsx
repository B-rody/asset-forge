import { useState } from "react";
import { Lightbulb, TrendingUp, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { IdeaDetailsDialog } from "./IdeaDetailsDialog";

interface IdeaCardProps {
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
  onBuildBundle?: (ideaId: string) => void;
  onBuildFullBundle?: (ideaId: string) => void;
  onDelete?: (ideaId: string) => Promise<void>;
}

export function IdeaCard({ idea, onBuildBundle, onBuildFullBundle, onDelete }: IdeaCardProps) {
  const [showDetails, setShowDetails] = useState(false);

  // Priority badge colors
  const priorityColors = {
    A: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 border-green-200 dark:border-green-800",
    B: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 border-blue-200 dark:border-blue-800",
    C: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400 border-gray-200 dark:border-gray-800",
  };

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
            <Lightbulb className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
            <h3 className="font-semibold text-sm leading-tight line-clamp-2">
              {idea.title}
            </h3>
          </div>
          <span
            className={cn(
              "px-2 py-0.5 text-xs font-bold rounded-full border flex-shrink-0",
              priorityColors[idea.priority as keyof typeof priorityColors] ||
                priorityColors.C
            )}
          >
            {idea.priority}
          </span>
        </div>

        {/* Idea ID and Niche */}
        <div className="mb-3 space-y-1">
          <p className="text-xs text-muted-foreground">
            {idea.idea_id}
          </p>
          <p className="text-xs text-muted-foreground">
            {idea.niche} • {idea.sub_niche}
          </p>
        </div>

        {/* ROI and Expand */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <TrendingUp className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            <span className="text-sm font-medium">
              ROI: {idea.roi_estimate.toFixed(2)}
            </span>
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground group-hover:text-foreground">
            <span>Details</span>
            <ChevronRight className="h-3 w-3" />
          </div>
        </div>
      </button>

      {/* Details Dialog */}
      <IdeaDetailsDialog
        idea={idea}
        open={showDetails}
        onOpenChange={setShowDetails}
        onBuildBundle={onBuildBundle}
        onBuildFullBundle={onBuildFullBundle}
        onDelete={onDelete}
      />
    </>
  );
}
