import React, { useEffect, useRef } from "react";
import { Check, AlertCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

interface StepChip {
  name: string;
  status: "pending" | "running" | "success" | "error";
}

interface StepChipsProps {
  steps: StepChip[];
  stepProgress: Record<string, number>;
}

// Step descriptions for tooltips
const stepDescriptions: Record<string, string> = {
  Researcher: "Scans marketplaces and finds digital product ideas",
  Planner: "Designs bundle structure and pricing",
  Maker: "Generates assets and metadata",
  Packager: "Finalizes ZIP and QA report",
};

export function StepChips({ steps, stepProgress }: StepChipsProps) {
  // Derive activeIndex from steps (first "running" step)
  const activeIndex = steps.findIndex((s) => s.status === "running");

  // Track previous activeIndex for shimmer-once effect
  const prevActiveRef = useRef(activeIndex);
  const activatedNow = prevActiveRef.current !== activeIndex;

  useEffect(() => {
    prevActiveRef.current = activeIndex;
  }, [activeIndex]);

  return (
    <div className="flex flex-wrap items-center justify-between gap-1 px-4 sm:flex-nowrap">
      {steps.map((step, index) => {
        const isActive = step.status === "running";
        const isComplete = step.status === "success";
        const isError = step.status === "error";
        const isPending = step.status === "pending";

        return (
          <React.Fragment key={step.name}>
            {/* Step Node */}
            <div className="flex flex-col items-center gap-2 group relative">
              <button
                type="button"
                aria-current={isActive ? "step" : undefined}
                className={cn(
                  "relative rounded-full h-10 w-10 flex items-center justify-center text-sm font-medium transition-all duration-300",
                  "border-2",
                  isActive &&
                    "bg-blue-600 text-white border-blue-600 breathe ring-1 ring-blue-500/40",
                  isComplete &&
                    "bg-green-500 text-white border-green-500",
                  isPending &&
                    "bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-400 border-slate-300 dark:border-slate-600",
                  isError &&
                    "bg-red-500 text-white border-red-500",
                  // Add shimmer-once when node becomes active
                  activatedNow && isActive && "shimmer-once"
                )}
              >
                <AnimatePresence mode="popLayout" initial={false}>
                  {isComplete ? (
                    <motion.span
                      key="chk"
                      initial={{ scale: 0.6, rotate: -15, opacity: 0 }}
                      animate={{ scale: 1, rotate: 0, opacity: 1 }}
                      exit={{ scale: 0.6, opacity: 0 }}
                      transition={{ type: "spring", stiffness: 420, damping: 24 }}
                    >
                      <Check className="h-5 w-5" />
                    </motion.span>
                  ) : isError ? (
                    <motion.span
                      key="err"
                      initial={{ scale: 0.6, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.6, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <AlertCircle className="h-5 w-5" />
                    </motion.span>
                  ) : (
                    <motion.span
                      key="num"
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.8, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="text-sm font-medium"
                    >
                      {index + 1}
                    </motion.span>
                  )}
                </AnimatePresence>
              </button>

              {/* Step Label with animated color */}
              <motion.div
                initial={false}
                animate={{
                  color: isActive
                    ? "rgb(59 130 246)" // text-blue-500
                    : isComplete
                    ? "rgb(34 197 94)" // text-green-500
                    : isError
                    ? "rgb(239 68 68)" // text-red-500
                    : "rgb(100 116 139)", // text-slate-500
                }}
                transition={{ duration: 0.25 }}
                className="text-xs font-medium whitespace-nowrap"
              >
                {step.name}
              </motion.div>

              {/* Tooltip */}
              <div className="absolute bottom-full mb-2 hidden group-hover:block z-10 pointer-events-none">
                <div className="bg-popover text-popover-foreground px-3 py-2 rounded-md shadow-lg text-xs min-w-[185px] text-center border whitespace-normal">
                  {stepDescriptions[step.name] || step.name}
                </div>
              </div>
            </div>

            {/* Connecting Line */}
            {index < steps.length - 1 && (
              <div className="relative flex-1 h-[3px] mx-1">
                {/* Base track */}
                <div className="absolute inset-0 rounded-full bg-slate-300 dark:bg-slate-600/60" />

                {/* Filled overlay */}
                <div
                  className="absolute inset-0 origin-left rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-transform duration-[400ms] ease-in-out"
                  style={{
                    transform: `scaleX(${
                      step.status === "success"
                        ? 1
                        : step.status === "running"
                        ? Math.max(0, Math.min(1, (stepProgress[step.name] || 0) / 100))
                        : 0
                    })`,
                  }}
                />

                {/* Optional glowing bead on active connector */}
                {step.status === "running" && (
                  <span className="progress-bead" />
                )}
              </div>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}
