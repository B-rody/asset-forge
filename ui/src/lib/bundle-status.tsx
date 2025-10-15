import React from "react";
import { Package, XCircle, Clock, Sparkles } from "lucide-react";

export interface BundleStatus {
  label: string;
  color: string;
  icon: React.ReactNode;
}

/**
 * Determine display status based on bundle workflow state
 *
 * @param current_step - Current pipeline step (planner, maker, packager)
 * @param status - Bundle status (pending, completed, failed)
 * @returns Status display configuration with label, color classes, and icon
 */
export function getDisplayStatus(current_step: string, status: string): BundleStatus {
  if (status === "failed") {
    return {
      label: "Failed",
      color: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 border-red-200 dark:border-red-800",
      icon: <XCircle className="h-3 w-3" />
    };
  }

  if (status === "pending") {
    return {
      label: "Pending",
      color: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400 border-yellow-200 dark:border-yellow-800",
      icon: <Clock className="h-3 w-3" />
    };
  }

  // Completed states - distinguish by current_step
  if (current_step === "planner" && status === "completed") {
    return {
      label: "Ready to Make",
      color: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 border-blue-200 dark:border-blue-800",
      icon: <Sparkles className="h-3 w-3" />
    };
  }

  if (current_step === "maker" && status === "completed") {
    return {
      label: "Ready to Package",
      color: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400 border-orange-200 dark:border-orange-800",
      icon: <Package className="h-3 w-3" />
    };
  }

  // Default fallback
  return {
    label: "In Progress",
    color: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400 border-yellow-200 dark:border-yellow-800",
    icon: <Clock className="h-3 w-3" />
  };
}
