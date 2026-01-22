import numpy as np
from typing import Optional


class PuzzleLine:
  """Tracks the state of a single row/column in the puzzle."""
  
  def __init__(self, block_colors: tuple, block_lengths: tuple, 
               possible_lines: Optional[np.ndarray] = None, 
               generated: bool = False, 
               count: int = 0):
    self._block_colors = block_colors
    self._block_lengths = block_lengths
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
  
  def update_from_color_possible(self, ori: str, line: int, color_possible: np.ndarray, msg_func):
    """Update this line's possible_lines based on color_possible constraints."""
    from solution import extract_row
    n_colors = color_possible.shape[2]
    old_count = self._count
    possible_lines0 = self._possible_lines
    for color in range(n_colors):
      extracted_row = extract_row(color_possible, ori, line, color)
      for idx2, val in enumerate(extracted_row):
        if val == 0:
          keep = possible_lines0[:,idx2] != color
          possible_lines0 = possible_lines0[keep,:]
    self._count = len(possible_lines0)
    self._possible_lines = possible_lines0
    msg_func(ori, line, self._count, "Reduced to", old_count)
  
  def get_allowed_colors(self):
    """Return list of allowed colors for each position in this line."""
    if self._possible_lines is None:
      return None
    _, n2 = self._possible_lines.shape
    return [np.unique(self._possible_lines[:,i]) for i in range(n2)]
