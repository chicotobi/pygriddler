from functools import cache
import numpy as np
from utils import totuple

WHITE = 0
  
@cache
def generate(n, block_lengths, block_colors, previous_color):
  if len(block_lengths) == 0:
    return np.zeros((1,n), dtype = np.uint8)
  l = []
  n_same_colored_neighbours = sum(np.diff(block_colors)==0)
  max_zeroes_left_side = n - sum(block_lengths) - n_same_colored_neighbours
  if block_colors[0] == previous_color:
    i0 = 1
  else:
    i0 = 0
  for i in range(i0,max_zeroes_left_side+1):
    a3 = generate(n - i - block_lengths[0], block_lengths[1:], block_colors[1:], block_colors[0])
    nrow, _ = a3.shape
    a1 = np.zeros((nrow,i), dtype = np.uint8)
    a2 = np.ones((nrow, block_lengths[0]), dtype = np.uint8) * block_colors[0]
    a = np.concatenate((a1,a2,a3),axis=1)
    l.append(a)
  return np.concatenate(l)

@cache
def generate_count(n, block_lengths, block_colors, previous_color):
  if len(block_lengths) == 0:
    return 1
  l = 0
  n_same_colored_neighbours = sum(np.diff(block_colors)==0)
  max_zeroes_left_side = n - sum(block_lengths) - n_same_colored_neighbours
  if block_colors[0] == previous_color:
    i0 = 1
  else:
    i0 = 0
  for i in range(i0,max_zeroes_left_side+1):
    tmp = generate_count(n - i - block_lengths[0], block_lengths[1:], block_colors[1:], block_colors[0])
    l += tmp
  return l

@cache
def generate_from_slice(n, block_lengths, block_colors, previous_color, slice):
  if len(slice) == 0:
    return generate(n, block_lengths, block_colors, previous_color)
  slice = np.asarray(slice)
  if len(block_lengths) == 0:
    if all(slice[:,WHITE]):
      return np.zeros((1,n), dtype = np.uint8)
    else:
      return np.zeros((0,n), dtype = np.uint8)
  pos = []
  n_same_colored_neighbours = sum(np.diff(block_colors)==0)
  max_zeroes_left_side_from_input = n - sum(block_lengths) - n_same_colored_neighbours
   
  # Find the first index where no white is allowed
  tmp = np.nonzero(slice[:,WHITE] == False)[0]
  if len(tmp) > 0:
    max_zeroes_left_side_from_slice = tmp[0]
  else:
    max_zeroes_left_side_from_slice = n
  
  l = block_lengths[0]
  c = block_colors[0]
  
  max_zeroes_left_side = min(max_zeroes_left_side_from_input, max_zeroes_left_side_from_slice)
  if block_colors[0] == previous_color:
    i0 = 1
  else:
    i0 = 0
  for i in range(i0,max_zeroes_left_side+1):
    # We checked that the white blocks are allowed, now check, if the colored block is allowed:
    if all(slice[i:(i+l),c]):
      a3 = generate_from_slice(n - i - l, block_lengths[1:], block_colors[1:], block_colors[0], totuple(slice[i+l:,]))
      nrow, _ = a3.shape
      if a3.shape[0] > 0:
        a1 = np.zeros((nrow,i), dtype = np.uint8)
        a2 = np.ones((nrow, block_lengths[0]), dtype = np.uint8) * block_colors[0]
        a = np.concatenate((a1,a2,a3),axis=1)
        pos.append(a)
  if len(pos) > 0:
    return np.concatenate(pos)
  else:
    return np.zeros((0,n), dtype=np.uint8)

@cache
def generate_count_from_slice(n, block_lengths, block_colors, previous_color, slice):
  if len(slice) == 0:
    return generate_count(n, block_lengths, block_colors, previous_color)
  slice = np.asarray(slice)
  if len(block_lengths) == 0:
    if all(slice[:,WHITE]):
      return 1
    else:
      return 0
  count = 0
  n_same_colored_neighbours = sum(np.diff(block_colors)==0)
  max_zeroes_left_side_from_input = n - sum(block_lengths) - n_same_colored_neighbours
   
  # Find the first index where no white is allowed
  tmp = np.nonzero(slice[:,WHITE] == False)[0]
  if len(tmp) > 0:
    max_zeroes_left_side_from_slice = tmp[0]
  else:
    max_zeroes_left_side_from_slice = n
  
  l = block_lengths[0]
  c = block_colors[0]
  
  max_zeroes_left_side = min(max_zeroes_left_side_from_input, max_zeroes_left_side_from_slice)
  if block_colors[0] == previous_color:
    i0 = 1
  else:
    i0 = 0
  for i in range(i0,max_zeroes_left_side+1):
    # We checked that the white blocks are allowed, now check, if the colored block is allowed:
    if all(slice[i:(i+l),c]):
      tmp = generate_count_from_slice(n - i - l, block_lengths[1:], block_colors[1:], block_colors[0], totuple(slice[i+l:,]))
      count += tmp
  return count
  
@cache
def generate_color_possible_from_slice(n, block_lengths, block_colors, previous_color, n_colors, slice):
  # This functions should return a numpy array of shape (n, n_colors) with boolean values

  slice = np.asarray(slice, dtype=np.bool_)

  result = np.zeros((n, n_colors), dtype=np.bool_)

  if n == 0:
    return np.zeros((0, n_colors), dtype=np.bool_)

  if len(block_lengths) == 0:
    result[:, WHITE] = slice[:, WHITE]
    return result

  n_same_colored_neighbours = sum(np.diff(block_colors) == 0)
  max_zeroes_left_side_from_input = n - sum(block_lengths) - n_same_colored_neighbours
   
  # Find the first index where no white is allowed
  tmp = np.nonzero(slice[:, WHITE] == False)[0]
  if len(tmp) > 0:
    max_zeroes_left_side_from_slice = tmp[0]
  else:
    max_zeroes_left_side_from_slice = n
  
  l = block_lengths[0]
  c = block_colors[0]
  
  max_zeroes_left_side = min(max_zeroes_left_side_from_input, max_zeroes_left_side_from_slice)
  if block_colors[0] == previous_color:
    i0 = 1
  else:
    i0 = 0
  for i in range(i0, max_zeroes_left_side + 1):
    # We checked that the white blocks are allowed, now check, if the colored block is allowed:
    if all(slice[i:(i+l), c]):
      a2 = generate_color_possible_from_slice(n - i - l, block_lengths[1:], block_colors[1:], block_colors[0], n_colors, totuple(slice[i+l:, :]))
      
      # Build result for this starting position
      a1 = np.zeros((i + l, n_colors), dtype=np.bool_)
      a1[:i, WHITE] = True  # Mark whites as possible
      a1[i:(i+l), c] = True  # Mark current color as possible
      a = np.concatenate((a1, a2), axis=0)

      # OR with previous results
      result = np.logical_or(result, a)
  
  return result