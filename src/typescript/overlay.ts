/**
 * Main TypeScript entry point for AicodeX
 */

export interface Config {
  hotkeys: Record<string, string>;
  theme: string;
  opacity: number;
}

export class OverlayManager {
  private config: Config;

  constructor(config: Config) {
    this.config = config;
  }

  public initialize(): void {
    console.log('Overlay Manager initialized');
  }

  public show(): void {
    console.log('Showing overlay');
  }

  public hide(): void {
    console.log('Hiding overlay');
  }

  public updateConfig(newConfig: Partial<Config>): void {
    this.config = { ...this.config, ...newConfig };
  }
}

export default OverlayManager;
