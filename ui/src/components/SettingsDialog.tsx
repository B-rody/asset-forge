import React, { useState, useEffect } from "react";
import { X, Key } from "lucide-react";
import { cn } from "@/lib/utils";
import { ipcClient } from "@/lib/ipc";

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SettingsDialog({ open, onOpenChange }: SettingsDialogProps) {
  const [apiKey, setApiKey] = useState("");
  const [saved, setSaved] = useState(false);
  const [hasExistingKey, setHasExistingKey] = useState(false);

  useEffect(() => {
    if (open) {
      // Check if API key already exists
      checkExistingKey();
    }
  }, [open]);

  const checkExistingKey = async () => {
    try {
      await ipcClient.sendCommand({ cmd: "get_api_key" });
      // Listen for response (simplified - in production you'd want proper event handling)
      // For now, we'll just show the placeholder differently if a key exists
      setHasExistingKey(true);
    } catch (error) {
      console.error("Failed to check for existing API key:", error);
    }
  };

  const handleSave = async () => {
    try {
      await ipcClient.sendCommand({
        cmd: "save_api_key",
        params: { api_key: apiKey }
      });
      setSaved(true);
      setTimeout(() => {
        setSaved(false);
        onOpenChange(false);
      }, 1500);
    } catch (error) {
      console.error("Failed to save API key:", error);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-background/80 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />

      {/* Dialog */}
      <div className="relative z-50 w-full max-w-lg rounded-lg border border-border bg-card p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Settings</h2>
          <button
            onClick={() => onOpenChange(false)}
            className={cn(
              "inline-flex h-8 w-8 items-center justify-center rounded-md",
              "hover:bg-accent hover:text-accent-foreground",
              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            )}
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label htmlFor="apiKey" className="mb-2 flex items-center gap-2 text-sm font-medium">
              <Key className="h-4 w-4" />
              OpenAI API Key
            </label>
            <input
              id="apiKey"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={hasExistingKey ? "••••••••••••••••" : "sk-..."}
              className={cn(
                "w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
                "placeholder:text-muted-foreground",
                "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              )}
            />
            <p className="mt-1 text-xs text-muted-foreground">
              Your API key is stored securely in your system keyring and never transmitted except to OpenAI.
            </p>
          </div>

          <div className="flex justify-end gap-2">
            <button
              onClick={() => onOpenChange(false)}
              className={cn(
                "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium",
                "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
                "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              )}
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={!apiKey || saved}
              className={cn(
                "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium",
                "bg-primary text-primary-foreground shadow hover:bg-primary/90",
                "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                "disabled:pointer-events-none disabled:opacity-50"
              )}
            >
              {saved ? "Saved!" : "Save"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
