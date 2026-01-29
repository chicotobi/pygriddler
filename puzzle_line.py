import numpy as np
import pandas as pd
from typing import Optional
import time
from utils import msg, totuple
from generators import generate_color_possible_from_slice

# Global counter for benchmarking get_color_possible_slice bottleneck
_time_unique = 0.0
_time_keep = 0.0


class PuzzleLine:
  """Tracks the state of a single row/column in the puzzle."""
  
  def __init__(self,
               n: int,
               n_colors: int,
               block_lengths: tuple,
               block_colors: tuple, 
               possible_lines: Optional[np.ndarray] = None, 
               generated: bool = False, 
               count: int = 0):
    self._n = n
    self._n_colors = n_colors
    self._block_lengths = block_lengths
    self._block_colors = block_colors
    self._possible_lines = possible_lines
    self._generated = generated
    self._count = count
    self._slice_of_color_possible = None
  
  @property
  def n(self) -> int:
    return self._n
    
  @property
  def n_colors(self) -> int:
    return self._n_colors
      
  @property
  def block_lengths(self) -> tuple:
    return self._block_lengths

  @property
  def block_colors(self) -> tuple:
    return self._block_colors
  
  @property
  def possible_lines(self) -> Optional[np.ndarray]:
    return self._possible_lines
  
  @possible_lines.setter
  def possible_lines(self, value: Optional[np.ndarray]):
    self._possible_lines = value
  
  @property
  def generated(self) -> bool:
    return self._generated
  
  @generated.setter
  def generated(self, value: bool):
    self._generated = value
  
  @property
  def count(self) -> int:
    return self._count
  
  @count.setter
  def count(self, value: int):
    self._count = value
  
  @property
  def slice_of_color_possible(self) -> Optional[np.ndarray]:
    return self._slice_of_color_possible
  
  @slice_of_color_possible.setter
  def slice_of_color_possible(self, value: Optional[np.ndarray]):
    self._slice_of_color_possible = value
  
  def update_from_color_possible(self, ori: str, line: int, row_data: np.ndarray):
    """Update this line's possible_lines based on color_possible constraints.
    
    Args:
      ori: Orientation ('horizontal' or 'vertical')
      line: Line index
      row_data: Extracted row data (len_line x n_colors)
      msg_func: Message function for logging
    """
    global _time_keep
    old_count = self._count
    possible_lines0 = self._possible_lines
    start = time.perf_counter()
    # Vectorized filtering: build single mask for all constraints
    keep_mask = np.ones(len(possible_lines0), dtype=bool)
    for color in range(self._n_colors):
      extracted_row = row_data[:, color]
      invalid_positions = np.where(~extracted_row)[0]
      if len(invalid_positions) > 0:
        # Lines that have this color at any invalid position should be removed
        keep_mask &= ~(possible_lines0[:, invalid_positions] == color).any(axis=1)
    possible_lines0 = possible_lines0[keep_mask, :]
    _time_keep += time.perf_counter() - start
    self._count = len(possible_lines0)
    self._possible_lines = possible_lines0
    msg(ori, line, "reduced", self._count, old_count)
    return self._count
  
  def get_color_possible_slice(self):
    """Reduce the possible lines to the color_possible slice of this line"""
    global _time_unique
    if not self.generated:
      raise RuntimeError("Line must be generated before getting color possible slice.")

    # Possibly the computational bottleneck
    start = time.perf_counter()
    y = np.zeros((self.n, self._n_colors), dtype=np.bool_)
    for idx in range(self.n):
      allowed_colors = pd.unique(self._possible_lines[:, idx])
      for color in allowed_colors:
        y[idx, color] = True
    _time_unique += time.perf_counter() - start

    self.slice_of_color_possible = y
    return y
  
  def update_slice_for_ungenerated(self, ori: str, idx: int, row_data: np.ndarray) -> np.ndarray:
    """Generate and return updated color_possible slice for ungenerated lines.
    
    Args:
      ori: Orientation ('horizontal' or 'vertical')
      idx: Line index
      row_data: Current row data (len_line x n_colors)
      
    Returns:
      Updated slice with more restricted possibilities
    """
    slice = generate_color_possible_from_slice(
      n=self._n,
      n_colors=self._n_colors,
      block_lengths=self._block_lengths,
      block_colors=self._block_colors,
      slice=totuple(row_data)
    )
    
    msg(ori, idx, "reduced slice sum", np.sum(slice), np.sum(row_data))
    return slice
