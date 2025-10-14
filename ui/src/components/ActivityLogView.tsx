import React, { useState, useEffect } from "react";
import { Activity, CheckCircle2, XCircle, Clock, Lightbulb, FileText, Package as PackageIcon, Box } from "lucide-react";
import { ipcClient } from "@/lib/ipc";
import { cn } from "@/lib/utils";

interface ActivityLog {
  activity_id: string;
  activity_type: string;
  bundle_id: string | null;
  idea_id: string | null;
  started_at: string;
  completed_at: string | null;
  status: string;
  duration_seconds: number | null;
  error_message: string | null;
  metadata_json: string | null;
}

export function ActivityLogView() {
  const [activities, setActivities] = useState<ActivityLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch activity log on mount
    const unsubscribe = ipcClient.subscribe((event) => {
      if (event.event === "activity_log_list") {
        setActivities(event.activities || []);
        setLoading(false);
      }
    });

    ipcClient.sendCommand({ cmd: "get_activity_log", params: { limit: 100 } });

    return unsubscribe;
  }, []);

  // Helper to get activity type icon
  const getActivityIcon = (type: string) => {
    switch (type) {
      case "research":
        return <Lightbulb className="h-4 w-4 text-blue-600 dark:text-blue-400" />;
      case "planner":
        return <FileText className="h-4 w-4 text-purple-600 dark:text-purple-400" />;
      case "maker":
        return <PackageIcon className="h-4 w-4 text-orange-600 dark:text-orange-400" />;
      case "packager":
        return <Box className="h-4 w-4 text-green-600 dark:text-green-400" />;
      default:
        return <Activity className="h-4 w-4 text-gray-600 dark:text-gray-400" />;
    }
  };

  // Helper to get status badge
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
            <CheckCircle2 className="h-3 w-3" />
            Completed
          </span>
        );
      case "failed":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
            <XCircle className="h-3 w-3" />
            Failed
          </span>
        );
      case "in_progress":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400">
            <Clock className="h-3 w-3" />
            In Progress
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400">
            {status}
          </span>
        );
    }
  };

  // Format duration
  const formatDuration = (seconds: number | null) => {
    if (!seconds) return "—";
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Group activities by date
  const groupedActivities = activities.reduce((groups, activity) => {
    const date = new Date(activity.started_at).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(activity);
    return groups;
  }, {} as Record<string, ActivityLog[]>);

  if (loading) {
    return (
      <div className="rounded-lg border border-border bg-card p-12 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
        <p className="mt-4 text-sm text-muted-foreground">Loading activity log...</p>
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-card p-12 text-center">
        <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">No Activity Yet</h3>
        <p className="text-sm text-muted-foreground max-w-md mx-auto">
          Pipeline activities will appear here once you start generating bundles.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {Object.entries(groupedActivities).map(([date, dateActivities]) => (
        <div key={date}>
          {/* Date header */}
          <h3 className="text-sm font-semibold text-muted-foreground mb-3">{date}</h3>

          {/* Activities for this date */}
          <div className="space-y-2">
            {dateActivities.map((activity) => (
              <div
                key={activity.activity_id}
                className="rounded-lg border border-border bg-card p-4 hover:shadow-sm transition-shadow"
              >
                <div className="flex items-start justify-between gap-4">
                  {/* Left: Icon + Type + Bundle ID */}
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    <div className="flex-shrink-0 mt-0.5">
                      {getActivityIcon(activity.activity_type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium text-sm capitalize">
                          {activity.activity_type}
                        </h4>
                        {getStatusBadge(activity.status)}
                      </div>
                      {activity.bundle_id && (
                        <p className="text-xs text-muted-foreground font-mono">
                          {activity.bundle_id}
                        </p>
                      )}
                      {activity.error_message && (
                        <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                          {activity.error_message}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Right: Time + Duration */}
                  <div className="text-right flex-shrink-0">
                    <p className="text-xs text-muted-foreground">
                      {formatDate(activity.started_at)}
                    </p>
                    {activity.duration_seconds && (
                      <p className="text-xs font-medium text-muted-foreground mt-1">
                        {formatDuration(activity.duration_seconds)}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
