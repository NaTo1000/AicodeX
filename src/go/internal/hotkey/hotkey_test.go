package hotkey

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestHotkeyMatches(t *testing.T) {
	h := &Hotkey{Key: "a", Modifiers: []string{"ctrl"}}
	assert.True(t, h.Matches("a", []string{"ctrl"}))
	assert.False(t, h.Matches("b", []string{"ctrl"}))
	assert.False(t, h.Matches("a", []string{}))
}

func TestHotkeyTrigger(t *testing.T) {
	triggered := false
	h := &Hotkey{Key: "a", Action: func() { triggered = true }}
	result := h.Trigger()
	assert.True(t, result)
	assert.True(t, triggered)
}

func TestHotkeyTriggerNoAction(t *testing.T) {
	h := &Hotkey{Key: "a"}
	result := h.Trigger()
	assert.False(t, result)
}

func TestRegisterHotkey(t *testing.T) {
	m := NewManager()
	h := &Hotkey{Key: "a", Modifiers: []string{"ctrl"}}
	result := m.Register(h)
	assert.True(t, result)
	assert.Len(t, m.ListHotkeys(), 1)
}

func TestRegisterDuplicateHotkey(t *testing.T) {
	m := NewManager()
	h1 := &Hotkey{Key: "a", Modifiers: []string{"ctrl"}}
	h2 := &Hotkey{Key: "a", Modifiers: []string{"ctrl"}}
	m.Register(h1)
	result := m.Register(h2)
	assert.False(t, result)
	assert.Len(t, m.ListHotkeys(), 1)
}

func TestUnregisterHotkey(t *testing.T) {
	m := NewManager()
	h := &Hotkey{Key: "a", Modifiers: []string{"ctrl"}}
	m.Register(h)
	result := m.Unregister("a", []string{"ctrl"})
	assert.True(t, result)
	assert.Len(t, m.ListHotkeys(), 0)
}

func TestProcessHotkey(t *testing.T) {
	m := NewManager()
	triggered := false
	h := &Hotkey{Key: "a", Modifiers: []string{"ctrl"}, Action: func() { triggered = true }}
	m.Register(h)
	result := m.Process("a", []string{"ctrl"})
	assert.True(t, result)
	assert.True(t, triggered)
}

func TestProcessWhenDisabled(t *testing.T) {
	m := NewManager()
	triggered := false
	h := &Hotkey{Key: "a", Action: func() { triggered = true }}
	m.Register(h)
	m.Disable()
	result := m.Process("a", []string{})
	assert.False(t, result)
	assert.False(t, triggered)
}
