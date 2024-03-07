from myfuncs import generate, generate_with_info
import numpy as np


def pr0(x):
  s = '\n'.join(''.join(str(j) for j in i) for i in x)
  print(s)
  
# Test case
n = 10
block_lengths = (2, 3)
block_colors = (1, 1)
previous_color = -1

ans = generate(n, block_lengths, block_colors, previous_color)
pr0(ans)

info = np.ones((n,2))
info[4,1] = 0
ans = generate_with_info(n, block_lengths, block_colors, previous_color, info)
pr0(ans)

# info = np.ones((n,2))
# info[4,1] = 0
# ans = generate_with_info(n, block_lengths, block_colors, previous_color, info)
# pr0(ans)


# Test case
# n = 7
# block_lengths = (3,)
# block_colors = (1,)
# previous_color = -1

# ans = generate(n, block_lengths, block_colors, previous_color)
# pr0(ans)

# info = np.ones((n,2))
# info[3,0] = 0
# ans = generate_with_info(n, block_lengths, block_colors, previous_color, info)
# pr0(ans)
