import { HotkeyManager, createHotkey } from './hotkey';

describe('Hotkey', () => {
  describe('createHotkey', () => {
    it('should create a hotkey with default values', () => {
      const hotkey = createHotkey('a');
      expect(hotkey.key).toBe('a');
      expect(hotkey.modifiers.size).toBe(0);
      expect(hotkey.description).toBe('');
    });

    it('should create a hotkey with modifiers', () => {
      const hotkey = createHotkey('a', ['ctrl', 'shift']);
      expect(hotkey.modifiers.has('ctrl')).toBe(true);
      expect(hotkey.modifiers.has('shift')).toBe(true);
    });
  });
});

describe('HotkeyManager', () => {
  describe('registration', () => {
    it('should register a hotkey', () => {
      const manager = new HotkeyManager();
      const hotkey = createHotkey('a', ['ctrl']);
      const result = manager.register(hotkey);
      expect(result).toBe(true);
      expect(manager.listHotkeys()).toHaveLength(1);
    });

    it('should reject duplicate hotkeys', () => {
      const manager = new HotkeyManager();
      manager.register(createHotkey('a', ['ctrl']));
      const result = manager.register(createHotkey('a', ['ctrl']));
      expect(result).toBe(false);
      expect(manager.listHotkeys()).toHaveLength(1);
    });

    it('should unregister a hotkey', () => {
      const manager = new HotkeyManager();
      manager.register(createHotkey('a', ['ctrl']));
      const result = manager.unregister('a', ['ctrl']);
      expect(result).toBe(true);
      expect(manager.listHotkeys()).toHaveLength(0);
    });
  });

  describe('processing', () => {
    it('should process matching hotkey', () => {
      const manager = new HotkeyManager();
      let triggered = false;
      manager.register(createHotkey('a', ['ctrl'], '', () => { triggered = true; }));
      const result = manager.process('a', ['ctrl']);
      expect(result).toBe(true);
      expect(triggered).toBe(true);
    });

    it('should not process when disabled', () => {
      const manager = new HotkeyManager();
      let triggered = false;
      manager.register(createHotkey('a', [], '', () => { triggered = true; }));
      manager.disable();
      const result = manager.process('a');
      expect(result).toBe(false);
      expect(triggered).toBe(false);
    });
  });
});
