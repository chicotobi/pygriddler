import numpy as np
import os.path
import json
import copy
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import Dict, Optional, Tuple
from puzzle_line import PuzzleLine
from utils import plot, msg, NoSolutionError
from griddler_parser import GriddlerParser

# Debug flag - set to True to enable distance map visualization
DEBUG = False

class Puzzle:
  """Represents a nonogram puzzle with color possibilities and puzzle lines."""
  
  def __init__(self, puzzle_id: int, limit_generate: int = 5_000_000, 
               strategy: str = "generate", check_ungenerated: bool = True):
    """Initialize puzzle from puzzle ID.
    
    Args:
      puzzle_id: Puzzle ID from griddlers.net or example number (1-9).
                 Will download/parse puzzle as needed.
      limit_generate: Maximum number of possible lines to generate for a line
      strategy: Solving strategy when stuck - "generate" or "assumption"
                - "generate": Generate more solutions for complex lines (default)
                - "assumption": Try random pixel assumptions to eliminate possibilities
      check_ungenerated: Whether to check ungenerated lines during solving
    """
    # Load puzzle from ID and get raw JSON data
    parser = GriddlerParser(puzzle_id)
    json_path = parser.ensure_json_exists()
    
    with open(json_path, 'r') as f:
      puzzle_data = json.load(f)
    
    # Use from_dict to initialize (reuse common logic)
    puzzle = Puzzle.from_dict(puzzle_data, limit_generate, strategy, check_ungenerated)
    
    # Copy all attributes to self
    self.__dict__.update(puzzle.__dict__)
  
  @classmethod
  def from_dict(cls, puzzle_dict: dict, limit_generate: int = 5_000_000, 
                strategy: str = "generate", check_ungenerated: bool = True) -> 'Puzzle':
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
      strategy: Solving strategy - "generate" or "assumption"
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
    
    # Initialize color_possible array as boolean
    puzzle.color_possible = np.ones((puzzle.y, puzzle.x, puzzle.n_colors), dtype=np.bool_)
    
    # Track last pixel solved by assumption (for sorting heuristic)
    puzzle.last_assumption_pixel = None
    
    # Create lines structure with PuzzleLine objects
    puzzle.lines = {}
    for ori_key in ["vertical", "horizontal"]:
      for idx, data in puzzle_dict["lines"][ori_key].items():
        puzzle.lines[(ori_key,int(idx))] = PuzzleLine(
            n = puzzle.x if ori_key == "horizontal" else puzzle.y,
            n_colors = puzzle.n_colors,
            block_lengths = tuple(data["block_lengths"]),
            block_colors = tuple(data["block_colors"]),
            check_ungenerated = check_ungenerated
        )
    
    return puzzle
    
  def initialize(self):
    """Initialize puzzle lines by counting possible solutions and generating initial constraints."""
    
    for (ori, idx), puzzle_line in self.lines.items():

      slice = self.get_slice(ori, idx)
      n_pos = puzzle_line.generate_count_from_slice(slice)
      new_slice = puzzle_line.generate_color_possible_from_slice(slice)

      if n_pos < self.limit_generate:
        new_slice = puzzle_line.generate_color_possible_from_slice(new_slice)
        msg(ori, idx, "generated", n_pos, puzzle_line.generated)
      else:
        msg(ori, idx, "counted", n_pos, puzzle_line.generated)
      self.set_slice(ori, idx, new_slice)
  
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
  
  def update(self) -> bool:
    """Refine existing solutions by filtering possible lines based on color_possible.
    
    Returns:
      True if color_possible was updated, False otherwise
    """
    old = self.color_possible.copy()
    
    for (ori, idx), puzzle_line in self.lines.items():
      slice = self.get_slice(ori, idx)
      new_slice = puzzle_line.update(ori, idx, slice)
      self.set_slice(ori, idx, new_slice)
    
    return not np.all(old == self.color_possible)
  
  def generate_solutions_under_limit(self) -> bool:
    """Generate solutions for lines under the generation limit.
    
    This should be called in ALL strategies on every iteration to generate 
    solutions for lines that are below the complexity threshold.
    
    Returns:
      True if at least one new line was generated, False otherwise
    """
    generated_new_line = False
    
    for (ori, idx), puzzle_line in self.lines.items():
      if puzzle_line.generated:
        continue
      
      slice = self.get_slice(ori, idx)
      n_pos = puzzle_line.generate_count_from_slice(slice)
      
      if n_pos <= self.limit_generate:
        new_slice = puzzle_line.generate_from_slice(slice)
        generated_new_line = True
        msg(ori, idx, "generated", n_pos, puzzle_line.generated)
        
        # Update color_possible
        self.set_slice(ori, idx, new_slice)
    
    return generated_new_line
  
  def force_generate_smallest_line(self) -> bool:
    """Force generate the smallest non-generated line, regardless of limit.
    
    This is used when stuck and need to make progress by generating 
    even complex lines. Only used in "generate" strategy.
    
    Returns:
      True if a line was generated, False if all lines already generated
    """
    
    print("\nNo update to color_possible: Generate new solutions")
    print("No line was below the generate limit", self.limit_generate)
    
    # Find minimum count among non-generated
    ori0, idx0 = None, None
    count0 = 1e10
    for (ori, idx), puzzle_line in self.lines.items():
      if not puzzle_line.generated and puzzle_line.count < count0:
        ori0, idx0, count0 = ori, idx, puzzle_line.count
    
    if ori0 is None:
      return False

    line0 = self.lines[(ori0, idx0)]
    
    slice = self.get_slice(ori0, idx0)
    new_slice = line0.generate_from_slice(slice)    
    # Update color_possible
    self.set_slice(ori0, idx0, new_slice)
    
    msg(ori0, idx0, "generated", count0, True)
    
    return True
  
  def solve_iteration(self, it: int, do_plot: bool = False):
    """Perform one iteration of the solving algorithm.
    
    Args:
      it: Iteration number
      do_plot: Whether to plot the current state
    """
    print("\nIteration", it)
    
    # Refine existing solutions
    updated = self.update()
    
    # No updates? Try to generate new solutions under the limit
    if not updated:
      updated = self.generate_solutions_under_limit()

    # STILL no updates? Use the configured strategy
    if not updated:
      if self.strategy == "assumption":
        updated = self.try_assumption(do_plot = do_plot)
        self.generate_solutions_under_limit()
      else:
        updated = self.force_generate_smallest_line()
      
    # STILL no updates? That should not happen, it means the algorithm is stuck
    if not updated:
      raise Exception("WARNING! Solver is stuck with no possible updates!")
      
    if do_plot:
      plot(self.desc, it, self.color_possible, self.colors, 0)
  
  def solve(self, do_plot: bool = False, max_iterations: Optional[int] = None):
    """Main solving loop - coordinates iteration, refinement, and generation.
    
    Args:
      do_plot: Whether to plot each iteration
      max_iterations: Maximum number of iterations (None for unlimited)
    """
    it = 0
    while not self.is_solved():
      it += 1
      self.solve_iteration(it, do_plot)
      
      if max_iterations is not None and it >= max_iterations:
        break
    
    if self.is_solved():
      print(f"\nPuzzle solved in {it} iterations!")
    else:
      print(f"\nStopped after {it} iterations (max_iterations={max_iterations})")
  
  def save_solution(self):
    """Save the solved puzzle to disk as both .npy and .json files."""
    # Save as numpy array
    solution_file = os.path.join('solutions', 'python', str(self.id0) + '.npy')
    np.save(solution_file, self.color_possible)
    
    # Save as JSON with the solution grid
    solution = np.argmax(self.color_possible, axis=2)
    solution_json = os.path.join('solutions', 'python', str(self.id0) + '.json')
    with open(solution_json, 'w') as f:
      json.dump({
        "id0": self.id0,
        "desc": self.desc,
        "solution": solution.tolist(),
        "colors": self.colors
      }, f, indent=2)
    
    print(f"Solution saved to {solution_file} and {solution_json}")
  
  def save_plot(self):
    """Save a PNG plot of the final solution."""
    plot(self.desc, "FINAL", self.color_possible, self.colors, 0)
    png_file = os.path.join('solutions', 'python', 'png', str(self.id0) + '.png')
    plt.savefig(png_file, bbox_inches='tight', dpi=150)
    print(f"Plot saved to {png_file}")
  
  def deep_copy(self) -> 'Puzzle':
    """Create a deep copy of this puzzle with all dependent members.
    
    Returns:
      A new Puzzle instance with deep-copied state
    """
    return copy.deepcopy(self)
  
  def __deepcopy__(self, memo) -> 'Puzzle':
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
      if key == 'lines':
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

    new_puzzle.strategy = 'generate'
    new_puzzle.check_ungenerated = False
    
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
    row_grid, col_grid = np.meshgrid(rows, cols, indexing='ij')
    
    # Initialize distance map with infinity
    distance_map = np.full((self.y, self.x), np.inf)
    
    # For each solved pixel, calculate Chebyshev distance to all pixels
    # and keep the minimum (vectorized per solved pixel)
    for solved_row, solved_col in solved_coords:
      chebyshev_dist = np.maximum(np.abs(row_grid - solved_row), 
                                   np.abs(col_grid - solved_col))
      distance_map = np.minimum(distance_map, chebyshev_dist)
    
    # Debug plot - show distance map the first time it's calculated
    if DEBUG:
      self._plot_distance_map(distance_map, solved_coords)
    
    return distance_map
  
  def _plot_distance_map(self, distance_map, solved_coords):
    """Debug visualization: plot distance map with heatmap and annotations."""
    
    fig, ax = plt.subplots(figsize=(max(8, self.x * 0.6), max(6, self.y * 0.6)))
    
    # Create heatmap with a nice color gradient
    im = ax.imshow(distance_map, cmap='viridis_r', interpolation='nearest', 
                   vmin=0, vmax=np.max(distance_map))
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, label='Distance to nearest solved pixel')
    
    # Annotate each cell with its distance value
    for i in range(self.y):
      for j in range(self.x):
        dist = distance_map[i, j]
        if np.isfinite(dist):
          text_color = 'white' if dist > np.max(distance_map) / 2 else 'black'
          ax.text(j, i, f'{int(dist)}', ha='center', va='center', 
                 color=text_color, fontsize=8, weight='bold')
    
    # Mark solved pixels with red X
    for row, col in solved_coords:
      ax.plot(col, row, 'rx', markersize=12, markeredgewidth=2)
    
    # Configure grid and labels
    ax.set_xticks(np.arange(self.x))
    ax.set_yticks(np.arange(self.y))
    ax.set_xticklabels(np.arange(self.x))
    ax.set_yticklabels(np.arange(self.y))
    ax.grid(which='minor', color='gray', linestyle='-', linewidth=0.5, alpha=0.3)
    ax.set_xticks(np.arange(-0.5, self.x, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, self.y, 1), minor=True)
    
    # Add legend
    solved_patch = mpatches.Patch(color='red', label=f'Solved pixels ({len(solved_coords)})')
    ax.legend(handles=[solved_patch], loc='upper right', bbox_to_anchor=(1.0, -0.05))
    
    plt.title(f'Distance Map: Chebyshev Distance to Nearest Solved Pixel\n{self.desc}', 
             fontsize=12, weight='bold')
    plt.tight_layout()
    plt.show(block=True)
    
    print("\n[DEBUG] Distance map visualization complete. Press any key to continue...")
    input()
  
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
      row_grid, col_grid = np.meshgrid(rows, cols, indexing='ij')
      distance_map = np.minimum(np.minimum(row_grid, self.y - 1 - row_grid),
                                 np.minimum(col_grid, self.x - 1 - col_grid))
    
    pixel_color_combinations = []
    
    # Single loop for all unsolved pixels
    for row, col in unsolved_indices:
      min_distance = distance_map[row, col]
      
      # Second key: Chebyshev distance to last assumption pixel (if any)
      if self.last_assumption_pixel is not None:
        last_row, last_col = self.last_assumption_pixel
        distance_to_last_assumption = max(abs(row - last_row), abs(col - last_col))
      else:
        # Fallback: use minimum line count if no assumption made yet
        distance_to_last_assumption = 0
      
      possible_colors = np.where(self.color_possible[row, col, :])[0]
      
      for color in possible_colors:
        pixel_color_combinations.append((min_distance, distance_to_last_assumption, row, col, color))
    
    # Sort by distance ascending (closest to solved pixels first), then by distance to last assumption ascending
    pixel_color_combinations.sort(key=lambda x: (x[0], x[1]))
    
    # Return list of (row, col, color) tuples
    return [(int(row), int(col), int(color)) for _, _, row, col, color in pixel_color_combinations]
  
  def try_assumption(self, do_plot=False) -> bool:
    """Try solving with systematic assumptions about unsolved pixels.
    
    Uses a breadth-first heuristic: makes a deep copy of the puzzle, sets an
    unsolved pixel to a specific color, and runs TWO iterations. 
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
      bar = '█' * filled + '░' * (bar_length - filled)
      print(f'\r[{bar}] {idx}/{total} checked', end='', flush=True)
      
      # Create a deep copy of the puzzle (suppress iteration output only)
      import sys
      import io
      old_stdout = sys.stdout
      sys.stdout = io.StringIO()
      
      try:
        puzzle_copy = self.deep_copy()

        # Force the copy to use "generate" strategy to avoid recursive assumptions
        puzzle_copy.strategy = "generate"
        
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
          ax.plot(col, row, 'rx', markersize=4, markeredgewidth=1, alpha=0.7)
          fig.canvas.draw()
          fig.canvas.flush_events()
          plt.pause(0.001)
        
      except (NoSolutionError) as e:
        # Restore output first
        sys.stdout = old_stdout
        
        # Contradiction found! The assumed color is impossible
        print(f'\n  → Contradiction found! Eliminating color {assumed_color} from pixel ({row}, {col})')
        
        # Eliminate this color from the original puzzle
        self.color_possible[row, col, assumed_color] = False
        
        # Track this pixel as the last assumption that led to progress
        self.last_assumption_pixel = (row, col)
        
        return True
    
    print()  # New line after progress bar
    return False
