package main

import "testing"

// Run with -race to check the version using a private copy of i.
func TestDockerRaceFixed(t *testing.T) {
	main()
}
