# from generators import generate_count, generate

# def pr0(x):
#   s = '\n'.join(''.join(str(j) for j in i) for i in x)
#   print(s)
  
# # Test case
# n = 30
# block_lengths = (2, 2, 3, 3)
# block_colors = (1, 1, 1, 1)
# previous_color = -1
# ans = generate(n, block_lengths, block_colors, previous_color)
# pr0(ans)

# n = 40
# block_lengths = (2, 2, 3, 3, 4, 4)
# block_colors = (1, 1, 2, 2, 2, 2)
# previous_color = -1
# ans = generate(n, block_lengths, block_colors, previous_color)
# pr0(ans)

# n = 50
# block_lengths = (1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
# block_colors = (1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
# previous_color = -1
# ans = generate_count(n, block_lengths, block_colors, previous_color)
# pr0(ans)

# info = np.ones((n,2))
# info[4,1] = 0
# ans = generate_with_info(n, block_lengths, block_colors, previous_color, info)
# pr0(ans)

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
