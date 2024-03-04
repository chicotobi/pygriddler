import urllib.request
from functools import cache
import os.path
import numpy as np
import matplotlib.pyplot as plt 
import matplotlib.colors

def download_and_write_file(id0):
  s1 = 'https://www.griddlers.net/nonogram/-/g/t1709243262226/i01?p_p_lifecycle=2&p_p_resource_id=griddlerPuzzle&p_p_cacheability=cacheLevelPage&_gpuzzles_WAR_puzzles_id='
  s2 = '&_gpuzzles_WAR_puzzles_lite=false&_gpuzzles_WAR_puzzles_name=touchScreen'
  link = s1 + str(id0) + s2
  s = str(urllib.request.urlopen(link).read())
 
  f = open(str(id0),'w')
  f.write(s)
  f.close()

def get_input(id0):
  fname = str(id0)
  if ~os.path.isfile(fname):
    download_and_write_file(id0)
  
  s = open(fname, 'r').read().split('\\n')
    
  inp_v = eval('[' + s[66].strip('\\t') + ']')
  inp_h = eval('[' + s[69].strip('  ').strip('\\t') + ']')
  used_colors = eval('[' + s[63].strip('  ').strip('\\t') + ']')
  colors = eval('[' + s[57].strip('  ').strip('\\t') + ']')
  
  inp = {}
  inp[0] = [[[i[0]-1, i[1]] for i in j] for j in inp_v]
  inp[1] = [[[i[0]-1, i[1]] for i in j] for j in inp_h]
    
  colors = [colors[i] for i in used_colors]
  
  return inp, colors

@cache
def generate(n, block_lengths, block_colors, previous_color):
  if len(block_lengths) == 0:
    return [[0]*n]
  l = []
  n_same_colored_neighbours = sum(np.diff(block_colors)==0)
  max_zeroes_left_side = n - sum(block_lengths) - n_same_colored_neighbours
  if block_colors[0] == previous_color:
    i0 = 1
  else:
    i0 = 0
  for i in range(i0,max_zeroes_left_side+1):
    tmp = generate(n - i - block_lengths[0], block_lengths[1:], block_colors[1:], block_colors[0])
    l += [[0]*i + [block_colors[0]]*block_lengths[0] + j for j in tmp]
  return l

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

@cache
def generate_with_info(n, block_lengths, block_colors, previous_color, info):
  if len(block_lengths) == 0:
    if all(info[:n,0]) == 1:
      return [[0]*n]
  l = []
  n_same_colored_neighbours = sum(np.diff(block_colors)==0)
  max_zeroes_left_side = n - sum(block_lengths) - n_same_colored_neighbours
  if block_colors[0] == previous_color:
    i0 = 1
  else:
    i0 = 0
  for i in range(i0,max_zeroes_left_side+1):
    tmp = generate(n - i - block_lengths[0], block_lengths[1:], block_colors[1:], block_colors[0])
    l += [[0]*i + [block_colors[0]]*block_lengths[0] + j for j in tmp]
  return l

def hex2rgb(hx):
  return tuple(int(hx[i:i+2], 16)/256 for i in (0, 2, 4))

def plot(color_possible, colors, ori):
  
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
  plt.show()