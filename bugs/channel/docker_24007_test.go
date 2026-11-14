package channel

import "testing"

// Minimal model of Docker #24007, Figure 10.
// Source: https://github.com/system-pclub/go-concurrency-bugs
// Force both goroutines into default before either closes the channel.
// Expected result: an unrecovered "close of closed channel" panic.
func TestDocker24007(t *testing.T) {
	closed := make(chan struct{})
	ready := make(chan struct{}, 2)
	release := make(chan struct{})
	done := make(chan struct{}, 2)

	worker := func() {
		select {
		case <-closed:
			done <- struct{}{}
		default:
			ready <- struct{}{}
			<-release
			close(closed)
			done <- struct{}{}
		}
	}

	go worker()
	go worker()

	<-ready
	<-ready

	t.Log("Both workers entered default; releasing concurrent close attempts")
	close(release)

	<-done
	<-done
}
