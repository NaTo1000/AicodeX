package overlay

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestDefaultConfig(t *testing.T) {
	config := DefaultConfig()
	assert.True(t, config.Enabled)
	assert.InDelta(t, 0.9, config.Opacity, 0.001)
	assert.Equal(t, 800, config.Width)
	assert.Equal(t, 600, config.Height)
}

func TestNewOverlay(t *testing.T) {
	o := New(nil)
	assert.NotNil(t, o)
	assert.False(t, o.IsVisible())
}

func TestShowOverlay(t *testing.T) {
	o := New(nil)
	result := o.Show()
	assert.True(t, result)
	assert.True(t, o.IsVisible())
}

func TestShowDisabledOverlay(t *testing.T) {
	config := &Config{Enabled: false}
	o := New(config)
	result := o.Show()
	assert.False(t, result)
	assert.False(t, o.IsVisible())
}

func TestHideOverlay(t *testing.T) {
	o := New(nil)
	o.Show()
	result := o.Hide()
	assert.True(t, result)
	assert.False(t, o.IsVisible())
}

func TestToggleOverlay(t *testing.T) {
	o := New(nil)
	o.Toggle()
	assert.True(t, o.IsVisible())
	o.Toggle()
	assert.False(t, o.IsVisible())
}
