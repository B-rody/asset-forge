import React from "react";
import { Zap, History, Database } from "lucide-react";
import { cn } from "@/lib/utils";

type TabId = "one-click" | "library" | "history";

interface Tab {
  id: TabId;
  label: string;
  icon: React.ReactNode;
}

const tabs: Tab[] = [
  { id: "one-click", label: "Generate", icon: <Zap className="h-4 w-4" /> },
  { id: "library", label: "Library", icon: <Database className="h-4 w-4" /> },
  { id: "history", label: "History", icon: <History className="h-4 w-4" /> },
];

interface SidebarProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
}

export function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  return (
    <aside className="w-64 border-r border-border bg-muted/40">
      <nav className="flex flex-col gap-1 p-4">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              "hover:bg-accent hover:text-accent-foreground",
              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
              activeTab === tab.id &&
                "bg-primary text-primary-foreground hover:bg-primary/90"
            )}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </nav>
    </aside>
  );
}
