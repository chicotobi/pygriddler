from myfuncs import generate, generate_with_info
import numpy as np

# Test cases
n = 10
block_lengths = (2, 3)
block_colors = (1, 1)
previous_color = -1

ans = generate(n, block_lengths, block_colors, previous_color)
print(ans)


info = np.ones((n,2))
info[4,0] = 0
ans = generate_with_info(n, block_lengths, block_colors, previous_color, info)
print(ans)

info = np.ones((n,2))
info[4,1] = 0
ans = generate_with_info(n, block_lengths, block_colors, previous_color, info)
print(ans)