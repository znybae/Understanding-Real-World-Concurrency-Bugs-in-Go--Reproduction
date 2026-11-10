package main

import "testing"

// This test intentionally blocks when it reaches Wait inside the loop.
// Run it separately with a test timeout.
func TestWaitGroupDeadlock(t *testing.T) {
	main()
}
