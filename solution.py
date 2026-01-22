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

def refine_solutions(inp, color_possible):
  """Refine existing solutions by filtering possible lines based on color_possible."""
  status = inp["status"]
  n_colors = inp["n_colors"]
  
  other_ori = {"vertical": "horizontal", "horizontal": "vertical"}
  
  old = color_possible.copy()
  for ori, pos0 in status.items():
    color_possible_before = color_possible.copy()
    for idx, status0 in pos0.items():      
      if not status0.generated or not status0.worth_checking:
        continue
      
      # Remove lines in pos, depending on solution
      possible_lines0 = status0.possible_lines
      old_count = status0.count
      for color in range(n_colors):
        extracted_row = extract_row(color_possible, ori, idx, color)
        for idx2, val in enumerate(extracted_row):
          if val == 0:
            keep = possible_lines0[:,idx2] != color
            possible_lines0 = possible_lines0[keep,:]
      status0.count = len(possible_lines0)
      status0.possible_lines = possible_lines0
      
      msg(ori,idx,status0.count,"Reduced to",old_count)
      
      # Update color_possible
      _, n2 = possible_lines0.shape
      allowed_colors = [np.unique(possible_lines0[:,i]) for i in range(n2)]
      for idx2, allowed_colors0 in enumerate(allowed_colors):
        for color in range(n_colors):
          if color not in allowed_colors0:
            if ori == "horizontal":
              color_possible[idx,idx2,color] = 0
            else:
              color_possible[idx2,idx,color] = 0
    
    # Update worth_checking flags for each line based on changes
    # for idx, status1 in status[other_ori[ori]].items():
    #   status1.worth_checking = np.any(color_possible_before[idx,:,:] != color_possible[idx,:,:])   
  
  return color_possible, old

def generate_new_solutions(inp, color_possible):
  """Generate new solutions for lines that haven't been generated yet."""
  status = inp["status"]
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
        # So we generated a new line, which may create new restrictions for the other orientation
        # Set worth_checking TRUE for the OTHER orientation lines
        # for idx, status_other in status[other_ori[ori]].items():
        #   status_other.worth_checking = True
      msg(ori,line,n_pos, status[ori][line].generated)
        
  # If no generation was successful - we have to generate the smallest one
  if not generated_new_line:
    print("No line was below the generate limit",limit_generate)
    # Find minimum count among non-generated
    ori0 = None
    line0 = None
    count0 = 1e10
    for ori, pos0 in status.items():
      for line, status0 in pos0.items():
        if not status0.generated and status0.count < count0:
          ori0, line0, count0 = ori, line, status0.count
    if ori0 is None:
      # This is a bug, we look for non-generated lines but all are generated
      # Somehow our decision "We have to generate a new line" was wrong
      # For now, just return, but we should look into it
      # Just reset all worth_checking flags to True
      for ori, pos0 in status.items():
        for line, status0 in pos0.items():
          status0.worth_checking = True
      return color_possible      
    len_line = len(status[other_ori[ori0]])
    block_colors  = status[ori0][line0].block_colors
    block_lengths = status[ori0][line0].block_lengths
    info = extract_row_2(color_possible, ori0, line0)
    status[ori0][line0].possible_lines = generate_with_info(len_line, block_lengths, block_colors, -1, totuple(info))
    status[ori0][line0].generated = True
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
    color_possible = generate_new_solutions(inp, color_possible)

  # Wait for a second
  #from time import sleep
  #sleep(1)  
  
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
  
  it = 0
  
  while np.any(np.sum(color_possible, axis=2)>1):
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
    