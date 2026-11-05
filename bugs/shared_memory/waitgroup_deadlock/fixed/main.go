package main

import (
	"fmt"
	"sync"
)

// Figure 5 fix: wait only after all tasks have been started.
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
	}

	fmt.Println("Waiting outside the loop")
	group.Wait()
	fmt.Println("All tasks completed")
}
