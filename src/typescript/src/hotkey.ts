/**
 * Hotkey management module for AicodeX
 */

export interface Hotkey {
  key: string;
  modifiers: Set<string>;
  description: string;
  action?: () => void;
}

export function createHotkey(
  key: string,
  modifiers: string[] = [],
  description: string = '',
  action?: () => void
): Hotkey {
  return {
    key,
    modifiers: new Set(modifiers),
    description,
    action,
  };
}

function hotkeyMatches(hotkey: Hotkey, key: string, modifiers: Set<string>): boolean {
  if (hotkey.key !== key) return false;
  if (hotkey.modifiers.size !== modifiers.size) return false;
  for (const mod of hotkey.modifiers) {
    if (!modifiers.has(mod)) return false;
  }
  return true;
}

export class HotkeyManager {
  private hotkeys: Hotkey[] = [];
  private enabled: boolean = true;

  isEnabled(): boolean {
    return this.enabled;
  }

  enable(): void {
    this.enabled = true;
  }

  disable(): void {
    this.enabled = false;
  }

  register(hotkey: Hotkey): boolean {
    for (const existing of this.hotkeys) {
      if (hotkeyMatches(existing, hotkey.key, hotkey.modifiers)) {
        return false;
      }
    }
    this.hotkeys.push(hotkey);
    return true;
  }

  unregister(key: string, modifiers: string[] = []): boolean {
    const modSet = new Set(modifiers);
    const index = this.hotkeys.findIndex((h) => hotkeyMatches(h, key, modSet));
    if (index >= 0) {
      this.hotkeys.splice(index, 1);
      return true;
    }
    return false;
  }

  process(key: string, modifiers: string[] = []): boolean {
    if (!this.enabled) return false;
    const modSet = new Set(modifiers);
    for (const hotkey of this.hotkeys) {
      if (hotkeyMatches(hotkey, key, modSet)) {
        if (hotkey.action) {
          hotkey.action();
        }
        return true;
      }
    }
    return false;
  }

  listHotkeys(): readonly Hotkey[] {
    return [...this.hotkeys];
  }
}
