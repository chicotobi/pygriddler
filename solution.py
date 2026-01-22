import numpy as np
import os.path
import json

from utils import plot, msg, totuple, LineStatus
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

def update_color_possible_from_line_status(ori, line, line_status, color_possible):
  """Update color_possible based on the possible lines of a specific line status."""
  n_colors = color_possible.shape[2]
  possible_lines0 = line_status.possible_lines
  _, n2 = possible_lines0.shape
  allowed_colors = [np.unique(possible_lines0[:,i]) for i in range(n2)]
  for idx2, allowed_colors0 in enumerate(allowed_colors):
    for color in range(n_colors):
      if color not in allowed_colors0:
        if ori == "horizontal":
          color_possible[line,idx2,color] = 0
        else:
          color_possible[idx2,line,color] = 0
  return color_possible

def update_line_status_from_color_possible(ori, line, line_status, color_possible):
  """Update line_status possible lines based on color_possible."""
  n_colors = color_possible.shape[2]
  old_count = line_status.count
  possible_lines0 = line_status.possible_lines
  for color in range(n_colors):
    extracted_row = extract_row(color_possible, ori, line, color)
    for idx2, val in enumerate(extracted_row):
      if val == 0:
        keep = possible_lines0[:,idx2] != color
        possible_lines0 = possible_lines0[keep,:]
  line_status.count = len(possible_lines0)
  line_status.possible_lines = possible_lines0
  msg(ori,line,line_status.count,"Reduced to",old_count)
  return line_status


def refine_solutions(inp, color_possible, check_all):
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

      if not check_all and not status0.worth_checking:
        continue
      
      status0 = update_line_status_from_color_possible(ori, idx, status0, color_possible)

      color_possible = update_color_possible_from_line_status(ori, idx, status0, color_possible)
    
    # Update worth_checking flags for each line based on changes
    if not check_all:
      if ori == "horizontal":
        for idx, status1 in status["vertical"].items():
          status1.worth_checking = np.any(color_possible_before[:,idx,:] != color_possible[:,idx,:])
      else:
        for idx, status1 in status["horizontal"].items():
          status1.worth_checking = np.any(color_possible_before[idx,:,:] != color_possible[idx,:,:])
    
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
      color_possible = update_color_possible_from_line_status(ori, line, status[ori][line], color_possible)

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
  color_possible = update_color_possible_from_line_status(ori0, line0, status[ori0][line0], color_possible)

  msg(ori0,line0,count0,True)
  
  return color_possible

def solve_iteration(inp, color_possible, it, check_all):
  """Perform one iteration of the solving algorithm."""
  print("\nIteration",it)
  
  # Refine existing solutions
  color_possible, old = refine_solutions(inp, color_possible, check_all = check_all)
  
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
      print("WARNING! No updates possible, but all lines generated - stuck!")
    check_all = True
  else:
    check_all = False
  
  return color_possible, check_all

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
  
  it = 0
  
  check_all = True
  while np.any(np.sum(color_possible, axis=2)>1):
    it += 1
    color_possible, check_all = solve_iteration(inp, color_possible, it, check_all)
  
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
    