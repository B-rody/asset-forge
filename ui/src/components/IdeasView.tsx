import React, { useState, useEffect } from "react";
import { Lightbulb, Filter, ArrowUpDown, Info } from "lucide-react";
import { ipcClient } from "@/lib/ipc";
import { IdeaCard } from "./IdeaCard";
import { cn } from "@/lib/utils";

interface Idea {
  idea_id: string;
  research_session_id: string;
  created_at: string;
  title: string;
  niche: string;
  sub_niche: string;
  priority: string;
  roi_estimate: number;
  idea_json: string;
}

type SortOption = "roi_desc" | "roi_asc" | "date_desc" | "date_asc" | "priority";
type FilterOption = "all" | "A" | "B" | "C";

interface IdeasViewProps {
  onBuildBundle?: (ideaId: string) => void;
}

export function IdeasView({ onBuildBundle }: IdeasViewProps = {}) {
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<SortOption>("roi_desc");
  const [filterPriority, setFilterPriority] = useState<FilterOption>("all");

  useEffect(() => {
    // Fetch ideas on mount
    const unsubscribe = ipcClient.subscribe((event) => {
      if (event.event === "ideas_list") {
        setIdeas(event.ideas || []);
        setLoading(false);
      }
    });

    ipcClient.sendCommand({ cmd: "get_ideas", params: { limit: 100 } });

    return unsubscribe;
  }, []);

  // Filter ideas by priority
  const filteredIdeas = ideas.filter((idea) => {
    if (filterPriority === "all") return true;
    return idea.priority === filterPriority;
  });

  // Sort ideas
  const sortedIdeas = [...filteredIdeas].sort((a, b) => {
    switch (sortBy) {
      case "roi_desc":
        return b.roi_estimate - a.roi_estimate;
      case "roi_asc":
        return a.roi_estimate - b.roi_estimate;
      case "date_desc":
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      case "date_asc":
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      case "priority":
        const priorityOrder = { A: 1, B: 2, C: 3 };
        return priorityOrder[a.priority as keyof typeof priorityOrder] - priorityOrder[b.priority as keyof typeof priorityOrder];
      default:
        return 0;
    }
  });

  if (loading) {
    return (
      <div className="rounded-lg border border-border bg-card p-12 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
        <p className="mt-4 text-sm text-muted-foreground">Loading ideas...</p>
      </div>
    );
  }

  if (ideas.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-card p-12 text-center">
        <Lightbulb className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">No Ideas Yet</h3>
        <p className="text-sm text-muted-foreground max-w-md mx-auto">
          Run the researcher to generate product ideas. They'll appear here for you to review and use.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex flex-wrap gap-3 items-center">
        {/* Priority Filter */}
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <select
            value={filterPriority}
            onChange={(e) => setFilterPriority(e.target.value as FilterOption)}
            className="text-sm border border-input bg-background rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="all">All Priorities</option>
            <option value="A">Priority A</option>
            <option value="B">Priority B</option>
            <option value="C">Priority C</option>
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
            <option value="roi_desc">ROI (High → Low)</option>
            <option value="roi_asc">ROI (Low → High)</option>
            <option value="priority">Priority</option>
            <option value="date_desc">Newest First</option>
            <option value="date_asc">Oldest First</option>
          </select>
        </div>

        {/* Info Tooltip */}
        <div className="group relative">
          <Info className="h-4 w-4 text-muted-foreground hover:text-primary cursor-help transition-colors" />
          <div className="absolute left-0 top-6 z-50 hidden group-hover:block w-80 p-3 bg-popover border border-border rounded-lg shadow-lg">
            <div className="space-y-2 text-xs">
              <div>
                <span className="font-semibold text-foreground">ROI:</span>
                <span className="text-muted-foreground"> Calculated metric (reach × impact × confidence / effort)</span>
              </div>
              <div>
                <span className="font-semibold text-foreground">Priority:</span>
                <span className="text-muted-foreground"> Strategic judgment considering timing, differentiation, and market fit</span>
              </div>
              <p className="text-muted-foreground italic pt-1 border-t border-border">
                Note: Priority B can have higher ROI than Priority A when strategic factors outweigh pure metrics
              </p>
            </div>
          </div>
        </div>

        {/* Count */}
        <div className="ml-auto text-sm text-muted-foreground">
          Showing {sortedIdeas.length} of {ideas.length} ideas
        </div>
      </div>

      {/* Ideas Grid */}
      {sortedIdeas.length === 0 ? (
        <div className="rounded-lg border border-border bg-card p-8 text-center">
          <p className="text-sm text-muted-foreground">
            No ideas match the selected filter.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {sortedIdeas.map((idea) => (
            <IdeaCard key={idea.idea_id} idea={idea} onBuildBundle={onBuildBundle} />
          ))}
        </div>
      )}
    </div>
  );
}
