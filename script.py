from puzzle import Puzzle
import matplotlib.pyplot as plt
import time
from puzzle_line import _time_unique, _time_keep

plt.ion()

# Create and initialize the puzzle
puzzle = Puzzle(
    puzzle_id=8, limit_generate=100_000, strategy="assumption", check_ungenerated=True
)
puzzle.initialize()

# Start full runtime timer
script_start = time.perf_counter()
puzzle.solve(do_plot=True)

# Calculate total runtime
total_runtime = time.perf_counter() - script_start

# Get the bottleneck timing from puzzle_line module
remaining_operations = total_runtime - _time_unique - _time_keep

print("\n--- Runtime Summary ---")
print(
    f"Calculating unique:   {_time_unique:6.2f} seconds = {(_time_unique / total_runtime * 100):6.2f} %"
)
print(
    f"Calculating keep:     {_time_keep:6.2f} seconds = {(_time_keep / total_runtime * 100):6.2f} %"
)
print(
    f"Other operations:     {remaining_operations:6.2f} seconds = {(remaining_operations / total_runtime * 100):6.2f} % "
)
print(f"Total runtime:        {total_runtime:6.2f} seconds = 100.00 %")

# Save the solution
puzzle.save_solution()
puzzle.save_plot()

plt.ioff()  # Turn off interactive mode
plt.show()  # Show the final plot and wait
