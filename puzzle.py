import numpy as np
import os.path
import json
import copy
from typing import Dict, Optional, Tuple
from puzzle_line import PuzzleLine
from generators import generate, generate_count
from generators import generate_with_info, generate_count_with_info
from generators import generate_color_possible
from utils import plot, msg, totuple
from griddler_parser import GriddlerParser

# Debug flag - set to True to enable distance map visualization
DEBUG = False


class Puzzle:
  """Represents a nonogram puzzle with color possibilities and puzzle lines."""
  
  def __init__(self, puzzle_id: int, limit_generate: int = 5_000_000, 
               strategy: str = "generate"):
    """Initialize puzzle from puzzle ID.
    
    Args:
      puzzle_id: Puzzle ID from griddlers.net or example number (1-9).
                 Will download/parse puzzle as needed.
      limit_generate: Maximum number of possible lines to generate for a line
      strategy: Solving strategy when stuck - "generate" or "assumption"
                - "generate": Generate more solutions for complex lines (default)
                - "assumption": Try random pixel assumptions to eliminate possibilities
    """
    # Load puzzle from ID and get raw JSON data
    parser = GriddlerParser(puzzle_id)
    json_path = parser.ensure_json_exists()
    
    with open(json_path, 'r') as f:
      puzzle_data = json.load(f)
    
    # Use from_dict to initialize (reuse common logic)
    puzzle = Puzzle.from_dict(puzzle_data, limit_generate, strategy)
    
    # Copy all attributes to self
    self.__dict__.update(puzzle.__dict__)
  
  @classmethod
  def from_dict(cls, puzzle_dict: dict, limit_generate: int = 5_000_000, 
                strategy: str = "generate"):
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
    
    # Initialize color_possible array
    puzzle.color_possible = np.ones((puzzle.y, puzzle.x, puzzle.n_colors))
    
    # Track last pixel solved by assumption (for sorting heuristic)
    puzzle.last_assumption_pixel = None
    
    # Create lines structure with PuzzleLine objects
    puzzle.lines = {}
    for ori_key in ["vertical", "horizontal"]:
      puzzle.lines[ori_key] = {
        int(idx): PuzzleLine(
          block_colors=tuple(data["block_colors"]),
          block_lengths=tuple(data["block_lengths"]),
          n_colors=puzzle.n_colors
        ) for idx, data in puzzle_dict["lines"][ori_key].items()
      }
    
    return puzzle
    
  def initialize(self):
    """Initialize puzzle lines by counting possible solutions and generating initial constraints."""
    other_ori = {"vertical": "horizontal", "horizontal": "vertical"}
    
    for ori, tmp in self.lines.items():
      len_line = len(self.lines[other_ori[ori]])
      for line, status0 in tmp.items():
        block_colors = status0.block_colors
        block_lengths = status0.block_lengths
        n_pos = generate_count(len_line, block_lengths, block_colors, -1)
        status0.count = n_pos
        if n_pos < self.limit_generate:
          status0.possible_lines = generate(len_line, block_lengths, block_colors, -1)
          status0.generated = True
        msg(ori, line, n_pos, status0.generated)
    
    # Initialize color_possible from sweeping the input
    for ori, tmp in self.lines.items():
      len_line = len(self.lines[other_ori[ori]])
      for line, status0 in tmp.items():
        block_colors = status0.block_colors
        block_lengths = status0.block_lengths
        ans = generate_color_possible(len_line, block_lengths, block_colors, self.n_colors)
        if ori == "vertical":
          self.color_possible[:, line, :] = np.logical_and(self.color_possible[:, line, :], ans)
        else:
          self.color_possible[line, :, :] = np.logical_and(self.color_possible[line, :, :], ans)
    
    # Trigger initial update of line_status
    for ori, tmp in self.lines.items():
      for line, status0 in tmp.items():
        status0.slice_of_color_possible = self.extract_row_2(ori, line) * -1
  
  def extract_row_2(self, ori: str, idx: int) -> np.ndarray:
    """Extract a specific row or column from color_possible based on orientation."""
    if ori == "vertical":
      return self.color_possible[:, idx, :]
    else:
      return self.color_possible[idx, :, :]
  
  def extract_row(self, ori: str, idx: int, color: int) -> np.ndarray:
    """Extract a specific row or column for a given color."""
    if ori == "vertical":
      return self.color_possible[:, idx, color]
    else:
      return self.color_possible[idx, :, color]
  
  def is_solved(self) -> bool:
    """Check if the puzzle is solved (each cell has exactly one possible color)."""
    return np.all(np.sum(self.color_possible, axis=2) == 1)
  
  def apply_line_constraints(self, ori: str, line: int, line_status: PuzzleLine):
    """Apply line constraints to color_possible based on allowed colors."""
    allowed_colors = line_status.get_allowed_colors()
    if allowed_colors is None:
      return
    
    for idx2, allowed_colors0 in enumerate(allowed_colors):
      for color in range(self.n_colors):
        if color not in allowed_colors0:
          if ori == "horizontal":
            self.color_possible[line, idx2, color] = 0
          else:
            self.color_possible[idx2, line, color] = 0
  
  def refine_solutions(self) -> bool:
    """Refine existing solutions by filtering possible lines based on color_possible.
    
    Returns:
      True if color_possible was updated, False otherwise
    """
    other_ori = {"vertical": "horizontal", "horizontal": "vertical"}
    old = self.color_possible.copy()
    
    for ori, pos0 in self.lines.items():
      for idx, status0 in pos0.items():
        if not status0.generated:
          continue
        
        # If the relevant slice of color_possible hasn't changed, skip
        if np.all(status0.slice_of_color_possible == self.extract_row_2(ori, idx)):
          continue
        
        row_data = self.extract_row_2(ori, idx)
        new_count = status0.update_from_color_possible(ori, idx, row_data, msg)
        if new_count == 0:
          # This should only happen for contradictions within assumptions
          raise ValueError(f"Line {ori} {idx} has no possible solutions left!")
        self.apply_line_constraints(ori, idx, status0)
        status0.slice_of_color_possible = row_data.copy()
    
    return not np.all(old == self.color_possible)
  
  def generate_solutions_under_limit(self) -> bool:
    """Generate solutions for lines under the generation limit.
    
    This should be called in ALL strategies on every iteration to generate 
    solutions for lines that are below the complexity threshold.
    
    Returns:
      True if at least one new line was generated, False otherwise
    """
    other_ori = {"vertical": "horizontal", "horizontal": "vertical"}
    generated_new_line = False
    
    for ori, pos0 in self.lines.items():
      len_line = len(self.lines[other_ori[ori]])
      for line, status0 in pos0.items():
        if status0.generated:
          continue
        
        block_colors = status0.block_colors
        block_lengths = status0.block_lengths
        info = self.extract_row_2(ori, line)
        n_pos = generate_count_with_info(len_line, block_lengths, block_colors, -1, totuple(info))
        
        status0.count = n_pos
        if n_pos <= self.limit_generate:
          status0.possible_lines = generate_with_info(len_line, block_lengths, block_colors, -1, totuple(info))
          status0.generated = True
          generated_new_line = True
          status0.slice_of_color_possible = info.copy()
          msg(ori, line, n_pos, status0.generated)
          
          # Update color_possible
          self.apply_line_constraints(ori, line, status0)
    
    return generated_new_line
  
  def force_generate_smallest_line(self) -> bool:
    """Force generate the smallest non-generated line, regardless of limit.
    
    This is used when stuck and need to make progress by generating 
    even complex lines. Only used in "generate" strategy.
    
    Returns:
      True if a line was generated, False if all lines already generated
    """
    other_ori = {"vertical": "horizontal", "horizontal": "vertical"}
    
    print("\nNo update to color_possible: Generate new solutions")
    print("No line was below the generate limit", self.limit_generate)
    
    # Find minimum count among non-generated
    ori0 = None
    line0 = None
    count0 = 1e10
    for ori, pos0 in self.lines.items():
      for line, status0 in pos0.items():
        if not status0.generated and status0.count < count0:
          ori0, line0, count0 = ori, line, status0.count
    
    if ori0 is None:
      return False
    
    len_line = len(self.lines[other_ori[ori0]])
    block_colors = self.lines[ori0][line0].block_colors
    block_lengths = self.lines[ori0][line0].block_lengths
    info = self.extract_row_2(ori0, line0)
    self.lines[ori0][line0].possible_lines = generate_with_info(len_line, block_lengths, block_colors, -1, totuple(info))
    self.lines[ori0][line0].generated = True
    
    # Update color_possible
    self.apply_line_constraints(ori0, line0, self.lines[ori0][line0])
    
    msg(ori0, line0, count0, True)
    
    return True
  
  def solve_iteration(self, it: int, do_plot: bool = False):
    """Perform one iteration of the solving algorithm.
    
    Args:
      it: Iteration number
      do_plot: Whether to plot the current state
    """
    print("\nIteration", it)
    
    # Refine existing solutions
    updated = self.refine_solutions()
    
    # No updates? Try to generate new solutions under the limit
    if not updated:
      updated = self.generate_solutions_under_limit()

    # STILL no updates? Use the configured strategy
    if not updated:
      if self.strategy == "assumption":
        updated = self.try_assumption()
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
    import matplotlib.pyplot as plt
    plot(self.desc, "FINAL", self.color_possible, self.colors, 0)
    png_file = os.path.join('solutions', 'python', 'png', str(self.id0) + '.png')
    plt.savefig(png_file, bbox_inches='tight', dpi=150)
    print(f"Plot saved to {png_file}")
  
  def deep_copy(self) -> 'Puzzle':
    """Create a deep copy of this puzzle with all dependent members.
    
    Returns:
      A new Puzzle instance with deep-copied state
    """
    # Create a new puzzle instance without calling __init__
    new_puzzle = object.__new__(Puzzle)
    
    # Copy scalar attributes
    new_puzzle.id0 = self.id0
    new_puzzle.desc = self.desc
    new_puzzle.colors = self.colors.copy() if isinstance(self.colors, list) else self.colors
    new_puzzle.n_colors = self.n_colors
    new_puzzle.x = self.x
    new_puzzle.y = self.y
    new_puzzle.limit_generate = self.limit_generate
    new_puzzle.strategy = self.strategy
    new_puzzle.last_assumption_pixel = self.last_assumption_pixel
    
    # Deep copy color_possible array
    new_puzzle.color_possible = self.color_possible.copy()
    
    # Deep copy lines dictionary with PuzzleLine objects
    new_puzzle.lines = {}
    for ori, lines_dict in self.lines.items():
      new_puzzle.lines[ori] = {}
      for line_idx, puzzle_line in lines_dict.items():
        # Create new PuzzleLine with copied data
        new_puzzle_line = PuzzleLine(
          block_colors=puzzle_line.block_colors,
          block_lengths=puzzle_line.block_lengths,
          n_colors=puzzle_line._n_colors,
          possible_lines=puzzle_line.possible_lines.copy() if puzzle_line.possible_lines is not None else None,
          generated=puzzle_line.generated,
          count=puzzle_line.count
        )
        # Copy slice_of_color_possible if it exists
        if puzzle_line.slice_of_color_possible is not None:
          new_puzzle_line.slice_of_color_possible = puzzle_line.slice_of_color_possible.copy()
        new_puzzle.lines[ori][line_idx] = new_puzzle_line
    
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
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    
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
        distance_to_last_assumption = min(self.lines["horizontal"][row].count, 
                                          self.lines["vertical"][col].count)
      
      possible_colors = np.where(self.color_possible[row, col, :] == 1)[0]
      
      for color in possible_colors:
        pixel_color_combinations.append((min_distance, distance_to_last_assumption, row, col, color))
    
    # Sort by distance ascending (closest to solved pixels first), then by distance to last assumption ascending
    pixel_color_combinations.sort(key=lambda x: (x[0], x[1]))
    
    # Return list of (row, col, color) tuples
    return [(int(row), int(col), int(color)) for _, _, row, col, color in pixel_color_combinations]
  
  def try_assumption(self) -> bool:
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
    import matplotlib.pyplot as plt
    
    # Get sorted list of all (pixel, color) combinations (furthest from center first)
    pixel_color_combos = self.get_sorted_unsolved_pixels()
    total = len(pixel_color_combos)
    
    print(f"\nTesting assumptions: {total} pixel-color combinations to check")
    
    # Ensure a plot is active
    if plt.get_fignums():
      fig = plt.gcf()
      ax = plt.gca()
    else:
      # Create initial plot if none exists
      from utils import plot as utils_plot
      utils_plot(self.desc, "Assumption Testing", self.color_possible, self.colors, 0)
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
        puzzle_copy.color_possible[row, col, :] = 0
        puzzle_copy.color_possible[row, col, assumed_color] = 1
        
        # Run limited iterations to test the assumption (max 5)
        puzzle_copy.solve(do_plot=False, max_iterations=5)
        
        # If we reach here, no contradiction was found
        # Restore output and mark pixel with red cross
        sys.stdout = old_stdout
        
        # Add red cross for unsuccessful attempt (note: row/col vs x/y in imshow)
        ax.plot(col, row, 'rx', markersize=4, markeredgewidth=1, alpha=0.7)
        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(0.001)
        
      except (ValueError, Exception) as e:
        # Restore output first
        sys.stdout = old_stdout
        
        # Contradiction found! The assumed color is impossible
        print(f'\n  → Contradiction found! Eliminating color {assumed_color} from pixel ({row}, {col})')
        
        # Eliminate this color from the original puzzle
        self.color_possible[row, col, assumed_color] = 0
        
        # Track this pixel as the last assumption that led to progress
        self.last_assumption_pixel = (row, col)
        
        return True
    
    print()  # New line after progress bar
    return False
