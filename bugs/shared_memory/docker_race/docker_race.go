package main

import (
	"fmt"
	"sync"
)

// Minimal reproduction of Figure 8 in
// "Understanding Real-World Concurrency Bugs in Go".
// Under Go 1.10, the closures share the loop variable i.
func main() {
	var group sync.WaitGroup

	for i := 17; i <= 20; i++ {
		group.Add(1)

		go func() {
			defer group.Done()
			apiVersion := fmt.Sprintf("v1.%d", i)
			fmt.Println(apiVersion)
		}()
	}

	group.Wait()
}
