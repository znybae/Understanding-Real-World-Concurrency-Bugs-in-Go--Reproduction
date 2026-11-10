package channel

import (
	"testing"
	"time"
)

// Minimal reproduction of Kubernetes #5316, Figure 1.
// Source: https://songlh.github.io/paper/go-study.pdf
// Hold the worker until the parent times out, then attempt an unbuffered send.
func TestK8s5316(t *testing.T) {
	result := make(chan int)
	work := make(chan struct{})
	attempting := make(chan struct{})
	done := make(chan struct{})

	go func() {
		<-work
		value := 42
		close(attempting)
		result <- value
		close(done)
	}()

	select {
	case <-result:
		t.Fatal("unexpected result before timeout")
	case <-time.After(10 * time.Millisecond):
		t.Log("parent timed out and stopped receiving")
	}

	close(work)

	select {
	case <-attempting:
	case <-time.After(time.Second):
		t.Fatal("worker did not reach the send")
	}

	select {
	case <-done:
		t.Fatal("unexpected completion without a receiver")
	case <-time.After(100 * time.Millisecond):
		t.Log("REPRODUCED: worker cannot finish sending without a receiver")
	}

	// Test-only cleanup: receive the value so repeated tests leave no leaked worker.
	select {
	case value := <-result:
		t.Logf("cleanup received result: %d", value)
	case <-time.After(time.Second):
		t.Fatal("cleanup could not receive the result")
	}

	select {
	case <-done:
		t.Log("worker exited after test cleanup")
	case <-time.After(time.Second):
		t.Fatal("worker did not exit after cleanup")
	}
}
