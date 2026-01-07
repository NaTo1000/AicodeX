// Package main is the entry point for AicodeX CLI
package main

import (
	"fmt"

	"github.com/NaTo1000/AicodeX/src/go/internal/overlay"
)

// Version of the application
const Version = "0.1.0"

func main() {
	fmt.Println("AicodeX - Companion Overlay Code Engine")
	fmt.Printf("Version: %s\n", Version)

	// Initialize overlay
	o := overlay.New(nil)
	fmt.Printf("Overlay enabled: %v\n", o.Config().Enabled)
}
