import numpy as np
import os.path
import json
from dataclasses import dataclass
from typing import Optional

from utils import plot, msg, totuple
from generators import generate, generate_count
from generators import generate_with_info, generate_count_with_info
from generators import generate_color_possible

@dataclass
class LineStatus:
  """Tracks the state of a single row/column in the puzzle."""
  possible_lines: Optional[np.ndarray]
  generated: bool
  count: int
  worth_checking: bool = True
  
  # Keep other fields from original status dict
  block_colors: Optional[tuple] = None
  block_lengths: Optional[tuple] = None

def initialize(inp):
  status = inp["status"]
  limit_generate = inp["limit_generate"]
  other_ori = {"vertical": "horizontal", "horizontal": "vertical"}
  for ori, tmp in status.items():
    len_line = len(status[other_ori[ori]])
    for line, status0 in tmp.items():
      block_colors  = tuple(status0["block_colors"])
      block_lengths = tuple(status0["block_lengths"])
      n_pos = generate_count(len_line, block_lengths, block_colors, -1)
      if n_pos < limit_generate:
        possible_lines = generate(len_line, block_lengths, block_colors, -1)
        generated = True
      else:
        possible_lines = None
        generated = False
      
      # Replace dict with LineStatus dataclass
      tmp[line] = LineStatus(
        possible_lines=possible_lines,
        generated=generated,
        count=n_pos,
        worth_checking=True,
        block_colors=block_colors,
        block_lengths=block_lengths
      )
      msg(ori,line,n_pos,generated)

def refine_solutions(inp, color_possible, generated_new_line):
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
            
      if not generated_new_line and not status0.worth_checking:
        continue
      
      # Remove lines in pos, depending on solution
      possible_lines0 = status0.possible_lines
      old_count = status0.count
      for color in range(n_colors):
        for idx2, val in enumerate(color_possible[:,idx,color]):
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
            color_possible[idx2,idx,color] = 0
    
    # Update worth_checking flags for each line based on changes
    for idx, status0 in status[other_ori[ori]].items():
      status0.worth_checking = np.any(color_possible_before[idx] != color_possible[idx])
    
    color_possible = np.transpose(color_possible, axes=(1,0,2))
  
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
      
      info = color_possible[:, line, :]
      n_pos = generate_count_with_info(len_line, block_lengths, block_colors, -1, totuple(info))
      
      if n_pos < limit_generate:
        status[ori][line].possible_lines = generate_with_info(len_line, block_lengths, block_colors, -1, totuple(info))
        status[ori][line].generated = True
        status[ori][line].count = n_pos
        generated_new_line = True
      else:
        status[ori][line].possible_lines = None
        status[ori][line].generated = False
        status[ori][line].count = n_pos
      msg(ori,line,n_pos, status[ori][line].generated)
    color_possible = np.transpose(color_possible, axes=(1,0,2))
        
  # If no generation was successful - we have to generate the smallest one
  if not generated_new_line:
    ori0 = -1
    line0 = -1
    count0 = 1e10
    for ori, pos0 in status.items():
      for line, status0 in pos0.items():
        if not status0.generated and status0.count < count0:
          ori0 = ori
          line0 = line
          count0 = status0.count
    if ori0 == "horizontal":
      color_possible = np.transpose(color_possible, axes=(1,0,2))
    print("No line was below the generate limit",limit_generate)
    len_line = len(status[other_ori[ori0]])
    block_colors  = status[ori0][line0].block_colors
    block_lengths = status[ori0][line0].block_lengths
    info = color_possible[:, line0, :]
    status[ori0][line0].possible_lines = generate_with_info(len_line, block_lengths, block_colors, -1, totuple(info))
    status[ori0][line0].generated = True
    msg(ori0,line0,count0,True)
    generated_new_line = True
    if ori0 == "horizontal":
      color_possible = np.transpose(color_possible, axes=(1,0,2))
  
  return color_possible, generated_new_line

def solve_iteration(inp, color_possible, it, generated_new_line):
  """Perform one iteration of the solving algorithm."""
  print("\nIteration",it)
  
  # Refine existing solutions
  color_possible, old = refine_solutions(inp, color_possible, generated_new_line)
  
  if inp["plot"]:
    plot(inp["desc"], it, color_possible, inp["colors"], 0)
  
  generated_new_line = False
    
  # No updates? Generate new solutions
  if np.all(old == color_possible):
    color_possible, generated_new_line = generate_new_solutions(inp, color_possible)
  
  return color_possible, generated_new_line

def solve(inp):
  """Main solving loop - coordinates iteration, refinement, and generation."""
  x = inp["x"]
  y = inp["y"]
  n_colors = inp["n_colors"]
  status = inp["status"]
  other_ori = {"vertical": "horizontal", "horizontal": "vertical"}
  
  # Initialize color_possible from sweeping the input from left to right, top to bottom
  # It creates simple restrictions even from lines that were only counted
  color_possible = np.ones((y,x,n_colors))
  for ori, tmp in status.items():
    len_line = len(status[other_ori[ori]])
    for line, status0 in tmp.items():
      block_colors  = status0.block_colors
      block_lengths = status0.block_lengths
      ans = generate_color_possible(len_line, block_lengths, block_colors, n_colors)
      color_possible[:,line,:] = np.logical_and(color_possible[:,line,:], ans)
    color_possible = np.transpose(color_possible, axes=(1,0,2))
  
  it = 0
  generated = True
  
  while np.any(np.sum(color_possible, axis=2)>1):
    it += 1
    color_possible, generated = solve_iteration(inp, color_possible, it, generated)
  
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
    