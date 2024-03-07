import numpy as np
from myfuncs import get_input, generate, generate_count, plot, generate_with_info, generate_count_with_info

#id0 = 241934
#id0 = 252952
#id0 = 47532
#id0 = 202358
id0 = 39756
#id0 = 275510

inp, colors = get_input(id0)

limit_generate = 1_000_000

status = {}
for ori in range(2):
  status[ori] = {}
  n_lines = len(inp[ori])
  len_line = len(inp[1-ori])
  for line in range(n_lines):
    status[ori][line] = {}
    block_colors  = tuple([j[0] for j in inp[ori][line]])
    block_lengths = tuple([j[1] for j in inp[ori][line]])
    n_pos = generate_count(len_line, block_lengths, block_colors, -1)
    if n_pos < limit_generate:
      status[ori][line]["possible_lines"] = generate(len_line, block_lengths, block_colors, -1)
      status[ori][line]["generated"     ] = True
      status[ori][line]["count"         ] = n_pos
      print("O",ori,"L",line,": Generated",n_pos,"possibilities.")
    else:
      status[ori][line]["possible_lines"] = None
      status[ori][line]["generated"     ] = False
      status[ori][line]["count"         ] = n_pos
      print("O",ori,"L",line,": Counted",n_pos,"possibilities.")

x = len(inp[0])
y = len(inp[1])
n_colors = len(colors)
color_possible = np.ones((y,x,n_colors))

it = 0
while np.any(np.sum(color_possible, axis=2)>1):
  
  it += 1
  print("\nIteration",it)
  
  old = color_possible.copy()
  for ori, pos0 in status.items():
    for idx, status0 in pos0.items():      
      #assert(color_possible.shape[0] == len(possible_lines0[0]))      
      #assert(color_possible.shape[1] == len(pos0))
      if not status0["generated"]:
        continue
      
      # Remove lines in pos, depending on solution
      possible_lines0 = status0["possible_lines"]
      for color in range(n_colors):
        for idx2, val in enumerate(color_possible[:,idx,color]):
          if val == 0:
            possible_lines0 = [i for i in possible_lines0 if i[idx2] != color]
      status0["count"] = len(possible_lines0)
      
      print("O", ori, "L", idx,": Possible solutions:",status0["count"])
      
      # Update color_possible
      allowed_colors = list(map(set, zip(*possible_lines0)))
      for idx2, allowed_colors0 in enumerate(allowed_colors):
        for color in range(n_colors):
          if color not in allowed_colors0:
            color_possible[idx2,idx,color] = 0
      plot(color_possible, colors, ori)
    color_possible = np.transpose(color_possible, axes=(1,0,2))
    
  # No updates?
  if np.all(old == color_possible):
    print("\nNo update to color_possible: Generate new solutions")
    
    for ori, pos0 in status.items():
      len_line = len(inp[1-ori])
      for line, status0 in pos0.items():
        if status[ori][line]["generated"]:
          continue
        status[ori][line] = {}
        block_colors  = tuple([j[0] for j in inp[ori][line]])
        block_lengths = tuple([j[1] for j in inp[ori][line]])
        
        info = color_possible[:, line, :]
        #if ori == 1 and line == 0:
        #  raise
        n_pos = generate_count_with_info(len_line, block_lengths, block_colors, -1, info)
        
        if n_pos < limit_generate:
          status[ori][line]["possible_lines"] = generate_with_info(len_line, block_lengths, block_colors, -1, info)
          status[ori][line]["generated"     ] = True
          status[ori][line]["count"         ] = n_pos
          print("O",ori,"L",line,": Generated",n_pos,"possibilities.")
        else:
          status[ori][line]["possible_lines"] = None
          status[ori][line]["generated"     ] = False
          status[ori][line]["count"         ] = n_pos
          print("O",ori,"L",line,": Counted",n_pos,"possibilities.")
      color_possible = np.transpose(color_possible, axes=(1,0,2))
          
  