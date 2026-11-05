package main

import (
	"fmt"
	"sync"
)

// Figure 8 fix: pass a copy of i as a function argument.
func main() {
	var group sync.WaitGroup

	for i := 17; i <= 20; i++ {
		group.Add(1)

		go func(i int) {
			defer group.Done()
			apiVersion := fmt.Sprintf("v1.%d", i)
			fmt.Println(apiVersion)
		}(i)
	}

	group.Wait()
}
