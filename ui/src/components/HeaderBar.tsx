import { useState, useEffect } from "react";
import { Moon, Sun, Key, HelpCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { SettingsDialog } from "./SettingsDialog";
import { HelpDialog } from "./HelpDialog";
import { ipcClient } from "@/lib/ipc";

export function HeaderBar() {
  const [isDark, setIsDark] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [hasApiKey, setHasApiKey] = useState<boolean | null>(null);

  // Set dark mode on initial load
  useEffect(() => {
    document.documentElement.classList.add("dark");
  }, []);

  // Check for API key on mount
  useEffect(() => {
    checkApiKey();
  }, []);

  const checkApiKey = async () => {
    const unsubscribe = ipcClient.subscribe((event) => {
      if (event.event === "api_key_status") {
        unsubscribe();
        setHasApiKey(event.has_key === true);
      }
    });

    await ipcClient.sendCommand({ cmd: "get_api_key" });

    // Timeout after 2 seconds
    setTimeout(() => {
      unsubscribe();
    }, 2000);
  };

  // Refresh API key status when settings dialog closes
  const handleSettingsChange = (open: boolean) => {
    setShowSettings(open);
    if (!open) {
      checkApiKey();
    }
  };

  const toggleTheme = () => {
    setIsDark(!isDark);
    document.documentElement.classList.toggle("dark");
  };

  return (
    <>
      <header className="border-b border-border bg-background px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img
              src="/app-icon.png"
              alt="AssetFurnace"
              className="h-10 w-10 rounded-lg"
            />
            <div>
              <h1 className="text-xl font-bold">AssetFurnace</h1>
              <p className="text-xs text-muted-foreground">
                Digital Asset Factory
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
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
              type="button"
              onClick={() => setShowHelp(true)}
              className={cn(
                "inline-flex items-center justify-center rounded-md text-sm font-medium",
                "h-9 w-9 hover:bg-accent hover:text-accent-foreground",
                "transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              )}
              aria-label="Help"
              title="Help & Documentation"
            >
              <HelpCircle className="h-5 w-5" />
            </button>

            <button
              type="button"
              onClick={() => setShowSettings(true)}
              className={cn(
                "relative inline-flex items-center justify-center rounded-md text-sm font-medium",
                "h-9 w-9 hover:bg-accent hover:text-accent-foreground",
                "transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              )}
              aria-label="API Key Settings"
              title={
                hasApiKey === null
                  ? "Checking API key..."
                  : hasApiKey
                    ? "API key configured"
                    : "No API key configured"
              }
            >
              <Key className="h-5 w-5" />
              {hasApiKey !== null && (
                <span
                  className={cn(
                    "absolute -top-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-background",
                    hasApiKey
                      ? "bg-green-500 dark:bg-green-400"
                      : "bg-amber-500 dark:bg-amber-400"
                  )}
                  aria-hidden="true"
                />
              )}
            </button>
          </div>
        </div>
      </header>

      <SettingsDialog open={showSettings} onOpenChange={handleSettingsChange} />
      <HelpDialog open={showHelp} onOpenChange={setShowHelp} />
    </>
  );
}
