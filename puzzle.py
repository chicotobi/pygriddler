import numpy as np
import os.path, json, time, copy
import matplotlib.pyplot as plt
from typing import Optional, Literal
from puzzle_line import PuzzleLine
from utils import plot, NoSolutionError, NoUpdateError
from griddler_parser import GriddlerParser


class Puzzle:
    """Represents a nonogram puzzle with color possibilities and puzzle lines."""

    def __init__(
        self,
        puzzle_id: int,
        limit_generate: int = 5_000_000,
        strategy: Literal[None, "force_generate", "guess"] = "force_generate",
        check_ungenerated: bool = True,
    ):
        """Initialize puzzle from puzzle ID.

        Args:
          puzzle_id: Puzzle ID from griddlers.net or example number (1-9).
                     Will download/parse puzzle as needed.
          limit_generate: Maximum number of possible lines to generate for a line
          strategy: Solving strategy when stuck - None, "force_generate" or "guess"
                    - "force_generate": Generate more solutions for complex lines (default)
                    - "guess": Try random pixel assumptions to eliminate possibilities
          check_ungenerated: Whether to check ungenerated lines during solving
        """
        # Load puzzle from ID and get raw JSON data
        parser = GriddlerParser(puzzle_id)
        json_path = parser.ensure_json_exists()

        with open(json_path, "r") as f:
            puzzle_data = json.load(f)

        if strategy not in (None, "force_generate", "guess"):
            raise ValueError(
                f"Invalid strategy '{strategy}': must be None, 'force_generate', or 'guess'"
            )

        # Use from_dict to initialize (reuse common logic)
        puzzle = Puzzle.from_dict(
            puzzle_data, limit_generate, strategy, check_ungenerated
        )

        # Copy all attributes to self
        self.__dict__.update(puzzle.__dict__)

    @classmethod
    def from_dict(
        cls,
        puzzle_dict: dict,
        limit_generate: int = 5_000_000,
        strategy: Literal[None, "force_generate", "guess"] = "force_generate",
        check_ungenerated: bool = True,
    ) -> "Puzzle":
        """Create a Puzzle instance from a custom dictionary structure.

        Uses the same JSON structure as GriddlerParser._translate_raw_to_json():
        {
            "id0": "custom_001",
            "desc": "My custom puzzle description",
            "x": 10,  # width
            "y": 10,  # height
            "n_colors": 2,
            "colors": ["ffffff", "000000"],  # hex color codes
            "lines": {
                "horizontal": {
                    0: {"block_colors": [1, 1], "block_lengths": [3, 2]},
                    1: {"block_colors": [1], "block_lengths": [5]},
                    ...
                },
                "vertical": {
                    0: {"block_colors": [1, 1], "block_lengths": [2, 3]},
                    1: {"block_colors": [1], "block_lengths": [4]},
                    ...
                }
            }
        }

        Note: block_colors are 0-indexed (0=first color, 1=second color, etc.)

        Args:
          puzzle_dict: Dictionary with puzzle structure (see above)
          limit_generate: Maximum number of possible lines to generate for a line
          strategy: Solving strategy - "force_generate" or "guess"
          check_ungenerated: Whether to check ungenerated lines during solving

        Returns:
          Puzzle instance
        """
        # Create a new puzzle instance (bypass normal __init__)
        puzzle = cls.__new__(cls)

        # Set basic attributes
        puzzle.id0 = puzzle_dict.get("id0", "custom")
        puzzle.desc = puzzle_dict.get("desc", "Custom puzzle")
        puzzle.x = puzzle_dict["x"]
        puzzle.y = puzzle_dict["y"]
        puzzle.colors = puzzle_dict["colors"]
        puzzle.n_colors = puzzle_dict["n_colors"]
        puzzle.limit_generate = limit_generate
        puzzle.strategy = strategy
        puzzle.check_ungenerated = check_ungenerated
        puzzle.t_total = 0.0

        # Initialize color_possible array as boolean
        puzzle.color_possible = np.ones(
            (puzzle.y, puzzle.x, puzzle.n_colors), dtype=np.bool_
        )

        # Track last pixel solved by assumption (for sorting heuristic)
        puzzle.last_assumption_pixel = None

        # Create lines structure with PuzzleLine objects
        puzzle.lines = {}
        for ori_key in ["vertical", "horizontal"]:
            for idx, data in puzzle_dict["lines"][ori_key].items():
                puzzle.lines[(ori_key, int(idx))] = PuzzleLine(
                    ori=ori_key,
                    idx=int(idx),
                    n=puzzle.x if ori_key == "horizontal" else puzzle.y,
                    n_colors=puzzle.n_colors,
                    block_lengths=tuple(data["block_lengths"]),
                    block_colors=tuple(data["block_colors"]),
                    limit_generate=limit_generate,
                    check_ungenerated=check_ungenerated,
                )

        return puzzle

    def get_slice(self, ori: str, idx: int) -> np.ndarray:
        """Extract a specific row or column from color_possible based on orientation."""
        if ori == "vertical":
            return self.color_possible[:, idx, :]
        else:
            return self.color_possible[idx, :, :]

    def set_slice(self, ori: str, idx: int, slice: np.ndarray):
        """Set a specific row or column in color_possible based on orientation."""
        if ori == "vertical":
            self.color_possible[:, idx, :] = slice
        else:
            self.color_possible[idx, :, :] = slice

    def is_solved(self) -> bool:
        """Check if the puzzle is solved (each cell has exactly one possible color)."""
        return np.all(np.sum(self.color_possible, axis=2) == 1)

    def initialize(self):
        """Initialize puzzle lines by counting possible solutions and generating initial constraints."""

        for (ori, idx), puzzle_line in self.lines.items():
            slice = self.get_slice(ori, idx)
            new_slice = puzzle_line.initialize(slice)
            self.set_slice(ori, idx, new_slice)

    def update(self) -> bool:
        """Refine existing solutions by filtering possible lines based on color_possible.

        Returns:
          True if color_possible was updated, False otherwise
        """
        old = self.color_possible.copy()

        for (ori, idx), puzzle_line in self.lines.items():
            slice = self.get_slice(ori, idx)
            new_slice = puzzle_line.update(slice)
            self.set_slice(ori, idx, new_slice)

        return not np.all(old == self.color_possible)

    def solve(self, do_plot: bool = False, max_iterations: Optional[int] = None, benchmark_output: bool = False):
        """Main solving loop - coordinates iteration, refinement, and generation.

        Args:
          do_plot: Whether to plot each iteration
          max_iterations: Maximum number of iterations (None for unlimited)
          benchmark_output: Whether to print benchmark output after solving
        """
        it = 0
        print("Initial puzzle state:")
        
        start = time.perf_counter()
        self.initialize()
        self.t_total += time.perf_counter() - start

        self.benchmark_output(benchmark_output)

        if do_plot:
            plot(self.desc, it, self.color_possible, self.colors, 0)

        while not self.is_solved():
            it += 1
            start = time.perf_counter()
            self.solve_iteration(it, do_plot)
            self.t_total += time.perf_counter() - start

            if max_iterations is not None and it >= max_iterations:
                break
            self.benchmark_output(benchmark_output)

        if self.is_solved():
            print(f"\nPuzzle solved in {it} iterations!")
        else:
            print(f"\nStopped after {it} iterations (max_iterations={max_iterations})")

    def solve_iteration(self, it: int, do_plot: bool = False):
        """Perform one iteration of the solving algorithm.

        Args:
          it: Iteration number
          do_plot: Whether to plot the current state
        """
        print("\nIteration", it)

        # Refine existing solutions
        updated = self.update()

        # No updates? Use the configured strategy
        if not updated:
            if self.strategy == "guess":
                updated = self.strategy_guess(do_plot=do_plot)
            elif self.strategy == "force_generate":
                updated = self.strategy_force_generate()

        # STILL no updates? That should not happen, it means the algorithm is stuck
        if not updated:
            raise NoUpdateError

        if do_plot:
            plot(self.desc, it, self.color_possible, self.colors, 0)

    def strategy_force_generate(self) -> bool:
        """Force generate the smallest non-generated line, regardless of limit.

        This is used when stuck and need to make progress by generating
        even complex lines. Only used in "force_generate" strategy.
        Returns:
          True if a line was generated, False if all lines already generated
        """

        print("\nNo update to color_possible: Generate new solutions")
        print("No line was below the generate limit", self.limit_generate)

        # Find minimum count among non-generated
        ungenerated = {k: v for k, v in self.lines.items() if not v.generated}
        if not ungenerated:
            return False
        (ori0, idx0), line0 = min(ungenerated.items(), key=lambda x: x[1].count)

        # Update color_possible from this new line
        slice = self.get_slice(ori0, idx0)
        new_slice = line0.update(slice, force_generate=True)
        self.set_slice(ori0, idx0, new_slice)

        return True

    def benchmark_output(self, enable: bool):
        """Print benchmark timing summary from puzzle_line module."""                    
        if not enable:
            return
        # Get benchmark timing from puzzle_line module
        t_unique = sum(line.t_unique for line in self.lines.values())
        t_keep = sum(line.t_keep for line in self.lines.values())
        t_generate_lines = sum(line.t_generate_lines for line in self.lines.values())
        t_calculate_count = sum(line.t_calculate_count for line in self.lines.values())
        t_calculate_slice = sum(line.t_calculate_slice for line in self.lines.values())
        t_total = self.t_total

        t_other = t_total - t_unique - t_keep - t_generate_lines - t_calculate_count - t_calculate_slice
        fac = 100 / t_total

        print(f"Calculating unique:   {t_unique:6.2f} s = {(t_unique * fac):6.2f} %")
        print(f"Calculating keep:     {t_keep:6.2f} s = {(t_keep * fac):6.2f} %")
        print(f"Calculating count:    {t_calculate_count:6.2f} s = {(t_calculate_count * fac):6.2f} % ")
        print(f"Generating lines:     {t_generate_lines:6.2f} s = {(t_generate_lines * fac):6.2f} % ")
        print(f"Calculating slice:    {t_calculate_slice:6.2f} s = {(t_calculate_slice * fac):6.2f} % ")
        print(f"Other operations:     {t_other:6.2f} s = {(t_other * fac):6.2f} % ")
        print(f"Total runtime:        {t_total:6.2f} s = 100.00 %")      

    def save_solution(self):
        """Save the solved puzzle to disk as a .json file."""
        # Save as JSON with the solution grid
        solution = np.argmax(self.color_possible, axis=2)
        solution_json = os.path.join("solutions", "python", str(self.id0) + ".json")
        with open(solution_json, "w") as f:
            json.dump(
                {
                    "id0": self.id0,
                    "desc": self.desc,
                    "solution": solution.tolist(),
                    "colors": self.colors,
                },
                f,
                indent=2,
            )

        print(f"Solution saved to {solution_json}")

    def save_plot(self):
        """Save a PNG plot of the final solution."""
        plot(self.desc, "FINAL", self.color_possible, self.colors, 0)
        png_file = os.path.join("solutions", "python", "png", str(self.id0) + ".png")
        plt.savefig(png_file, bbox_inches="tight", dpi=150)
        print(f"Plot saved to {png_file}")

    def deep_copy(self) -> "Puzzle":
        """Create a deep copy of this puzzle with all dependent members.

        Returns:
          A new Puzzle instance with deep-copied state
        """
        return copy.deepcopy(self)

    def __deepcopy__(self, memo) -> "Puzzle":
        """Custom deep copy implementation for Puzzle objects.

        Args:
          memo: Dictionary of objects already copied (used by copy.deepcopy)

        Returns:
          A new Puzzle instance with deep-copied state
        """
        # Create a new puzzle instance without calling __init__
        new_puzzle = object.__new__(Puzzle)

        # Add to memo to handle circular references
        memo[id(self)] = new_puzzle

        # Copy all attributes using deepcopy for mutable objects
        for key, value in self.__dict__.items():
            if key == "lines":
                # Special handling for lines dictionary with PuzzleLine objects
                new_puzzle.lines = {}
                for (ori, idx), puzzle_line in value.items():
                    new_puzzle.lines[(ori, idx)] = copy.deepcopy(puzzle_line, memo)
            elif isinstance(value, np.ndarray):
                # NumPy arrays need .copy()
                setattr(new_puzzle, key, value.copy())
            elif isinstance(value, (list, dict)):
                # Deep copy mutable containers
                setattr(new_puzzle, key, copy.deepcopy(value, memo))
            else:
                # Immutable objects and primitives can be copied by reference
                setattr(new_puzzle, key, value)
        return new_puzzle

    def _calculate_distance_from_solved(self):
        """Calculate minimum Chebyshev distance from each pixel to any solved pixel.

        Uses vectorized NumPy operations for efficiency - O(num_solved * height * width).

        Returns:
          np.ndarray or None: Distance map of shape (height, width) where each cell contains
                             the minimum Chebyshev distance to any solved pixel.
                             Returns None if no pixels are solved yet.
        """
        # Find solved pixels (where exactly one color is possible)
        solved_mask = np.sum(self.color_possible, axis=2) == 1
        solved_coords = np.argwhere(solved_mask)

        if len(solved_coords) == 0:
            return None

        # Create coordinate grids for all pixels
        rows = np.arange(self.y)
        cols = np.arange(self.x)
        row_grid, col_grid = np.meshgrid(rows, cols, indexing="ij")

        # Initialize distance map with infinity
        distance_map = np.full((self.y, self.x), np.inf)

        # For each solved pixel, calculate Chebyshev distance to all pixels
        # and keep the minimum (vectorized per solved pixel)
        for solved_row, solved_col in solved_coords:
            chebyshev_dist = np.maximum(
                np.abs(row_grid - solved_row), np.abs(col_grid - solved_col)
            )
            distance_map = np.minimum(distance_map, chebyshev_dist)

        return distance_map

    def get_sorted_unsolved_pixels(self) -> list:
        """Get unsolved pixel-color combinations sorted by distance from solved regions.

        Uses minimum Chebyshev distance to any solved pixel - this creates a "flood fill"
        effect from solved regions into unsolved regions. Pixels at the boundary between
        solved and unsolved areas are prioritized.

        Returns:
          List of (row, col, color) tuples sorted by distance from solved pixels (ascending)
        """
        # Find all unsolved pixels (cells with more than one possible color)
        unsolved_mask = np.sum(self.color_possible, axis=2) > 1
        unsolved_indices = np.argwhere(unsolved_mask)

        if len(unsolved_indices) == 0:
            return []

        # Calculate distance map
        distance_map = self._calculate_distance_from_solved()

        # If no solved pixels yet, use distance from edges as fallback
        if distance_map is None:
            rows = np.arange(self.y)
            cols = np.arange(self.x)
            row_grid, col_grid = np.meshgrid(rows, cols, indexing="ij")
            distance_map = np.minimum(
                np.minimum(row_grid, self.y - 1 - row_grid),
                np.minimum(col_grid, self.x - 1 - col_grid),
            )

        pixel_color_combinations = []

        # Single loop for all unsolved pixels
        for row, col in unsolved_indices:
            min_distance = distance_map[row, col]

            # Second key: Chebyshev distance to last assumption pixel (if any)
            if self.last_assumption_pixel is not None:
                last_row, last_col = self.last_assumption_pixel
                distance_to_last_assumption = max(
                    abs(row - last_row), abs(col - last_col)
                )
            else:
                # Fallback: use minimum line count if no assumption made yet
                distance_to_last_assumption = 0

            possible_colors = np.where(self.color_possible[row, col, :])[0]

            for color in possible_colors:
                pixel_color_combinations.append(
                    (min_distance, distance_to_last_assumption, row, col, color)
                )

        # Sort by distance ascending (closest to solved pixels first), then by distance to last assumption ascending
        pixel_color_combinations.sort(key=lambda x: (x[0], x[1]))

        # Return list of (row, col, color) tuples
        return [
            (int(row), int(col), int(color))
            for _, _, row, col, color in pixel_color_combinations
        ]

    def strategy_guess(self, do_plot=False) -> bool:
        """Try solving with systematic assumptions about unsolved pixels.

        Uses a breadth-first heuristic: makes a deep copy of the puzzle, sets an
        unsolved pixel to a specific color, and runs some iterations.
        If a contradiction is reached, the assumption was wrong and that color is
        eliminated from the original puzzle. Tests all pixel-color combinations
        systematically.

        Pixels are tried in order of distance from center (furthest first), as edge
        pixels tend to lead to contradictions faster.

        Returns:
          True if the assumption led to eliminating a color, False otherwise
        """

        # Get sorted list of all (pixel, color) combinations (furthest from center first)
        pixel_color_combos = self.get_sorted_unsolved_pixels()
        total = len(pixel_color_combos)

        print(f"\nTesting assumptions: {total} pixel-color combinations to check")

        # Ensure a plot is active
        if do_plot:
            fig = plt.gcf()
            ax = plt.gca()

        # Try all pixel-color combinations
        for idx, (row, col, assumed_color) in enumerate(pixel_color_combos, 1):
            # Show progress bar
            progress = idx / total
            bar_length = 40
            filled = int(bar_length * progress)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"\r[{bar}] {idx}/{total} checked", end="", flush=True)

            # Create a deep copy of the puzzle (suppress iteration output only)
            import sys
            import io

            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            try:
                puzzle_copy = self.deep_copy()

                # Force the copy to use "generate" strategy to avoid recursive assumptions
                puzzle_copy.strategy = None
                puzzle_copy.check_ungenerated = False

                # Set the assumed color in the copy
                puzzle_copy.color_possible[row, col, :] = False
                puzzle_copy.color_possible[row, col, assumed_color] = True

                # Run limited iterations to test the assumption (max 3)
                puzzle_copy.solve(do_plot=False, max_iterations=3)

                # If we reach here, no contradiction was found
                # Restore output and mark pixel with red cross
                sys.stdout = old_stdout

                # Add red cross for unsuccessful attempt (note: row/col vs x/y in imshow)
                if do_plot:
                    ax.plot(col, row, "rx", markersize=4, markeredgewidth=1, alpha=0.7)
                    fig.canvas.draw()
                    fig.canvas.flush_events()
                    plt.pause(0.001)

            except NoSolutionError:
                # Restore output first
                sys.stdout = old_stdout

                # Contradiction found! The assumed color is impossible
                print(
                    f"\n  → Contradiction found! Eliminating color {assumed_color} from pixel ({row}, {col})"
                )

                # Eliminate this color from the original puzzle
                self.color_possible[row, col, assumed_color] = False

                # Track this pixel as the last assumption that led to progress
                self.last_assumption_pixel = (row, col)

                return True
            except NoUpdateError:
                # If we reach here, no contradiction was found
                # Restore output and mark pixel with red cross
                sys.stdout = old_stdout

                # Add red cross for unsuccessful attempt (note: row/col vs x/y in imshow)
                if do_plot:
                    ax.plot(col, row, "rx", markersize=4, markeredgewidth=1, alpha=0.7)
                    fig.canvas.draw()
                    fig.canvas.flush_events()
                    plt.pause(0.001)

        print()  # New line after progress bar
        return False
