/**
 * IPC Communication Layer
 * Handles JSON-Lines communication with Python backend over stdio
 */

import { invoke } from "@tauri-apps/api/tauri";
import { listen } from "@tauri-apps/api/event";

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
  success?: boolean;
  error?: string;
  current_path?: string;
  default_path?: string;
  is_custom?: boolean;
  path?: string;
  count?: number;
  has_key?: boolean;
  research_only?: boolean;
  // Data arrays
  ideas?: any[];
  bundles?: any[];
  activities?: any[];
  sessions?: any[];
  // Stats object
  stats?: any;
  // IDs
  idea_id?: string;
  bundle_id?: string;
}

export type IPCEventHandler = (event: IPCEvent) => void;

class IPCClient {
  private handlers: Set<IPCEventHandler> = new Set();

  constructor() {
    // Listen to backend events from Tauri
    this.setupTauriEventListener();
  }

  /**
   * Setup Tauri event listener to receive events from Python backend
   */
  private async setupTauriEventListener() {
    try {
      await listen<IPCEvent>("backend_event", (event) => {
        // Debug logging to see all backend events
        console.log("📨 Backend event:", event.payload);

        // Forward event to all subscribed handlers
        this.emit(event.payload);
      });
      // Note: unlisten function intentionally not stored - event listener persists for app lifetime
    } catch (error) {
      console.error("Failed to setup Tauri event listener:", error);
    }
  }

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
    // Call backend via Tauri
    try {
      await invoke('send_to_backend', { command });
    } catch (error) {
      console.error('Failed to send command to backend:', error);
      this.emit({
        event: "error",
        message: `Backend error: ${error}`
      });
    }
  }


  /**
   * Emit event to all subscribers
   */
  private emit(event: IPCEvent): void {
    this.handlers.forEach((handler) => handler(event));
  }
}

export const ipcClient = new IPCClient();
