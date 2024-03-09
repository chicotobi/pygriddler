import numpy as np
from myfuncs import get_input, get_title
from myfuncs import generate, generate_count, plot, generate_with_info, generate_count_with_info
from myfuncs import generate_color_possible

example = 8

if   example == 1: # Owl           30 x 35 x 2
  id0 = 241934     
elif example == 2: # Dog           40 x 45 x 2
  id0 = 252952    
elif example == 3: # NOT SOLVED?
  id0 = 32310
elif example == 4: # Maple leaf    30 x 30 x 2
  id0 = 202358     
elif example == 5: # Beautiful eye 35 x 25 x 7
  id0 = 39756     
elif example == 6: # Flamingo      13 x 20 x 4
  id0 = 275510
elif example == 7: # Rosebud       27 x 45 x 8
  id0 = 236744
elif example == 8: # Santorini     40 x 50 x 8
  id0 = 233499    
elif example == 9: # Family in the Summer Heat 50 x 50 x 6 - NOT SOLVED
  id0 = 118315
elif example == 10:
  id0 = 88712
elif example == 11:
  id0 = 42015

status, colors = get_input(id0)
x = len(status[0])
y = len(status[1])
n_colors = len(colors)

limit_generate = 1_000_000

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
      print("O",ori,"L",line,": Generated",n_pos,"possibilities.")
    else:
      status0["possible_lines"] = None
      status0["generated"     ] = False
      status0["count"         ] = n_pos
      print("O",ori,"L",line,": Counted",n_pos,"possibilities.")


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


title = "{ttl} {x} x {y} x {n_colors}\n{id0}".format(ttl=get_title(id0),x=x,y=y,n_colors=n_colors,id0=id0)

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
    color_possible = np.transpose(color_possible, axes=(1,0,2))
  
  plot(title, color_possible, colors, 0)
    
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
        #info = tuple(tuple(i) for i in info)
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
          
  