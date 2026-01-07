/**
 * AicodeX - A companion overlay code engine
 */

export interface EngineConfig {
  debug?: boolean;
  hotkeys?: Record<string, string>;
}

export class Engine {
  private running: boolean = false;
  private config: EngineConfig;

  constructor(config: EngineConfig = {}) {
    this.config = config;
  }

  /**
   * Start the engine
   */
  public start(): boolean {
    this.running = true;
    return true;
  }

  /**
   * Stop the engine
   */
  public stop(): boolean {
    this.running = false;
    return true;
  }

  /**
   * Check if engine is running
   */
  public isRunning(): boolean {
    return this.running;
  }

  /**
   * Get engine configuration
   */
  public getConfig(): EngineConfig {
    return { ...this.config };
  }
}

export const VERSION = '0.1.0';
