from download import get_input
from solution import initialize, solve
import matplotlib.pyplot as plt
import sys
import os.path
import time

plt.ion()

inp = {}
inp["limit_generate"] = 5_000_000
inp["plot"] = True
inp["example"] = 276557

# Redirect stdout to file
# sys.stdout = open('output.txt', 'w')


inp = get_input(inp)
initialize(inp)

# Start full runtime timer
script_start = time.perf_counter()
solve(inp)

# Calculate total runtime
total_runtime = time.perf_counter() - script_start

# Get the bottleneck timing from puzzle_line module
from puzzle_line import _time_unique, _time_keep

remaining_operations = total_runtime - _time_unique - _time_keep

print("\n--- Runtime Summary ---")
print(f"Calculating unique:   {_time_unique:6.2f} seconds = {(_time_unique/total_runtime*100):6.2f} %")
print(f"Calculating keep:     {_time_keep:6.2f} seconds = {(_time_keep/total_runtime*100):6.2f} %")
print(f"Other operations:     {remaining_operations:6.2f} seconds = {(remaining_operations/total_runtime*100):6.2f} % ")
print(f"Total runtime:        {total_runtime:6.2f} seconds = 100.00 %")

# Restore stdout
# sys.stdout.close()
# sys.stdout = sys.__stdout__

# Compare output with blueprint
# compare_output_with_blueprint(inp["id0"])

plt.ioff()  # Turn off interactive mode
plt.show()  # Show the final plot and wait  