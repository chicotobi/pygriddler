"""
Example script showing how to create and solve a custom puzzle from a dict structure.
"""

from puzzle import Puzzle
import matplotlib.pyplot as plt

plt.ion()

# Example: Simple 5x5 black and white puzzle (heart shape)
simple_puzzle = {
    "id0": "tobi_heart",
    "desc": "Tobi's heart puzzle - 5 x 5 x 2",
    "x": 5,
    "y": 5,
    "n_colors": 2,
    "colors": ["ffffff", "000000"],  # white, black
    "lines": {
        "horizontal": {
            0: {"block_colors": [1], "block_lengths": [1]},
            1: {"block_colors": [1, 1], "block_lengths": [1, 1]},
            2: {"block_colors": [1, 1], "block_lengths": [1, 1]},
            3: {"block_colors": [1], "block_lengths": [3]},
            4: {"block_colors": [1], "block_lengths": [5]},
        },
        "vertical": {
            0: {"block_colors": [1, 1], "block_lengths": [1, 1]},
            1: {"block_colors": [1, 1], "block_lengths": [1, 2]},
            2: {"block_colors": [1, 1], "block_lengths": [1, 2]},
            3: {"block_colors": [1, 1], "block_lengths": [1, 2]},
            4: {"block_colors": [1, 1], "block_lengths": [1, 1]},
        }
    }
}

# Create puzzle from dictionary using the class method
puzzle = Puzzle.from_dict(simple_puzzle, limit_generate=2, strategy='assumption')
puzzle.initialize()

puzzle.solve(do_plot=True)

plt.ioff()  # Turn off interactive mode
plt.show()  # Show the final plot and wait 