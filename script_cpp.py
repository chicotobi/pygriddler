from download import get_input
from nonogram_cpp import NonogramSolver
from utils import create_data_from_color_possible, plot as plot_utils
import matplotlib.pyplot as plt
import numpy as np

plt.ion()

inp = {}
inp["limit_generate"] = 5_000_000
inp["plot"] = True
inp["example"] = 5  # Change this to any example number or puzzle ID

# Load puzzle
get_input(inp)

print(f"Solving: {inp['desc']}")

# Horizontal constraints (rows) - status[1]
h_constraints = []
for i in range(inp['y']):
    constraint = inp['status'][1][i]
    h_constraints.append({
        "block_lengths": constraint["block_lengths"],
        "block_colors": constraint["block_colors"]
    })

# Vertical constraints (columns) - status[0]
v_constraints = []
for i in range(inp['x']):
    constraint = inp['status'][0][i]
    v_constraints.append({
        "block_lengths": constraint["block_lengths"],
        "block_colors": constraint["block_colors"]
    })

# Solve with C++
solver = NonogramSolver(inp['x'], inp['y'], inp['n_colors'], h_constraints, v_constraints)
solver.initialize(inp['limit_generate'])
solution = solver.solve(False)

unsolved = np.sum(solution == -1)
if unsolved == 0:
    print("✓ SOLVED!")
else:
    print(f"PARTIAL: {unsolved} unsolved cells")

# Plot if requested - convert solution to color_possible format for plotting
if inp["plot"]:
    # C++ solver returns solution in (y, x) format
    # Convert to color_possible (x, y, n_colors) format for the plot function
    # Note: color_possible has x as first dimension, y as second dimension
    color_possible = np.zeros((inp['x'], inp['y'], inp['n_colors']))
    for y in range(inp['y']):
        for x in range(inp['x']):
            if solution[y, x] == -1:
                # Unsolved - all colors possible
                color_possible[x, y, :] = 1.0 / inp['n_colors']
            else:
                # Solved - only one color
                color_possible[x, y, int(solution[y, x])] = 1.0
    
    # ori=0 means normal orientation (x, y, colors)
    # The plot function will display it correctly
    plot_utils(inp['desc'], "Final", color_possible, inp['colors'], 0)
    
    plt.ioff()
    plt.show()
