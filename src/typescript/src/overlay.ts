/**
 * Overlay module for AicodeX
 */

export interface OverlayConfig {
  enabled: boolean;
  opacity: number;
  positionX: number;
  positionY: number;
  width: number;
  height: number;
}

const defaultConfig: OverlayConfig = {
  enabled: true,
  opacity: 0.9,
  positionX: 0,
  positionY: 0,
  width: 800,
  height: 600,
};

export class Overlay {
  private config: OverlayConfig;
  private visible: boolean = false;

  constructor(config?: Partial<OverlayConfig>) {
    this.config = { ...defaultConfig, ...config };
  }

  isVisible(): boolean {
    return this.visible;
  }

  show(): boolean {
    if (!this.config.enabled) {
      return false;
    }
    this.visible = true;
    return true;
  }

  hide(): boolean {
    this.visible = false;
    return true;
  }

  toggle(): boolean {
    if (this.visible) {
      return this.hide();
    }
    return this.show();
  }

  getConfig(): Readonly<OverlayConfig> {
    return { ...this.config };
  }
}
