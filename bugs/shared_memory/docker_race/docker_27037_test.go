package main

import "testing"

// Run with -race to detect concurrent accesses to the loop variable.
func TestDockerRace(t *testing.T) {
	main()
}
