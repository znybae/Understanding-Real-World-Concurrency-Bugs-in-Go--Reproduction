package channel

import (
	"testing"
	"time"
)

// Minimal model of Kubernetes #5316, Figure 1.
// Source: https://songlh.github.io/paper/go-study.pdf
// Force the parent to time out before the worker sends its result.
func TestK8s5316(t *testing.T) {
	result := make(chan int)
	work := make(chan struct{})
	done := make(chan struct{})

	go func() {
		<-work
		result <- 42
		close(done)
	}()

	select {
	case <-result:
		t.Fatal("unexpected result before timeout")
	case <-time.After(10 * time.Millisecond):
		t.Log("Parent timed out and stopped receiving")
	}

	close(work)

	t.Log("Worker will block sending to the unbuffered channel")

	// Test-only wait: keep the process alive to expose the blocked worker.
	// Without a receiver, the worker cannot close done.
	<-done
}
