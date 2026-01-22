import numpy as np
import os.path
import json

from utils import plot, msg, totuple
from puzzle_line import PuzzleLine
from generators import generate, generate_count
from generators import generate_with_info, generate_count_with_info
from generators import generate_color_possible

def initialize(inp):
  status = inp["status"]
  limit_generate = inp["limit_generate"]
  other_ori = {"vertical": "horizontal", "horizontal": "vertical"}
  for ori, tmp in status.items():
    len_line = len(status[other_ori[ori]])
    for line, status0 in tmp.items():
      block_colors  = status0.block_colors
      block_lengths = status0.block_lengths
      n_pos = generate_count(len_line, block_lengths, block_colors, -1)
      status0.count = n_pos
      if n_pos < limit_generate:
        status0.possible_lines = generate(len_line, block_lengths, block_colors, -1)
        status0.generated = True
      msg(ori,line,n_pos,status0.generated)

def extract_row_2(color_possible, ori, idx):
  """Extract a specific row or column from color_possible based on orientation."""
  if ori == "vertical":
    return color_possible[:, idx, :]
  else:
    return color_possible[idx, :, :]

def extract_row(color_possible, ori, idx, color):
  """Extract a specific row or column from color_possible based on orientation."""
  if ori == "vertical":
    return color_possible[:, idx, color]
  else:
    return color_possible[idx, :, color]

def solved(color_possible):
  """Check if the puzzle is solved (each cell has exactly one possible color)."""
  return np.all(np.sum(color_possible, axis=2) == 1)

def apply_line_constraints(ori, line, line_status, color_possible):
  """Apply line constraints to color_possible based on allowed colors."""
  allowed_colors = line_status.get_allowed_colors()
  if allowed_colors is None:
    return
  n_colors = color_possible.shape[2]
  for idx2, allowed_colors0 in enumerate(allowed_colors):
    for color in range(n_colors):
      if color not in allowed_colors0:
        if ori == "horizontal":
          color_possible[line,idx2,color] = 0
        else:
          color_possible[idx2,line,color] = 0

def refine_solutions(inp, color_possible):
  """Refine existing solutions by filtering possible lines based on color_possible."""
  status = inp["status"]
  n_colors = inp["n_colors"]
  
  other_ori = {"vertical": "horizontal", "horizontal": "vertical"}
  
  old = color_possible.copy()
  for ori, pos0 in status.items():
    color_possible_before = color_possible.copy()
    for idx, status0 in pos0.items():
      if not status0.generated:
        continue

      # If the relevant slice of color_possible hasn't changed, skip
      if np.all(status0.slice_of_color_possible == extract_row_2(color_possible, ori, idx)):
        continue
      
      status0.update_from_color_possible(ori, idx, color_possible, msg)
      apply_line_constraints(ori, idx, status0, color_possible)
      status0.slice_of_color_possible = extract_row_2(color_possible, ori, idx).copy()
    
  return color_possible, old

def generate_new_solutions(inp, color_possible):
  """Generate new solutions for lines that haven't been generated yet."""
  status = inp["status"]
  n_colors = inp["n_colors"]
  limit_generate = inp["limit_generate"]
  generated_new_line = False
  other_ori = {"vertical": "horizontal", "horizontal": "vertical"}
  
  print("\nNo update to color_possible: Generate new solutions")
      
  for ori, pos0 in status.items():
    len_line = len(status[other_ori[ori]])
    for line, status0 in pos0.items():
      if status[ori][line].generated:
        continue
      block_colors  = status0.block_colors
      block_lengths = status0.block_lengths
      
      info = extract_row_2(color_possible, ori, line)
      n_pos = generate_count_with_info(len_line, block_lengths, block_colors, -1, totuple(info))
      
      status[ori][line].count = n_pos
      if n_pos < limit_generate:
        status[ori][line].possible_lines = generate_with_info(len_line, block_lengths, block_colors, -1, totuple(info))
        status[ori][line].generated = True
        generated_new_line = True
      msg(ori,line,n_pos, status[ori][line].generated)

      # Update color_possible
      apply_line_constraints(ori, line, status[ori][line], color_possible)

  if generated_new_line:
    return color_possible
        
  print("No line was below the generate limit",limit_generate)

  # Find minimum count among non-generated
  ori0 = None
  line0 = None
  count0 = 1e10
  for ori, pos0 in status.items():
    for line, status0 in pos0.items():
      if not status0.generated and status0.count < count0:
        ori0, line0, count0 = ori, line, status0.count
  len_line = len(status[other_ori[ori0]])
  block_colors  = status[ori0][line0].block_colors
  block_lengths = status[ori0][line0].block_lengths
  info = extract_row_2(color_possible, ori0, line0)
  status[ori0][line0].possible_lines = generate_with_info(len_line, block_lengths, block_colors, -1, totuple(info))
  status[ori0][line0].generated = True

  # Update color_possible
  apply_line_constraints(ori0, line0, status[ori0][line0], color_possible)

  msg(ori0,line0,count0,True)
  
  return color_possible

def solve_iteration(inp, color_possible, it):
  """Perform one iteration of the solving algorithm."""
  print("\nIteration",it)
  
  # Refine existing solutions
  color_possible, old = refine_solutions(inp, color_possible)
  
  if inp["plot"]:
    plot(inp["desc"], it, color_possible, inp["colors"], 0)
    
  # No updates? Generate new solutions
  if np.all(old == color_possible):
    # Check if there are still non-generated lines
    still_non_generated = False
    for ori, pos0 in inp["status"].items():
      for line, status0 in pos0.items():
        if not status0.generated:
          still_non_generated = True
          break
      if still_non_generated:
        break
    if still_non_generated:
      color_possible = generate_new_solutions(inp, color_possible)
    else: 
      raise Exception("WARNING! No updates possible, but all lines generated - stuck!")
  
  return color_possible

def solve(inp):
  """Main solving loop - coordinates iteration, refinement, and generation."""
  x = inp["x"]
  y = inp["y"]
  n_colors = inp["n_colors"]
  status = inp["status"]
  
  # Initialize color_possible from sweeping the input from left to right, top to bottom
  # It creates simple restrictions even from lines that were only counted
  color_possible = np.ones((y,x,n_colors))
  for ori, tmp in status.items():
    if ori == "horizontal":
      len_line = len(status["vertical"])
    else:
      len_line = len(status["horizontal"])
    for line, status0 in tmp.items():
      block_colors  = status0.block_colors
      block_lengths = status0.block_lengths
      ans = generate_color_possible(len_line, block_lengths, block_colors, n_colors)
      if ori == "vertical":
        color_possible[:,line,:] = np.logical_and(color_possible[:,line,:], ans)
      else:
        color_possible[line,:,:] = np.logical_and(color_possible[line,:,:], ans)

  # Trigger initial update of line_status
  for ori, tmp in status.items():
    for line, status0 in tmp.items():
      status0.slice_of_color_possible = extract_row_2(color_possible, ori, line) * -1

  it = 0  
  while not solved(color_possible):
    it += 1
    color_possible = solve_iteration(inp, color_possible, it)
  
  # Save solution
  solution_file = os.path.join('solutions', 'python', str(inp["id0"]) + '.npy')
  np.save(solution_file, color_possible)
  
  # Also save as JSON with the solution grid
  solution = np.argmax(color_possible, axis=2)
  solution_json = os.path.join('solutions', 'python', str(inp["id0"]) + '.json')
  with open(solution_json, 'w') as f:
    json.dump({
      "id0": inp["id0"],
      "desc": inp["desc"],
      "solution": solution.tolist(),
      "colors": inp["colors"]
    }, f, indent=2)
  
  # Save PNG of final solution
  plot(inp["desc"], "FINAL", color_possible, inp["colors"], 0)
  png_file = os.path.join('solutions', 'python','png', str(inp["id0"]) + '.png')
  import matplotlib.pyplot as plt
  plt.savefig(png_file, bbox_inches='tight', dpi=150)    
    