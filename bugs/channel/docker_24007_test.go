package channel

import (
	"fmt"
	"testing"
	"time"
)

// Source: https://github.com/system-pclub/go-concurrency-bugs
// Docker #24007: two goroutines may both enter default before close.
// The extra channels force this interleaving for a minimal reproduction.
func TestDocker24007(t *testing.T) {
	closed := make(chan struct{})
	ready := make(chan struct{}, 2)
	release := make(chan struct{})
	results := make(chan string, 2)

	worker := func() {
		defer func() {
			if err := recover(); err != nil {
				results <- fmt.Sprint(err)
			}
		}()

		select {
		case <-closed:
			results <- "already closed"
		default:
			ready <- struct{}{}
			<-release
			close(closed)
			results <- "closed successfully"
		}
	}

	go worker()
	go worker()

	<-ready
	<-ready
	close(release)

	successes := 0
	panics := 0
	timer := time.NewTimer(5 * time.Second)
	defer timer.Stop()

	for i := 0; i < 2; i++ {
		select {
		case result := <-results:
			t.Log(result)
			if result == "closed successfully" {
				successes++
			} else if result == "close of closed channel" {
				panics++
			} else {
				t.Fatalf("unexpected result: %s", result)
			}
		case <-timer.C:
			t.Fatal("timed out waiting for workers")
		}
	}

	if successes != 1 || panics != 1 {
		t.Fatalf("expected one close and one panic; got %d closes, %d panics",
			successes, panics)
	}

	t.Log("REPRODUCED: concurrent close caused one panic")
}
