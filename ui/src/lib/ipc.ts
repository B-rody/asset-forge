/**
 * IPC Communication Layer
 * Handles JSON-Lines communication with Python backend over stdio
 */

export interface IPCCommand {
  cmd: string;
  mode?: string;
  params?: Record<string, any>;
}

export interface IPCEvent {
  event: string;
  step?: string;
  message?: string;
  pct?: number;
  status?: string;
  score?: number;
  result?: any;
}

export type IPCEventHandler = (event: IPCEvent) => void;

class IPCClient {
  private handlers: Set<IPCEventHandler> = new Set();

  /**
   * Subscribe to IPC events from backend
   */
  subscribe(handler: IPCEventHandler): () => void {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  /**
   * Send command to backend
   */
  async sendCommand(command: IPCCommand): Promise<void> {
    // In development, simulate backend responses
    if (import.meta.env.DEV) {
      this.simulateBackendResponse(command);
      return;
    }

    // TODO: In production, use Tauri's Command API to invoke sidecar
    // await invoke('send_to_sidecar', { command });
  }

  /**
   * Simulate backend responses for development/testing
   */
  private simulateBackendResponse(command: IPCCommand): void {
    const steps = ["Researcher", "Planner", "Maker", "Packager"];
    let currentStep = 0;

    // Simulate initial log
    setTimeout(() => {
      this.emit({
        event: "log",
        step: steps[0],
        message: "Starting pipeline...",
      });
    }, 500);

    // Simulate progress through steps
    const progressInterval = setInterval(() => {
      if (currentStep >= steps.length) {
        clearInterval(progressInterval);
        
        // Emit completion
        setTimeout(() => {
          this.emit({
            event: "done",
            result: {
              bundle_id: `2025-10-07-${command.mode || "test"}-bundle`,
              output_path: "data/2025-10-07/bundle.zip",
            },
          });
        }, 500);
        return;
      }

      const step = steps[currentStep];
      
      // Log step start
      this.emit({
        event: "log",
        step,
        message: `Processing ${step}...`,
      });

      // Simulate progress
      for (let pct = 0; pct <= 100; pct += 25) {
        setTimeout(() => {
          this.emit({
            event: "progress",
            step,
            pct,
          });
        }, (pct / 100) * 2000);
      }

      currentStep++;
    }, 3000);
  }

  /**
   * Emit event to all subscribers
   */
  private emit(event: IPCEvent): void {
    this.handlers.forEach((handler) => handler(event));
  }
}

export const ipcClient = new IPCClient();
