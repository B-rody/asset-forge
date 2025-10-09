import React, { useState } from "react";
import { Download, CheckCircle2, XCircle, FolderOpen, Clock, FileText, Copy, ChevronDown } from "lucide-react";
import { open as openPath } from "@tauri-apps/api/shell";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface Result {
  bundle_id: string;
  output_path: string;
  qa_score?: number;
  status: "success" | "error" | "pending";
  runtime?: string; // e.g., "2m 15s"
  file_count?: number;
}

interface ResultPanelProps {
  result: Result | null;
}

export function ResultPanel({ result }: ResultPanelProps) {
  const [copiedPath, setCopiedPath] = useState(false);

  const handleOpenFolder = async () => {
    if (result?.output_path) {
      try {
        // Open the folder containing the bundle
        const folderPath = result.output_path.substring(0, result.output_path.lastIndexOf('/'));
        await openPath(folderPath);
      } catch (error) {
        console.error("Failed to open folder:", error);
      }
    }
  };

  const handleCopyPath = async () => {
    if (result?.output_path) {
      try {
        await navigator.clipboard.writeText(result.output_path);
        setCopiedPath(true);
        setTimeout(() => setCopiedPath(false), 2000);
      } catch (error) {
        console.error("Failed to copy path:", error);
      }
    }
  };

  const handleDownloadZip = () => {
    // TODO: Implement ZIP download
    console.log("Download ZIP clicked");
  };

  if (!result) {
    return (
      <div className="rounded-lg border border-border bg-card p-6">
        <h2 className="mb-4 text-lg font-semibold">Results</h2>
        <div className="text-sm text-muted-foreground">
          <p>Once your bundle is ready, it will appear here with download options.</p>
        </div>
      </div>
    );
  }

  const qaScoreColor =
    result.qa_score !== undefined
      ? result.qa_score >= 0.9
        ? "green"
        : result.qa_score >= 0.7
        ? "yellow"
        : "red"
      : "gray";

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <h2 className="mb-4 text-lg font-semibold">Results</h2>

      <div className="space-y-4">
        {/* Bundle Info */}
        <div className="flex items-start gap-4">
          {result.status === "success" ? (
            <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 mt-1" />
          ) : result.status === "error" ? (
            <XCircle className="h-5 w-5 text-destructive mt-1" />
          ) : null}

          <div className="flex-1">
            <button
              onClick={handleOpenFolder}
              className="font-medium text-primary hover:underline flex items-center gap-2 group"
            >
              {result.bundle_id}
              <FolderOpen className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>
            <p className="text-sm text-muted-foreground mt-1">{result.output_path}</p>

            {/* Stats Row */}
            <div className="flex items-center gap-4 mt-3 text-sm text-muted-foreground">
              {result.runtime && (
                <div className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  <span>{result.runtime || "2m 15s"}</span>
                </div>
              )}
              {result.file_count !== undefined && (
                <div className="flex items-center gap-1">
                  <FileText className="h-4 w-4" />
                  <span>{result.file_count || 3} files</span>
                </div>
              )}
            </div>
          </div>

          {/* Circular QA Badge */}
          {result.qa_score !== undefined && (
            <div className="flex flex-col items-center gap-2 animate-in fade-in zoom-in duration-500">
              <div
                className={cn(
                  "relative w-16 h-16 rounded-full border-4 flex items-center justify-center font-bold text-lg",
                  qaScoreColor === "green" &&
                    "border-green-500 text-green-600 dark:text-green-400",
                  qaScoreColor === "yellow" &&
                    "border-yellow-500 text-yellow-600 dark:text-yellow-400",
                  qaScoreColor === "red" &&
                    "border-red-500 text-red-600 dark:text-red-400"
                )}
              >
                {(result.qa_score * 100).toFixed(0)}%
              </div>
              <span className="text-xs text-muted-foreground">QA Score</span>
            </div>
          )}
        </div>

        {/* Download Menu */}
        {result.status === "success" && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                className={cn(
                  "inline-flex w-full items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium",
                  "bg-primary text-primary-foreground shadow hover:bg-primary/90",
                  "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                  "transition-colors"
                )}
              >
                <Download className="h-4 w-4" />
                Download Bundle
                <ChevronDown className="h-4 w-4 ml-auto" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-[200px]">
              <DropdownMenuItem onClick={handleDownloadZip}>
                <Download className="mr-2 h-4 w-4" />
                Download ZIP
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleOpenFolder}>
                <FolderOpen className="mr-2 h-4 w-4" />
                Open Folder
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleCopyPath}>
                <Copy className="mr-2 h-4 w-4" />
                {copiedPath ? "Path Copied!" : "Copy Path"}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    </div>
  );
}
