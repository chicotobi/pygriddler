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
    # Load puzzle from ID
    parser = GriddlerParser(puzzle_id)
    json_path = parser.ensure_json_exists()
    data = GriddlerParser.load_puzzle_data(json_path)
    
    # Initialize from data
    self.id0 = data["id0"]
    self.desc = data["desc"]
    self.lines = data["lines"]
    self.colors = data["colors"]
    self.n_colors = data["n_colors"]
    self.x = data["x"]
    self.y = data["y"]
    self.limit_generate = limit_generate
    self.strategy = strategy
    
    # Initialize color_possible array (y x x x n_colors)
    self.color_possible = np.ones((self.y, self.x, self.n_colors))
    
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
        if n_pos < self.limit_generate:
          status0.possible_lines = generate_with_info(len_line, block_lengths, block_colors, -1, totuple(info))
          status0.generated = True
          generated_new_line = True
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
    
    if do_plot:
      plot(self.desc, it, self.color_possible, self.colors, 0)
    
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
  
  def get_sorted_unsolved_pixels(self) -> list:
    """Get unsolved pixel-color combinations sorted by distance from center (furthest first).
    
    Pixels near the boundary are tried first as they tend to lead to contradictions
    more quickly due to edge constraints.
    
    Returns:
      List of (row, col, color) tuples sorted by distance from center (descending)
    """
    # Find all unsolved pixels (cells with more than one possible color)
    unsolved_mask = np.sum(self.color_possible, axis=2) > 1
    unsolved_indices = np.argwhere(unsolved_mask)
    
    if len(unsolved_indices) == 0:
      return []
    
    # Calculate center of puzzle
    center_y = self.y / 2.0
    center_x = self.x / 2.0
    
    # Calculate distance from center and create (distance, min_count, row, col, color) tuples
    pixel_color_combinations = []
    for row, col in unsolved_indices:
      # Use Chebyshev distance (L∞ metric): max of absolute distances in x and y
      distance = max(abs(row - center_y), abs(col - center_x))
      # Get the minimum of row and column solution counts (more constrained = fewer solutions)
      min_count = min(self.lines["horizontal"][row].count, self.lines["vertical"][col].count)
      # Get all possible colors for this pixel
      possible_colors = np.where(self.color_possible[row, col, :] == 1)[0]
      # Add a tuple for each (row, col, color) combination
      for color in possible_colors:
        pixel_color_combinations.append((distance, min_count, row, col, color))
    
    # Sort by distance descending (furthest from center first), then by min_count ascending (more constrained first)
    pixel_color_combinations.sort(key=lambda x: (-x[0], x[1]))
    
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
    # Get sorted list of all (pixel, color) combinations (furthest from center first)
    pixel_color_combos = self.get_sorted_unsolved_pixels()
    
    # Try all pixel-color combinations
    for row, col, assumed_color in pixel_color_combos:
      print(f"Testing assumption: pixel ({row}, {col}) = color {assumed_color}")
      
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
        
        # Run limited iterations to test the assumption (max 3)
        puzzle_copy.solve(do_plot=False, max_iterations=3)
        
        # If we reach here, no contradiction was found
        # Restore output and continue to next pixel-color combination
        sys.stdout = old_stdout
        print(f"  → Inconclusive (no contradiction detected)")
        
      except (ValueError, Exception) as e:
        # Restore output first
        sys.stdout = old_stdout
        
        # Contradiction found! The assumed color is impossible
        print(f"  → Contradiction! Eliminating color {assumed_color} from pixel ({row}, {col})")
        
        # Eliminate this color from the original puzzle
        self.color_possible[row, col, assumed_color] = 0
        
        return True
    
    return False
