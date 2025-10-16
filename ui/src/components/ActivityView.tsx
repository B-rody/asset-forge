import { useState, useEffect } from "react";
import { Search, Calendar, Lightbulb } from "lucide-react";
import { ipcClient } from "@/lib/ipc";

interface ResearchSession {
  session_id: string;
  created_at: string;
  idea_count: number;
}

export function ActivityView() {
  const [sessions, setSessions] = useState<ResearchSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch research sessions on mount
    const unsubscribe = ipcClient.subscribe((event) => {
      if (event.event === "research_sessions_list") {
        setSessions(event.sessions || []);
        setLoading(false);
      }
    });

    ipcClient.sendCommand({ cmd: "get_research_sessions", params: { limit: 100 } });

    return unsubscribe;
  }, []);

  if (loading) {
    return (
      <div className="rounded-lg border border-border bg-card p-12 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
        <p className="mt-4 text-sm text-muted-foreground">Loading activity...</p>
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-card p-12 text-center">
        <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">No Research Sessions Yet</h3>
        <p className="text-sm text-muted-foreground max-w-md mx-auto">
          Run the researcher to generate product ideas. Your research sessions will appear here as a historical record.
        </p>
      </div>
    );
  }

  // Group sessions by date
  const sessionsByDate = sessions.reduce((acc, session) => {
    const date = new Date(session.created_at).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
    if (!acc[date]) {
      acc[date] = [];
    }
    acc[date].push(session);
    return acc;
  }, {} as Record<string, ResearchSession[]>);

  return (
    <div className="space-y-6">
      <div className="text-sm text-muted-foreground">
        {sessions.length} {sessions.length === 1 ? 'session' : 'sessions'} recorded
      </div>

      {/* Timeline */}
      <div className="space-y-6">
        {Object.entries(sessionsByDate).map(([date, dateSessions]) => (
          <div key={date}>
            {/* Date Header */}
            <div className="flex items-center gap-2 mb-3 text-sm font-semibold text-muted-foreground">
              <Calendar className="h-4 w-4" />
              {date}
            </div>

            {/* Sessions for this date */}
            <div className="space-y-3 ml-6 border-l-2 border-border pl-4">
              {dateSessions.map((session) => {
                const time = new Date(session.created_at).toLocaleTimeString('en-US', {
                  hour: '2-digit',
                  minute: '2-digit'
                });

                return (
                  <div
                    key={session.session_id}
                    className="rounded-lg border border-border bg-card p-4 hover:shadow-sm hover:border-primary/50 transition-all duration-200"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3 flex-1">
                        <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
                          <Search className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-sm mb-1">Research Session</h3>
                          <p className="text-xs text-muted-foreground">
                            {time}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-muted">
                        <Lightbulb className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
                        <span className="text-xs font-medium">
                          {session.idea_count} {session.idea_count === 1 ? 'idea' : 'ideas'}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
