import numpy as np
from myfuncs import get_input, generate, generate_count, plot

#id0 = 241934
#id0 = 252952
#id0 = 47532
#id0 = 202358
#id0 = 39756
id0 = 275510

inp, colors = get_input(id0)

limit_generate = 1_000_000

pos = {}
for ori in range(2):
  pos[ori] = {}
  n_lines = len(inp[ori])
  len_line = len(inp[1-ori])
  for line in range(n_lines):
    block_colors  = tuple([j[0] for j in inp[ori][line]])
    block_lengths = tuple([j[1] for j in inp[ori][line]])
    n_pos = generate_count(len_line, block_lengths, block_colors, -1)
    if n_pos < limit_generate:
      pos[ori][line] = generate(len_line, block_lengths, block_colors, -1)
      print("Orientation",ori,"Line",line,": Generated",n_pos,"possibilities.")
    else:
      pos[ori][line] = -1
      print("Orientation",ori,"Line",line,": Counted",n_pos,"possibilities.")

x = len(inp[0])
y = len(inp[1])
color_possible = np.ones((x,y,len(colors)-1))
  
while np.any(np.sum(color_possible, axis=2)>1):
  for ori, pos0 in pos.items():
    for idx, line in pos0.items():
      # Update from solution
      for idx2, val in enumerate(solution[idx,]):
        if val != -1:
          line = [i for i in line if i[idx2] == val]
      
      print("Look at", ori, idx)
      
      # Now see if these solutions have given values  
      uniques = [(idx2,i.pop()) for idx2,i in enumerate(map(set, zip(*line))) if len(i)==1]
      for idx2, val in uniques:
        solution[idx][idx2] = val
      #plot(x, y, solution, colors)
    solution = solution.transpose()
  