from puzzle import Puzzle
import matplotlib.pyplot as plt
import time

plt.ion()

# Create the puzzle
puzzle = Puzzle(
    puzzle_id=189048, limit_generate=1_000_000, strategy="guess", check_ungenerated=True
)

# Solve the puzzle and time the execution
start = time.perf_counter()
puzzle.solve(do_plot=True, benchmark_output = True)

# Save the solution
puzzle.save_solution()
puzzle.save_plot()

plt.ioff()  # Turn off interactive mode
plt.show()  # Show the final plot and wait
