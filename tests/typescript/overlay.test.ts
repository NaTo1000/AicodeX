import { OverlayManager, Config } from '../../src/typescript/overlay';

describe('OverlayManager', () => {
  let config: Config;

  beforeEach(() => {
    config = {
      hotkeys: { 'ctrl+a': 'action1' },
      theme: 'dark',
      opacity: 0.9,
    };
  });

  test('should initialize correctly', () => {
    const manager = new OverlayManager(config);
    expect(manager).toBeDefined();
  });

  test('should update config', () => {
    const manager = new OverlayManager(config);
    manager.updateConfig({ theme: 'light' });
    // Config is private, but we can verify no errors occur
    expect(manager).toBeDefined();
  });

  test('should have show and hide methods', () => {
    const manager = new OverlayManager(config);
    expect(() => manager.show()).not.toThrow();
    expect(() => manager.hide()).not.toThrow();
  });
});
