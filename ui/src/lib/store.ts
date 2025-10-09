/**
 * Settings store wrapper for UI configuration persistence
 * Uses Tauri commands to store settings in JSON file
 */

import { invoke } from "@tauri-apps/api";

// UI Configuration Interface
export interface UIConfig {
  theme: "light" | "dark" | "system";
  lastModel: string;
  lastMode: "one_click" | "focused";
  windowWidth?: number;
  windowHeight?: number;
}

// Default configuration
const DEFAULT_CONFIG: UIConfig = {
  theme: "system",
  lastModel: "gpt-4o",
  lastMode: "one_click",
};

/**
 * Get a setting value
 */
async function getSetting<T>(key: string): Promise<T | null> {
  try {
    return await invoke<T | null>("get_setting", { key });
  } catch (error) {
    console.error(`Failed to get setting ${key}:`, error);
    return null;
  }
}

/**
 * Set a setting value
 */
async function setSetting(key: string, value: any): Promise<void> {
  try {
    await invoke("set_setting", { key, value });
  } catch (error) {
    console.error(`Failed to set setting ${key}:`, error);
  }
}

/**
 * Get UI configuration
 */
export async function getUIConfig(): Promise<UIConfig> {
  const theme = (await getSetting<string>("theme")) || DEFAULT_CONFIG.theme;
  const lastModel = (await getSetting<string>("lastModel")) || DEFAULT_CONFIG.lastModel;
  const lastMode = (await getSetting<string>("lastMode")) || DEFAULT_CONFIG.lastMode;
  const windowWidth = await getSetting<number>("windowWidth");
  const windowHeight = await getSetting<number>("windowHeight");

  return {
    theme: theme as UIConfig["theme"],
    lastModel,
    lastMode: lastMode as UIConfig["lastMode"],
    windowWidth: windowWidth ?? undefined,
    windowHeight: windowHeight ?? undefined,
  };
}

/**
 * Set theme preference
 */
export async function setTheme(theme: UIConfig["theme"]): Promise<void> {
  await setSetting("theme", theme);
}

/**
 * Set last used model
 */
export async function setLastModel(model: string): Promise<void> {
  await setSetting("lastModel", model);
}

/**
 * Set last used mode
 */
export async function setLastMode(mode: UIConfig["lastMode"]): Promise<void> {
  await setSetting("lastMode", mode);
}

/**
 * Set window dimensions
 */
export async function setWindowSize(width: number, height: number): Promise<void> {
  await setSetting("windowWidth", width);
  await setSetting("windowHeight", height);
}
