"""
Nonogram solver - supports both Python and C++ solvers
Usage: Modify the settings at the top of the file
"""

import json
import os
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np

from puzzle_loader import load_puzzle
from solution import initialize as py_initialize, solve as py_solve
from utils import plot as plot_utils, create_data_from_color_possible

# ============================================================
# SETTINGS - Modify these
# ============================================================
USE_CPP_SOLVER = False  # Set to True to use C++ solver, False for Python
EXAMPLE = 8              # Example number (1-9) or direct puzzle ID
PLOT = True              # Show visualization
VERBOSE = True           # Show solving progress
LIMIT_GENERATE = 5_000_000

# ============================================================
# Load puzzle
# ============================================================
puzzle = load_puzzle(EXAMPLE)
puzzle["limit_generate"] = LIMIT_GENERATE
puzzle["plot"] = PLOT

print(f"\nPuzzle: ID {puzzle['id']}")
print(f"Size: {puzzle['width']} x {puzzle['height']}")
print(f"Colors: {puzzle['n_colors']}")

# ============================================================
# Solve
# ============================================================
if PLOT:
    plt.ion() 

if USE_CPP_SOLVER:
    # C++ Solver
    from nonogram_cpp import NonogramSolver
    
    print("\n" + "="*60)
    print("C++ SOLVER")
    print("="*60)
    
    solver = NonogramSolver(
        puzzle['width'], puzzle['height'], puzzle['n_colors'],
        puzzle['h_constraints'], puzzle['v_constraints']
    )
    solver.initialize(LIMIT_GENERATE)
    solution = solver.solve(VERBOSE)
    
    unsolved = np.sum(solution == -1)
    if unsolved == 0:
        print("\n[SOLVED] PUZZLE SOLVED!")
    else:
        print(f"\n[PARTIAL] PARTIAL SOLUTION ({unsolved} cells remaining)")
    
    # Convert C++ solution to color_possible format for plotting
    color_possible = np.zeros((puzzle['width'], puzzle['height'], puzzle['n_colors']))
    for y in range(puzzle['height']):
        for x in range(puzzle['width']):
            if solution[y, x] == -1:
                color_possible[x, y, :] = 1.0 / puzzle['n_colors']
            else:
                color_possible[x, y, int(solution[y, x])] = 1.0
    
    # Plot if requested
    if PLOT:
        plot_utils(f"Puzzle {puzzle['id']}", "Final", color_possible, puzzle['colors'], 0)

else:
    # Python Solver
    print("\n" + "="*60)
    print("PYTHON SOLVER")
    print("="*60)
    
    py_initialize(puzzle, verbose=VERBOSE)
    solution = py_solve(puzzle, verbose=VERBOSE)
    
    unsolved = np.sum(solution == -1)
    if unsolved == 0:
        print("\n[SOLVED] PUZZLE SOLVED!")
    else:
        print(f"\n[PARTIAL] PARTIAL SOLUTION ({unsolved} cells remaining)")
    
    # Get color_possible for plotting
    color_possible = create_data_from_color_possible(
        np.array([[[1.0 if solution[y, x] == c else 0.0 
                    for c in range(puzzle['n_colors'])] 
                   for x in range(puzzle['width'])] 
                  for y in range(puzzle['height'])])
    )

# ============================================================
# Save solution
# ============================================================
solver_type = "cpp" if USE_CPP_SOLVER else "python"
os.makedirs(f'solutions/{solver_type}', exist_ok=True)
os.makedirs('solutions/png', exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"solutions/{solver_type}/{puzzle['id']}.json"

# Convert constraints to JSON-serializable format (remove numpy arrays)
h_constraints_clean = [
    {"block_lengths": c["block_lengths"], "block_colors": c["block_colors"]}
    for c in puzzle['h_constraints']
]
v_constraints_clean = [
    {"block_lengths": c["block_lengths"], "block_colors": c["block_colors"]}
    for c in puzzle['v_constraints']
]

solution_data = {
    "puzzle": {
        "id": puzzle['id'],
        "width": puzzle['width'],
        "height": puzzle['height'],
        "n_colors": puzzle['n_colors'],
        "colors": puzzle['colors'],
        "h_constraints": h_constraints_clean,
        "v_constraints": v_constraints_clean
    },
    "solution": {
        "solver": solver_type,
        "timestamp": timestamp,
        "grid": solution.tolist(),
        "solved": bool(unsolved == 0),
        "unsolved_cells": int(unsolved)
    }
}

with open(filename, 'w') as f:
    json.dump(solution_data, f, indent=2)

print(f"\n[SAVED] Solution saved to: {filename}")

# ============================================================
# Save PNG plot
# ============================================================
png_filename = f"solutions/png/{puzzle['id']}.png"

# Create colormap with gray for unsolved cells
colors_with_gray = ['808080'] + puzzle['colors']
cmap = [tuple(int(hx[i:i+2], 16)/256 for i in (0, 2, 4)) for hx in colors_with_gray]
import matplotlib.colors
cmap = matplotlib.colors.ListedColormap(cmap)

# Create figure for saving
fig, ax = plt.subplots(figsize=(puzzle['width']/2, puzzle['height']/2))
ax.imshow(solution, interpolation='nearest', cmap=cmap, vmin=-1, vmax=len(colors_with_gray)-1)
ax.set_title(f"Puzzle {puzzle['id']} - {solver_type.upper()}")
ax.axis('off')
plt.tight_layout()
plt.savefig(png_filename, dpi=100, bbox_inches='tight')
plt.close(fig)

print(f"[SAVED] Plot saved to: {png_filename}")

# ============================================================
# Finish
# ============================================================
if PLOT:
    plt.ioff()
    plt.show()  