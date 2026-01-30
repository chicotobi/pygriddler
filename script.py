from puzzle import Puzzle
import matplotlib.pyplot as plt
import time

plt.ion()

# Create the puzzle
puzzle = Puzzle(
    puzzle_id=8, limit_generate=1_000_000, strategy="guess", check_ungenerated=True
)

# Solve the puzzle and time the execution
start = time.perf_counter()
puzzle.solve(do_plot=False)
t_total = time.perf_counter() - start

# Get benchmark timing from puzzle_line module
from puzzle_line import t_keep, t_unique, t_generate_lines, t_calculate_count, t_calculate_slice
t_other = t_total - t_unique - t_keep - t_generate_lines - t_calculate_count - t_calculate_slice
fac = 100 / t_total

print("\n--- Runtime Summary ---")
print(f"Calculating unique:   {t_unique:6.2f} s = {(t_unique * fac):6.2f} %")
print(f"Calculating keep:     {t_keep:6.2f} s = {(t_keep * fac):6.2f} %")
print(f"Calculating count:    {t_calculate_count:6.2f} s = {(t_calculate_count * fac):6.2f} % ")
print(f"Generating lines:     {t_generate_lines:6.2f} s = {(t_generate_lines * fac):6.2f} % ")
print(f"Calculating slice:    {t_calculate_slice:6.2f} s = {(t_calculate_slice * fac):6.2f} % ")
print(f"Other operations:     {t_other:6.2f} s = {(t_other * fac):6.2f} % ")
print(f"Total runtime:        {t_total:6.2f} s = 100.00 %")

# Save the solution
puzzle.save_solution()
puzzle.save_plot()

plt.ioff()  # Turn off interactive mode
plt.show()  # Show the final plot and wait
