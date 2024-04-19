import numpy as np

from myfuncs import plot, msg
from myfuncs import generate, generate_count
from myfuncs import generate_with_info, generate_count_with_info
from myfuncs import generate_color_possible, totuple

def initialize(inp):
  status = inp["status"]
  limit_generate = inp["limit_generate"]
  for ori, tmp in status.items():
    len_line = len(status[1-ori])
    for line, status0 in tmp.items():
      block_colors  = tuple(status0["block_colors"])
      block_lengths = tuple(status0["block_lengths"])
      n_pos = generate_count(len_line, block_lengths, block_colors, -1)
      if n_pos < limit_generate:
        status0["possible_lines"] = generate(len_line, block_lengths, block_colors, -1)
        status0["generated"     ] = True
        status0["count"         ] = n_pos
      else:
        status0["possible_lines"] = None
        status0["generated"     ] = False
        status0["count"         ] = n_pos
      msg(ori,line,n_pos,status0["generated"])

def solve(inp):
  x = inp["x"]
  y = inp["y"]
  n_colors = inp["n_colors"]
  status = inp["status"]
  limit_generate = inp["limit_generate"]
  
  # Initialize color_possible from sweeping the input from left to right, top to bottom
  # It creates simple restrictions even from lines that were only counted
  color_possible = np.ones((y,x,n_colors))
  for ori, tmp in status.items():
    len_line = len(status[1-ori])
    for line, status0 in tmp.items():
      block_colors  = tuple(status0["block_colors"])
      block_lengths = tuple(status0["block_lengths"])
      ans = generate_color_possible(len_line, block_lengths, block_colors, n_colors)
      color_possible[:,line,:] = np.logical_and(color_possible[:,line,:], ans)
    color_possible = np.transpose(color_possible, axes=(1,0,2))
  
  it = 0
  generated = True
  worth_checking = None # Warning as not defined
  while np.any(np.sum(color_possible, axis=2)>1):
    
    it += 1
    print("\nIteration",it)
    
    old = color_possible.copy()
    for ori, pos0 in status.items():
      changed = color_possible.copy()
      for idx, status0 in pos0.items():      
        if not status0["generated"]:
          continue
              
        if not generated and not worth_checking[idx]:
          msg(ori, idx, status0["count"], "Same at   ")
          continue
        
        # Remove lines in pos, depending on solution
        possible_lines0 = status0["possible_lines"]
        for color in range(n_colors):
          for idx2, val in enumerate(color_possible[:,idx,color]):
            if val == 0:
              keep = possible_lines0[:,idx2] != color
              possible_lines0 = possible_lines0[keep,:]
        status0["count"] = len(possible_lines0)
        status0["possible_lines"] = possible_lines0
        
        msg(ori,idx,status0["count"],"Reduced to")
        
        # Update color_possible
        _, n2 = possible_lines0.shape
        allowed_colors = [set(possible_lines0[:,i]) for i in range(n2)]
        for idx2, allowed_colors0 in enumerate(allowed_colors):
          for color in range(n_colors):
            if color not in allowed_colors0:
              color_possible[idx2,idx,color] = 0
      changed2 = color_possible.copy()
      
      worth_checking = np.any(changed != changed2, axis = (1,2))
      
      color_possible = np.transpose(color_possible, axes=(1,0,2))
    
    plot(inp["desc"], it, color_possible, inp["colors"], 0)
    
    generated = False
      
    # No updates?
    if np.all(old == color_possible):
      print("\nNo update to color_possible: Generate new solutions")
          
      for ori, pos0 in status.items():
        len_line = len(status[1-ori])
        for line, status0 in pos0.items():
          if status[ori][line]["generated"]:
            continue
          block_colors  = tuple(status0["block_colors"])
          block_lengths = tuple(status0["block_lengths"])
          
          info = color_possible[:, line, :]
          n_pos = generate_count_with_info(len_line, block_lengths, block_colors, -1, totuple(info))
          
          if n_pos < limit_generate:
            status[ori][line]["possible_lines"] = generate_with_info(len_line, block_lengths, block_colors, -1, totuple(info))
            status[ori][line]["generated"     ] = True
            status[ori][line]["count"         ] = n_pos
            generated = True
          else:
            status[ori][line]["possible_lines"] = None
            status[ori][line]["generated"     ] = False
            status[ori][line]["count"         ] = n_pos
          msg(ori,line,n_pos, status[ori][line]["generated"])
        color_possible = np.transpose(color_possible, axes=(1,0,2))
            
      # If no generation was successful - we have to generate the smallest one
      if not generated:
        ori0 = -1
        line0 = -1
        count0 = 1e10
        for ori, pos0 in status.items():
          for line, status0 in pos0.items():
            if not status0["generated"] and status0["count"] < count0:
              ori0 = ori
              line0 = line
              count0 = status0["count"]
        if ori0 == 1:
          color_possible = np.transpose(color_possible, axes=(1,0,2))
        print("No line was below the generate limit",limit_generate)
        len_line = len(status[1-ori0])
        block_colors  = tuple(status[ori0][line0]["block_colors"])
        block_lengths = tuple(status[ori0][line0]["block_lengths"])
        info = color_possible[:, line0, :]
        status[ori0][line0]["possible_lines"] = generate_with_info(len_line, block_lengths, block_colors, -1, totuple(info))
        status[ori0][line0]["generated"     ] = True
        msg(ori0,line0,count0,True)
        generated = True
        if ori0 == 1:
          color_possible = np.transpose(color_possible, axes=(1,0,2))    
    