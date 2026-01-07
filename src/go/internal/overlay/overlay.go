// Package overlay provides overlay management for AicodeX
package overlay

// Config represents the configuration for the overlay
type Config struct {
	Enabled   bool
	Opacity   float32
	PositionX int
	PositionY int
	Width     int
	Height    int
}

// DefaultConfig returns the default overlay configuration
func DefaultConfig() *Config {
	return &Config{
		Enabled:   true,
		Opacity:   0.9,
		PositionX: 0,
		PositionY: 0,
		Width:     800,
		Height:    600,
	}
}

// Overlay manages the overlay display
type Overlay struct {
	config  *Config
	visible bool
}

// New creates a new Overlay with the given configuration
// If config is nil, DefaultConfig is used
func New(config *Config) *Overlay {
	if config == nil {
		config = DefaultConfig()
	}
	return &Overlay{
		config:  config,
		visible: false,
	}
}

// IsVisible returns whether the overlay is currently visible
func (o *Overlay) IsVisible() bool {
	return o.visible
}

// Show displays the overlay
func (o *Overlay) Show() bool {
	if !o.config.Enabled {
		return false
	}
	o.visible = true
	return true
}

// Hide hides the overlay
func (o *Overlay) Hide() bool {
	o.visible = false
	return true
}

// Toggle toggles the overlay visibility
func (o *Overlay) Toggle() bool {
	if o.visible {
		return o.Hide()
	}
	return o.Show()
}

// Config returns the current configuration
func (o *Overlay) Config() *Config {
	return o.config
}
