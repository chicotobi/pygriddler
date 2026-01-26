import numpy as np
import os.path
import json
from typing import Dict
from puzzle_line import PuzzleLine
from generators import generate, generate_count
from generators import generate_with_info, generate_count_with_info
from generators import generate_color_possible
from utils import plot, msg, totuple


class Puzzle:
  """Represents a nonogram puzzle with color possibilities and puzzle lines."""
  
  def __init__(self, puzzle_data: dict, limit_generate: int = 5_000_000):
    """Initialize puzzle from puzzle data dictionary.
    
    Args:
      puzzle_data: Dictionary containing id0, desc, status, colors, n_colors, x, y
      limit_generate: Maximum number of possible lines to generate for a line
    """
    self.id0 = puzzle_data["id0"]
    self.desc = puzzle_data["desc"]
    self.status = puzzle_data["status"]
    self.colors = puzzle_data["colors"]
    self.n_colors = puzzle_data["n_colors"]
    self.x = puzzle_data["x"]
    self.y = puzzle_data["y"]
    self.limit_generate = limit_generate
    
    # Initialize color_possible array (y x x x n_colors)
    self.color_possible = np.ones((self.y, self.x, self.n_colors))
    
  def initialize(self):
    """Initialize puzzle lines by counting possible solutions and generating initial constraints."""
    other_ori = {"vertical": "horizontal", "horizontal": "vertical"}
    
    for ori, tmp in self.status.items():
      len_line = len(self.status[other_ori[ori]])
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
    for ori, tmp in self.status.items():
      len_line = len(self.status[other_ori[ori]])
      for line, status0 in tmp.items():
        block_colors = status0.block_colors
        block_lengths = status0.block_lengths
        ans = generate_color_possible(len_line, block_lengths, block_colors, self.n_colors)
        if ori == "vertical":
          self.color_possible[:, line, :] = np.logical_and(self.color_possible[:, line, :], ans)
        else:
          self.color_possible[line, :, :] = np.logical_and(self.color_possible[line, :, :], ans)
    
    # Trigger initial update of line_status
    for ori, tmp in self.status.items():
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
    
    for ori, pos0 in self.status.items():
      for idx, status0 in pos0.items():
        if not status0.generated:
          continue
        
        # If the relevant slice of color_possible hasn't changed, skip
        if np.all(status0.slice_of_color_possible == self.extract_row_2(ori, idx)):
          continue
        
        row_data = self.extract_row_2(ori, idx)
        status0.update_from_color_possible(ori, idx, row_data, msg)
        self.apply_line_constraints(ori, idx, status0)
        status0.slice_of_color_possible = row_data.copy()
    
    return not np.all(old == self.color_possible)
  
  def generate_new_solutions(self) -> bool:
    """Generate new solutions for lines that haven't been generated yet.
    
    Returns:
      True if at least one new line was generated, False if stuck
    """
    other_ori = {"vertical": "horizontal", "horizontal": "vertical"}
    generated_new_line = False
    
    print("\nNo update to color_possible: Generate new solutions")
    
    for ori, pos0 in self.status.items():
      len_line = len(self.status[other_ori[ori]])
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
    
    if generated_new_line:
      return True
    
    print("No line was below the generate limit", self.limit_generate)
    
    # Find minimum count among non-generated
    ori0 = None
    line0 = None
    count0 = 1e10
    for ori, pos0 in self.status.items():
      for line, status0 in pos0.items():
        if not status0.generated and status0.count < count0:
          ori0, line0, count0 = ori, line, status0.count
    
    if ori0 is None:
      raise Exception("WARNING! No updates possible, but all lines generated - stuck!")
    
    len_line = len(self.status[other_ori[ori0]])
    block_colors = self.status[ori0][line0].block_colors
    block_lengths = self.status[ori0][line0].block_lengths
    info = self.extract_row_2(ori0, line0)
    self.status[ori0][line0].possible_lines = generate_with_info(len_line, block_lengths, block_colors, -1, totuple(info))
    self.status[ori0][line0].generated = True
    
    # Update color_possible
    self.apply_line_constraints(ori0, line0, self.status[ori0][line0])
    
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
    
    # No updates? Generate new solutions
    if not updated:
      # Check if there are still non-generated lines
      still_non_generated = any(
        not status0.generated
        for ori, pos0 in self.status.items()
        for line, status0 in pos0.items()
      )
      
      if still_non_generated:
        self.generate_new_solutions()
      else:
        raise Exception("WARNING! No updates possible, but all lines generated - stuck!")
  
  def solve(self, do_plot: bool = False):
    """Main solving loop - coordinates iteration, refinement, and generation.
    
    Args:
      do_plot: Whether to plot each iteration
    """
    it = 0
    while not self.is_solved():
      it += 1
      self.solve_iteration(it, do_plot)
    
    print(f"\nPuzzle solved in {it} iterations!")
  
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
