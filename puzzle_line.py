import numpy as np
import pandas as pd
from typing import Optional
import time

# Global counter for benchmarking get_color_possible_slice bottleneck
_time_unique = 0.0
_time_keep = 0.0


class PuzzleLine:
  """Tracks the state of a single row/column in the puzzle."""
  
  def __init__(self, n: int, block_colors: tuple, block_lengths: tuple, 
               n_colors: int,
               possible_lines: Optional[np.ndarray] = None, 
               generated: bool = False, 
               count: int = 0):
    self.n = n
    self._block_colors = block_colors
    self._block_lengths = block_lengths
    self._n_colors = n_colors
    self._possible_lines = possible_lines
    self._generated = generated
    self._count = count
    self._slice_of_color_possible = None
  
  @property
  def block_colors(self) -> tuple:
    return self._block_colors
  
  @property
  def block_lengths(self) -> tuple:
    return self._block_lengths
  
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
  
  def update_from_color_possible(self, ori: str, line: int, row_data: np.ndarray, msg_func):
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
    for color in range(self._n_colors):
      extracted_row = row_data[:, color]
      for idx2, val in enumerate(extracted_row):
        if not val:  # If color is not possible (False)
          keep = possible_lines0[:,idx2] != color
          possible_lines0 = possible_lines0[keep,:]
    _time_keep += time.perf_counter() - start
    self._count = len(possible_lines0)
    self._possible_lines = possible_lines0
    msg_func(ori, line, self._count, "Reduced to", old_count)
    return self._count
  
  def get_color_possible_slice(self):
    """Reduce the possible lines to the color_possible slice of this line"""
    global _time_unique
    if self._possible_lines is None:
      return None
    _, n2 = self._possible_lines.shape
    # Possibly the computational bottleneck
    start = time.perf_counter()
    #x = [np.unique(self._possible_lines[:,i]) for i in range(n2)]
    x = [pd.unique(self._possible_lines[:,i]) for i in range(n2)]
    y = np.zeros((n2, self._n_colors), dtype=np.bool_)
    for i in range(n2):
      y[i, x[i]] = True
    _time_unique += time.perf_counter() - start
    return y
