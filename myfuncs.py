from functools import cache

import numpy as np
import matplotlib.pyplot as plt 
import matplotlib.colors

WHITE = 0
ALLOWED = 1
NOT_ALLOWED = 0
  
def msg(ori,line,n,status):
  if type(status) is str:
    s3 = status
  elif status:
    s3 = 'Generated '
  else:
    s3 = 'Counted   '
  if n == 1:
    s3 = 'Finished  '
  line = ' '*(3-len(str(line))) + str(line)
  x = 6
  s = ' '*(x*3-len(str(n))) + str(n)
  s2 = '.'.join([s[3*i:3*i+3] for i in range(x)])

  print("O"+str(ori)+"L"+str(line),s3,s2)


@cache
def generate(n, block_lengths, block_colors, previous_color):
  if len(block_lengths) == 0:
    return np.zeros((1,n), dtype = np.uint8)
  l = []
  n_same_colored_neighbours = sum(np.diff(block_colors)==0)
  max_zeroes_left_side = n - sum(block_lengths) - n_same_colored_neighbours
  if block_colors[0] == previous_color:
    i0 = 1
  else:
    i0 = 0
  for i in range(i0,max_zeroes_left_side+1):
    a3 = generate(n - i - block_lengths[0], block_lengths[1:], block_colors[1:], block_colors[0])
    nrow, _ = a3.shape
    a1 = np.zeros((nrow,i), dtype = np.uint8)
    a2 = np.ones((nrow, block_lengths[0]), dtype = np.uint8) * block_colors[0]
    a = np.concatenate((a1,a2,a3),axis=1)
    l.append(a)
  return np.concatenate(l)

@cache
def generate_count(n, block_lengths, block_colors, previous_color):
  if len(block_lengths) == 0:
    return 1
  l = 0
  n_same_colored_neighbours = sum(np.diff(block_colors)==0)
  max_zeroes_left_side = n - sum(block_lengths) - n_same_colored_neighbours
  if block_colors[0] == previous_color:
    i0 = 1
  else:
    i0 = 0
  for i in range(i0,max_zeroes_left_side+1):
    tmp = generate_count(n - i - block_lengths[0], block_lengths[1:], block_colors[1:], block_colors[0])
    l += tmp
  return l

def totuple(x):
  return tuple(tuple(i) for i in x)

@cache
def generate_with_info(n, block_lengths, block_colors, previous_color, info):
  if len(info) == 0:
    return generate(n, block_lengths, block_colors, previous_color)
  info = np.asarray(info)
  if len(block_lengths) == 0:
    if all(info[:,WHITE]) == ALLOWED:
      return np.zeros((1,n), dtype = np.uint8)
    else:
      return np.zeros((0,n), dtype = np.uint8)
  pos = []
  n_same_colored_neighbours = sum(np.diff(block_colors)==0)
  max_zeroes_left_side_from_input = n - sum(block_lengths) - n_same_colored_neighbours
   
  # Find the first index where no white is allowed
  tmp = np.nonzero(info[:,WHITE] == NOT_ALLOWED)[0]
  if len(tmp) > 0:
    max_zeroes_left_side_from_info = tmp[0]
  else:
    max_zeroes_left_side_from_info = n
  
  l = block_lengths[0]
  c = block_colors[0]
  
  max_zeroes_left_side = min(max_zeroes_left_side_from_input, max_zeroes_left_side_from_info)
  if block_colors[0] == previous_color:
    i0 = 1
  else:
    i0 = 0
  for i in range(i0,max_zeroes_left_side+1):
    # We checked that the white blocks are allowed, now check, if the colored block is allowed:
    if all(info[i:(i+l),c] == 1):
      a3 = generate_with_info(n - i - l, block_lengths[1:], block_colors[1:], block_colors[0], totuple(info[i+l:,]))
      nrow, _ = a3.shape
      if a3.shape[0] > 0:
        a1 = np.zeros((nrow,i), dtype = np.uint8)
        a2 = np.ones((nrow, block_lengths[0]), dtype = np.uint8) * block_colors[0]
        a = np.concatenate((a1,a2,a3),axis=1)
        pos.append(a)
  if len(pos) > 0:
    return np.concatenate(pos)
  else:
    return np.zeros((0,n))

@cache
def generate_count_with_info(n, block_lengths, block_colors, previous_color, info):
  if len(info) == 0:
    return generate_count(n, block_lengths, block_colors, previous_color)
  info = np.asarray(info)
  if len(block_lengths) == 0:
    if all(info[:,WHITE]) == ALLOWED:
      return 1
    else:
      return 0
  count = 0
  n_same_colored_neighbours = sum(np.diff(block_colors)==0)
  max_zeroes_left_side_from_input = n - sum(block_lengths) - n_same_colored_neighbours
   
  # Find the first index where no white is allowed
  tmp = np.nonzero(info[:,WHITE] == NOT_ALLOWED)[0]
  if len(tmp) > 0:
    max_zeroes_left_side_from_info = tmp[0]
  else:
    max_zeroes_left_side_from_info = n
  
  l = block_lengths[0]
  c = block_colors[0]
  
  max_zeroes_left_side = min(max_zeroes_left_side_from_input, max_zeroes_left_side_from_info)
  if block_colors[0] == previous_color:
    i0 = 1
  else:
    i0 = 0
  for i in range(i0,max_zeroes_left_side+1):
    # We checked that the white blocks are allowed, now check, if the colored block is allowed:
    if all(info[i:(i+l),c] == 1):
      tmp = generate_count_with_info(n - i - l, block_lengths[1:], block_colors[1:], block_colors[0], totuple(info[i+l:,]))
      count += tmp
  return count

def generate_color_possible(n, block_lengths, block_colors, n_colors):
  color_possible = np.zeros((n,n_colors))
  
  # Zero is always possible, because it's really difficult to find out, where whites are possible
  color_possible[:,0] = 1
  
  # Stupid edge case - if no blocks, only white is possible
  if len(block_lengths) == 0:
    return color_possible
  
  # Compressed representation
  line = [block_colors[0]] * block_lengths[0]
  for i in range(1,len(block_lengths)):
    if block_colors[i-1] == block_colors[i]:
      line += [0]
    line += [block_colors[i]] * block_lengths[i]
    
  
  for i in range(n-len(line)+1):
    for j in range(len(line)):
      c = line[j]
      color_possible[i+j,c] = 1
  
  
  return color_possible
  

def hex2rgb(hx):
  return tuple(int(hx[i:i+2], 16)/256 for i in (0, 2, 4))

def plot(title, iteration, color_possible, colors, ori):
  
  plt.clf()
  if ori == 1:    
    color_possible = np.transpose(color_possible, axes=(1,0,2))
      
  colors = ['808080'] + colors
  cmap = [hex2rgb(i) for i in colors]
  cmap = matplotlib.colors.ListedColormap(cmap)
  
  x, y, ncolors = color_possible.shape
  data = -1 * np.ones((x, y))
  for i in range(x):
    for j in range(y):
      if sum(color_possible[i,j,:]) == 1:
        #print(np.where(color_possible[i,j,:]))
        data[i,j] = np.where(color_possible[i,j,:])[0] + 1
      else:
        data[i,j] = -1
  plt.imshow(data, interpolation='nearest', cmap = cmap,  vmin=-1, vmax=len(colors))
  plt.gca().get_xaxis().set_visible(False)
  plt.gca().get_yaxis().set_visible(False)
  plt.title(title+" - "+str(iteration))
  plt.show()
