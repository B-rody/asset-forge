import React, { useState } from "react";
import { Moon, Sun, Settings } from "lucide-react";
import { cn } from "@/lib/utils";
import { SettingsDialog } from "./SettingsDialog";

export function HeaderBar() {
  const [isDark, setIsDark] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const toggleTheme = () => {
    setIsDark(!isDark);
    document.documentElement.classList.toggle("dark");
  };

  return (
    <>
      <header className="border-b border-border bg-background px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold text-lg">
              AF
            </div>
            <div>
              <h1 className="text-xl font-bold">AssetForge</h1>
              <p className="text-xs text-muted-foreground">
                Digital Asset Factory
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={toggleTheme}
              className={cn(
                "inline-flex items-center justify-center rounded-md text-sm font-medium",
                "h-9 w-9 hover:bg-accent hover:text-accent-foreground",
                "transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              )}
              aria-label="Toggle theme"
            >
              {isDark ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Moon className="h-5 w-5" />
              )}
            </button>

            <button
              onClick={() => setShowSettings(true)}
              className={cn(
                "inline-flex items-center justify-center rounded-md text-sm font-medium",
                "h-9 w-9 hover:bg-accent hover:text-accent-foreground",
                "transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              )}
              aria-label="Settings"
            >
              <Settings className="h-5 w-5" />
            </button>
          </div>
        </div>
      </header>

      <SettingsDialog open={showSettings} onOpenChange={setShowSettings} />
    </>
  );
}
