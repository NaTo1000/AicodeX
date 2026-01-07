// Package hotkey provides hotkey management for AicodeX
package hotkey

// Hotkey represents a hotkey binding
type Hotkey struct {
	Key         string
	Modifiers   []string
	Description string
	Action      func()
}

// Matches checks if the given key and modifiers match this hotkey
func (h *Hotkey) Matches(key string, modifiers []string) bool {
	if h.Key != key {
		return false
	}
	if len(h.Modifiers) != len(modifiers) {
		return false
	}
	modMap := make(map[string]bool)
	for _, m := range modifiers {
		modMap[m] = true
	}
	for _, m := range h.Modifiers {
		if !modMap[m] {
			return false
		}
	}
	return true
}

// Trigger executes the hotkey action
func (h *Hotkey) Trigger() bool {
	if h.Action != nil {
		h.Action()
		return true
	}
	return false
}

// Manager manages hotkey bindings
type Manager struct {
	hotkeys []*Hotkey
	enabled bool
}

// NewManager creates a new hotkey manager
func NewManager() *Manager {
	return &Manager{
		hotkeys: make([]*Hotkey, 0),
		enabled: true,
	}
}

// IsEnabled returns whether the manager is enabled
func (m *Manager) IsEnabled() bool {
	return m.enabled
}

// Enable enables the hotkey manager
func (m *Manager) Enable() {
	m.enabled = true
}

// Disable disables the hotkey manager
func (m *Manager) Disable() {
	m.enabled = false
}

// Register registers a new hotkey
func (m *Manager) Register(h *Hotkey) bool {
	for _, existing := range m.hotkeys {
		if existing.Matches(h.Key, h.Modifiers) {
			return false
		}
	}
	m.hotkeys = append(m.hotkeys, h)
	return true
}

// Unregister removes a hotkey
func (m *Manager) Unregister(key string, modifiers []string) bool {
	for i, h := range m.hotkeys {
		if h.Matches(key, modifiers) {
			m.hotkeys = append(m.hotkeys[:i], m.hotkeys[i+1:]...)
			return true
		}
	}
	return false
}

// Process processes a key press
func (m *Manager) Process(key string, modifiers []string) bool {
	if !m.enabled {
		return false
	}
	for _, h := range m.hotkeys {
		if h.Matches(key, modifiers) {
			return h.Trigger()
		}
	}
	return false
}

// ListHotkeys returns all registered hotkeys
func (m *Manager) ListHotkeys() []*Hotkey {
	result := make([]*Hotkey, len(m.hotkeys))
	copy(result, m.hotkeys)
	return result
}
