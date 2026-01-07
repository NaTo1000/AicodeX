import { Overlay } from './overlay';

describe('Overlay', () => {
  describe('OverlayConfig defaults', () => {
    it('should have correct default values', () => {
      const overlay = new Overlay();
      const config = overlay.getConfig();
      expect(config.enabled).toBe(true);
      expect(config.opacity).toBe(0.9);
      expect(config.width).toBe(800);
      expect(config.height).toBe(600);
    });
  });

  describe('visibility', () => {
    it('should start hidden', () => {
      const overlay = new Overlay();
      expect(overlay.isVisible()).toBe(false);
    });

    it('should show overlay when enabled', () => {
      const overlay = new Overlay();
      const result = overlay.show();
      expect(result).toBe(true);
      expect(overlay.isVisible()).toBe(true);
    });

    it('should not show overlay when disabled', () => {
      const overlay = new Overlay({ enabled: false });
      const result = overlay.show();
      expect(result).toBe(false);
      expect(overlay.isVisible()).toBe(false);
    });

    it('should hide overlay', () => {
      const overlay = new Overlay();
      overlay.show();
      const result = overlay.hide();
      expect(result).toBe(true);
      expect(overlay.isVisible()).toBe(false);
    });

    it('should toggle visibility', () => {
      const overlay = new Overlay();
      overlay.toggle();
      expect(overlay.isVisible()).toBe(true);
      overlay.toggle();
      expect(overlay.isVisible()).toBe(false);
    });
  });
});
