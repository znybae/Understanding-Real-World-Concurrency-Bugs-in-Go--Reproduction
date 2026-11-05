package main

import (
	"fmt"
	"sync"
)

// Minimal reproduction of Figure 5 in
// "Understanding Real-World Concurrency Bugs in Go".
// Trigger: at least two tasks, with Wait incorrectly inside the loop.
func main() {
	const tasks = 2
	var group sync.WaitGroup
	group.Add(tasks)

	for i := 0; i < tasks; i++ {
		fmt.Printf("Starting task %d\n", i)

		go func(id int) {
			defer group.Done()
			fmt.Printf("Task %d finished\n", id)
		}(i)

		fmt.Println("Waiting inside the loop")
		group.Wait() // BUG: prevents the next task from starting.
	}

	fmt.Println("All tasks completed")
}
