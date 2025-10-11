import React, { useEffect, useRef, useState } from "react";
import { Copy, Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface LogEntry {
  timestamp: string;
  step?: string;
  message: string;
  type: "info" | "success" | "error" | "progress";
}

interface LogStreamProps {
  logs: LogEntry[];
  isProcessing?: boolean;
  startTime?: number | null;
}

type LogFilter = "all" | "info" | "warnings" | "errors";

export function LogStream({ logs, isProcessing = false, startTime = null }: LogStreamProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [filter, setFilter] = useState<LogFilter>("all");
  const [copied, setCopied] = useState(false);
  const [elapsedTime, setElapsedTime] = useState<string>("0s");

  // Detect manual scroll
  const handleScroll = () => {
    if (scrollRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 10;
      setAutoScroll(isAtBottom);
    }
  };

  // Copy logs to clipboard
  const handleCopyLogs = async () => {
    const logText = filteredLogs
      .map((log) => `${log.timestamp} ${log.step ? `[${log.step}]` : ""} ${log.message}`)
      .join("\n");

    try {
      await navigator.clipboard.writeText(logText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error("Failed to copy logs:", error);
    }
  };

  // Auto-scroll to bottom when logs update (only if user hasn't scrolled up)
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  // Timer for elapsed time
  useEffect(() => {
    if (!isProcessing || !startTime) {
      setElapsedTime("0s");
      return;
    }

    const updateElapsedTime = () => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      const minutes = Math.floor(elapsed / 60);
      const seconds = elapsed % 60;

      if (minutes > 0) {
        setElapsedTime(`${minutes}m ${seconds}s`);
      } else {
        setElapsedTime(`${seconds}s`);
      }
    };

    // Update immediately
    updateElapsedTime();

    // Update every second
    const interval = setInterval(updateElapsedTime, 1000);

    return () => clearInterval(interval);
  }, [isProcessing, startTime]);

  // Filter logs
  const filteredLogs = logs.filter((log) => {
    if (filter === "all") return true;
    if (filter === "info") return log.type === "info" || log.type === "progress";
    if (filter === "warnings") return log.type === "success";
    if (filter === "errors") return log.type === "error";
    return true;
  });

  return (
    <div className="flex flex-col h-full">
      {/* Filter Tabs and Controls */}
      <div className="flex items-center justify-between gap-2 mb-3 border-b border-border pb-2">
        <div className="flex gap-2">
          {(["all", "info", "warnings", "errors"] as LogFilter[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                "px-3 py-1 text-xs font-medium rounded-md transition-colors",
                filter === f
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
              )}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          {/* Auto-scroll indicator */}
          {!autoScroll && (
            <span className="text-xs text-muted-foreground">
              Auto-scroll paused
            </span>
          )}

          {/* Copy Logs Button */}
          <button
            onClick={handleCopyLogs}
            disabled={logs.length === 0}
            className={cn(
              "inline-flex items-center gap-1.5 px-2 py-1 text-xs font-medium rounded-md transition-colors",
              "hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
            )}
            title="Copy logs to clipboard"
          >
            {copied ? (
              <>
                <Check className="h-3 w-3 text-green-600" />
                <span className="text-green-600">Copied</span>
              </>
            ) : (
              <>
                <Copy className="h-3 w-3" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Log Content */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto rounded-md border border-border bg-slate-50 dark:bg-slate-900/20 p-4 font-mono text-sm leading-6 custom-scrollbar"
      >
        {filteredLogs.length === 0 ? (
          <p className="text-muted-foreground">
            {logs.length === 0
              ? "No logs yet. Start a pipeline to see activity."
              : `No ${filter} logs to display.`}
          </p>
        ) : (
          <div className="space-y-1">
            {filteredLogs.map((log, index) => (
              <div key={index} className="flex gap-2">
                <span className="text-muted-foreground">{log.timestamp}</span>
                {log.step && (
                  <span className="font-semibold text-primary">[{log.step}]</span>
                )}
                <span
                  className={cn(
                    log.type === "error" && "text-destructive font-medium",
                    log.type === "success" && "text-green-600 dark:text-green-400",
                    log.type === "info" && "text-foreground",
                    log.type === "progress" && "text-muted-foreground"
                  )}
                >
                  {log.message}
                </span>
              </div>
            ))}

            {/* Processing indicator */}
            {isProcessing && (
              <div className="flex gap-2 mt-3 pt-3 border-t border-border/50">
                <span className="text-blue-600 dark:text-blue-400 font-medium">
                  Processing<span className="animate-dots">...</span>
                  <span className="ml-2 text-muted-foreground font-normal">
                    ({elapsedTime})
                  </span>
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
