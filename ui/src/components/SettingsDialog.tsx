import React, { useState, useEffect } from "react";
import { X, Key, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { ipcClient } from "@/lib/ipc";
import OpenAI from "openai";

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SettingsDialog({ open, onOpenChange }: SettingsDialogProps) {
  const [apiKey, setApiKey] = useState("");
  const [saved, setSaved] = useState(false);
  const [hasExistingKey, setHasExistingKey] = useState(false);
  const [validating, setValidating] = useState(false);
  const [error, setError] = useState("");
  const [pendingDelete, setPendingDelete] = useState(false);

  useEffect(() => {
    if (open) {
      // Check if API key already exists
      checkExistingKey();
      // Clear error and pending delete when dialog opens
      setError("");
      setPendingDelete(false);
      setApiKey("");
    }
  }, [open]);

  const checkExistingKey = async () => {
    try {
      // Subscribe to the response
      const unsubscribe = ipcClient.subscribe((event) => {
        if (event.event === "api_key_status") {
          unsubscribe();
          setHasExistingKey(event.has_key === true);
        }
      });

      // Send the command
      await ipcClient.sendCommand({ cmd: "get_api_key" });

      // Timeout after 2 seconds
      setTimeout(() => {
        unsubscribe();
      }, 2000);
    } catch (error) {
      console.error("Failed to check for existing API key:", error);
      setHasExistingKey(false);
    }
  };

  const validateApiKey = async (key: string): Promise<boolean> => {
    try {
      const client = new OpenAI({
        apiKey: key,
        dangerouslyAllowBrowser: true, // We're in a desktop app, this is safe
      });

      // Make a lightweight API call to verify the key works
      await client.models.list();
      return true;
    } catch (err: any) {
      // Parse the error to provide helpful feedback
      if (err?.status === 401) {
        setError("Invalid API key. Please check your key and try again.");
      } else if (err?.status === 429) {
        setError("Rate limit exceeded. Your key is valid but you've hit the rate limit.");
        return true; // Key is technically valid
      } else if (err?.message?.includes("network") || err?.message?.includes("fetch")) {
        setError("Network error. Please check your internet connection.");
      } else {
        setError(`Validation failed: ${err?.message || "Unknown error"}`);
      }
      return false;
    }
  };

  const handleSave = async (e?: React.FormEvent) => {
    e?.preventDefault();
    setError("");

    // If pending delete, actually delete the key
    if (pendingDelete) {
      setValidating(true);
      try {
        await ipcClient.sendCommand({
          cmd: "delete_api_key"
        });

        setHasExistingKey(false);
        setPendingDelete(false);
        setSaved(true);
        setValidating(false);

        setTimeout(() => {
          setSaved(false);
          setApiKey("");
          onOpenChange(false);
        }, 1500);
      } catch (error) {
        console.error("Failed to delete API key:", error);
        setError("Failed to delete API key. Please try again.");
        setValidating(false);
      }
      return;
    }

    // Otherwise, validate and save the new key
    setValidating(true);

    try {
      // Validate the API key first
      const isValid = await validateApiKey(apiKey);

      if (!isValid) {
        setValidating(false);
        return;
      }

      // If valid, save it
      await ipcClient.sendCommand({
        cmd: "save_api_key",
        params: { api_key: apiKey }
      });

      setSaved(true);
      setValidating(false);

      setTimeout(() => {
        setSaved(false);
        setApiKey("");
        setError("");
        setPendingDelete(false);
        onOpenChange(false);
      }, 1500);
    } catch (error) {
      console.error("Failed to save API key:", error);
      setError("Failed to save API key. Please try again.");
      setValidating(false);
    }
  };

  const handleDelete = () => {
    // Mark for deletion and clear input
    setPendingDelete(true);
    setApiKey("");
    setError("");
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-background/80 backdrop-blur-sm"
        onClick={() => {
          setPendingDelete(false);
          setApiKey("");
          setError("");
          onOpenChange(false);
        }}
      />

      {/* Dialog */}
      <div className="relative z-50 w-full max-w-lg rounded-lg border border-border bg-card p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Settings</h2>
          <button
            onClick={() => {
              setPendingDelete(false);
              setApiKey("");
              setError("");
              onOpenChange(false);
            }}
            className={cn(
              "inline-flex h-8 w-8 items-center justify-center rounded-md",
              "hover:bg-accent hover:text-accent-foreground",
              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            )}
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label htmlFor="apiKey" className="mb-2 flex items-center gap-2 text-sm font-medium">
              <Key className="h-4 w-4" />
              OpenAI API Key
            </label>
            <div className="flex gap-2">
              <input
                id="apiKey"
                type="password"
                value={apiKey}
                onChange={(e) => {
                  setApiKey(e.target.value);
                  setError(""); // Clear error when user types
                  if (pendingDelete && e.target.value) {
                    setPendingDelete(false); // Cancel deletion if user starts typing
                  }
                }}
                placeholder={
                  pendingDelete
                    ? "Key marked for deletion"
                    : hasExistingKey
                    ? "••••••••••••••••"
                    : "sk-..."
                }
                className={cn(
                  "flex-1 rounded-md border px-3 py-2 text-sm",
                  "placeholder:text-muted-foreground",
                  "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                  pendingDelete
                    ? "border-destructive bg-destructive/5"
                    : "border-input bg-background"
                )}
              />
              {hasExistingKey && !pendingDelete && (
                <button
                  type="button"
                  onClick={handleDelete}
                  className={cn(
                    "inline-flex items-center justify-center rounded-md px-3 py-2",
                    "border border-input bg-background hover:bg-destructive/10 hover:border-destructive",
                    "transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  )}
                  title="Delete API key"
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </button>
              )}
            </div>
            {pendingDelete ? (
              <p className="mt-1 text-xs text-destructive">
                ⚠️ Are you sure you want to delete your API key?
              </p>
            ) : (
              <p className="mt-1 text-xs text-muted-foreground">
                Your API key is stored securely in your system keyring and never transmitted except to OpenAI.
              </p>
            )}
            {error && (
              <p className="mt-2 text-xs text-destructive">
                {error}
              </p>
            )}
          </div>

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => {
                setPendingDelete(false);
                setApiKey("");
                setError("");
                onOpenChange(false);
              }}
              className={cn(
                "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium",
                "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
                "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              )}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={(!apiKey && !pendingDelete) || saved || validating}
              className={cn(
                "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium",
                "shadow focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                "disabled:pointer-events-none disabled:opacity-50",
                pendingDelete
                  ? "bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  : "bg-primary text-primary-foreground hover:bg-primary/90"
              )}
            >
              {validating
                ? pendingDelete
                  ? "Deleting..."
                  : "Validating..."
                : saved
                ? "Saved!"
                : pendingDelete
                ? "Confirm Delete"
                : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
