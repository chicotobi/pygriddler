import numpy as np

from utils import create_data_from_color_possible, plot, msg, totuple
from generators import generate, generate_count
from generators import generate_with_info, generate_count_with_info
from generators import generate_color_possible

def initialize(inp, verbose=True):
  h_constraints = inp["h_constraints"]
  v_constraints = inp["v_constraints"]
  limit_generate = inp["limit_generate"]
  
  # Process horizontal constraints (rows)
  for line, constraint in enumerate(h_constraints):
    len_line = inp["width"]
    block_colors  = tuple(constraint["block_colors"])
    block_lengths = tuple(constraint["block_lengths"])
    n_pos = generate_count(len_line, block_lengths, block_colors, -1)
    if n_pos < limit_generate:
      constraint["possible_lines"] = generate(len_line, block_lengths, block_colors, -1)
      constraint["generated"     ] = True
      constraint["count"         ] = n_pos
    else:
      constraint["possible_lines"] = None
      constraint["generated"     ] = False
      constraint["count"         ] = n_pos
    msg(1, line, n_pos, constraint["generated"], verbose=verbose)
  
  # Process vertical constraints (columns)
  for line, constraint in enumerate(v_constraints):
    len_line = inp["height"]
    block_colors  = tuple(constraint["block_colors"])
    block_lengths = tuple(constraint["block_lengths"])
    n_pos = generate_count(len_line, block_lengths, block_colors, -1)
    if n_pos < limit_generate:
      constraint["possible_lines"] = generate(len_line, block_lengths, block_colors, -1)
      constraint["generated"     ] = True
      constraint["count"         ] = n_pos
    else:
      constraint["possible_lines"] = None
      constraint["generated"     ] = False
      constraint["count"         ] = n_pos
    msg(0, line, n_pos, constraint["generated"], verbose=verbose)

def solve(inp, verbose=True):
  width = inp["width"]
  height = inp["height"]
  n_colors = inp["n_colors"]
  h_constraints = inp["h_constraints"]
  v_constraints = inp["v_constraints"]
  limit_generate = inp["limit_generate"]
  
  # Initialize color_possible from sweeping the input from left to right, top to bottom
  # It creates simple restrictions even from lines that were only counted
  color_possible = np.ones((height, width, n_colors))
  
  # Process horizontal constraints (rows)
  for line, constraint in enumerate(h_constraints):
    len_line = width
    block_colors  = tuple(constraint["block_colors"])
    block_lengths = tuple(constraint["block_lengths"])
    ans = generate_color_possible(len_line, block_lengths, block_colors, n_colors)
    color_possible[line, :, :] = np.logical_and(color_possible[line, :, :], ans)
  
  # Process vertical constraints (columns)
  for line, constraint in enumerate(v_constraints):
    len_line = height
    block_colors  = tuple(constraint["block_colors"])
    block_lengths = tuple(constraint["block_lengths"])
    ans = generate_color_possible(len_line, block_lengths, block_colors, n_colors)
    color_possible[:, line, :] = np.logical_and(color_possible[:, line, :], ans)
  
  it = 0
  generated = True
  worth_checking_h = None
  worth_checking_v = None
  
  while np.any(np.sum(color_possible, axis=2) > 1):
    
    it += 1
    if verbose:
      print("\nIteration", it)
    
    old = color_possible.copy()
    
    # Process horizontal constraints (rows)
    changed = color_possible.copy()
    for idx, constraint in enumerate(h_constraints):
      if not constraint["generated"]:
        continue
            
      if not generated and not worth_checking_h[idx]:
        continue
      
      # Remove lines in pos, depending on solution
      possible_lines0 = constraint["possible_lines"]
      old_count = constraint["count"]
      for color in range(n_colors):
        for idx2, val in enumerate(color_possible[idx, :, color]):
          if val == 0:
            keep = possible_lines0[:, idx2] != color
            possible_lines0 = possible_lines0[keep, :]
      constraint["count"] = len(possible_lines0)
      constraint["possible_lines"] = possible_lines0
      
      msg(1, idx, constraint["count"], "Reduced to", old_count, verbose=verbose)
      
      # Update color_possible
      _, n2 = possible_lines0.shape
      allowed_colors = [np.unique(possible_lines0[:, i]) for i in range(n2)]
      for idx2, allowed_colors0 in enumerate(allowed_colors):
        for color in range(n_colors):
          if color not in allowed_colors0:
            color_possible[idx, idx2, color] = 0
    
    changed2 = color_possible.copy()
    worth_checking_h = np.any(changed != changed2, axis=(1, 2))
    
    # Process vertical constraints (columns)
    changed = color_possible.copy()
    for idx, constraint in enumerate(v_constraints):
      if not constraint["generated"]:
        continue
            
      if not generated and worth_checking_v is not None and not worth_checking_v[idx]:
        continue
      
      # Remove lines in pos, depending on solution
      possible_lines0 = constraint["possible_lines"]
      old_count = constraint["count"]
      for color in range(n_colors):
        for idx2, val in enumerate(color_possible[:, idx, color]):
          if val == 0:
            keep = possible_lines0[:, idx2] != color
            possible_lines0 = possible_lines0[keep, :]
      constraint["count"] = len(possible_lines0)
      constraint["possible_lines"] = possible_lines0
      
      msg(0, idx, constraint["count"], "Reduced to", old_count, verbose=verbose)
      
      # Update color_possible
      _, n2 = possible_lines0.shape
      allowed_colors = [np.unique(possible_lines0[:, i]) for i in range(n2)]
      for idx2, allowed_colors0 in enumerate(allowed_colors):
        for color in range(n_colors):
          if color not in allowed_colors0:
            color_possible[idx2, idx, color] = 0
    
    changed2 = color_possible.copy()
    worth_checking_v = np.any(changed != changed2, axis=(0, 2))
    
    if inp.get("plot", False):
      plot(f"Puzzle {inp['id']}", it, color_possible, inp["colors"], 0)
    
    generated = False
      
    # No updates?
    if np.all(old == color_possible):
      if verbose:
        print("\nNo update to color_possible: Generate new solutions")
          
      # Try to generate horizontal constraints
      for line, constraint in enumerate(h_constraints):
        if constraint["generated"]:
          continue
        block_colors  = tuple(constraint["block_colors"])
        block_lengths = tuple(constraint["block_lengths"])
        
        info = color_possible[line, :, :]
        n_pos = generate_count_with_info(width, block_lengths, block_colors, -1, totuple(info))
        
        if n_pos < limit_generate:
          constraint["possible_lines"] = generate_with_info(width, block_lengths, block_colors, -1, totuple(info))
          constraint["generated"] = True
          constraint["count"] = n_pos
          generated = True
        else:
          constraint["possible_lines"] = None
          constraint["generated"] = False
          constraint["count"] = n_pos
        msg(1, line, n_pos, constraint["generated"], verbose=verbose)
      
      # Try to generate vertical constraints
      for line, constraint in enumerate(v_constraints):
        if constraint["generated"]:
          continue
        block_colors  = tuple(constraint["block_colors"])
        block_lengths = tuple(constraint["block_lengths"])
        
        info = color_possible[:, line, :]
        n_pos = generate_count_with_info(height, block_lengths, block_colors, -1, totuple(info))
        
        if n_pos < limit_generate:
          constraint["possible_lines"] = generate_with_info(height, block_lengths, block_colors, -1, totuple(info))
          constraint["generated"] = True
          constraint["count"] = n_pos
          generated = True
        else:
          constraint["possible_lines"] = None
          constraint["generated"] = False
          constraint["count"] = n_pos
        msg(0, line, n_pos, constraint["generated"], verbose=verbose)
            
      # If no generation was successful - we have to generate the smallest one
      if not generated:
        if verbose:
          print("No line was below the generate limit", limit_generate)
        
        # Find the smallest count
        min_count = 1e10
        min_is_h = True
        min_line = -1
        
        for line, constraint in enumerate(h_constraints):
          if not constraint["generated"] and constraint["count"] < min_count:
            min_is_h = True
            min_line = line
            min_count = constraint["count"]
        
        for line, constraint in enumerate(v_constraints):
          if not constraint["generated"] and constraint["count"] < min_count:
            min_is_h = False
            min_line = line
            min_count = constraint["count"]
        
        if min_is_h:
          constraint = h_constraints[min_line]
          block_colors  = tuple(constraint["block_colors"])
          block_lengths = tuple(constraint["block_lengths"])
          info = color_possible[min_line, :, :]
          constraint["possible_lines"] = generate_with_info(width, block_lengths, block_colors, -1, totuple(info))
          constraint["generated"] = True
          msg(1, min_line, min_count, True, verbose=verbose)
        else:
          constraint = v_constraints[min_line]
          block_colors  = tuple(constraint["block_colors"])
          block_lengths = tuple(constraint["block_lengths"])
          info = color_possible[:, min_line, :]
          constraint["possible_lines"] = generate_with_info(height, block_lengths, block_colors, -1, totuple(info))
          constraint["generated"] = True
          msg(0, min_line, min_count, True, verbose=verbose)
        
        generated = True    

  return create_data_from_color_possible(color_possible)
    