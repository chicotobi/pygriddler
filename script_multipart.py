"""Example script for solving multi-part puzzles."""

from multipart_puzzle import MultiPartPuzzle
import matplotlib.pyplot as plt
import time

plt.ion()

# Define the Sweet Violets multi-part puzzle (80275-80278)
# Assuming a 2x2 layout (adjust if you know the actual layout)
# mp_puzzle = MultiPartPuzzle(
#     start_id=80275,
#     end_id=80278,
#     layout=(2, 2),  # 2 rows, 2 columns
#     limit_generate=1_000_000,
#     strategy="force_generate",
#     check_ungenerated=True,
# )

mp_puzzle = MultiPartPuzzle(
    start_id=203094,
    end_id=203109,
    layout=(4, 4),  # 4 rows, 4 columns
    limit_generate=1_000_000,
    strategy="force_generate",
    check_ungenerated=True,
)

# Print information about the parts
print("\n" + "="*60)
print(mp_puzzle.get_part_info())
print("="*60 + "\n")

# Solve all parts
start = time.perf_counter()
mp_puzzle.solve_all(do_plot=False, benchmark_output=False)
elapsed = time.perf_counter() - start

print(f"\nTotal solving time: {elapsed:.2f}s")

# Save individual solutions
mp_puzzle.save_all_solutions()
mp_puzzle.save_all_plots()

# Plot the assembled result
mp_puzzle.plot_assembled(
    title="Sweet Violets (Multi-part 80275-80278)",
    save_path="solutions/multipart_80275-80278.png"
)

plt.ioff()
plt.show()
