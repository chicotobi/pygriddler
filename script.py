from functools import cache

# inp_v = [
#   [5],
#   [2,2,2],
#   [5,3,1],
#   [1,1,1,1],
#   [5,3,1],
#   [2,2,2],
#   [5]
#   ]

# inp_h =[
#   [5],
#   [2,2],
#   [1,1],
#   [1,1],
#   [2,2],
#   [2,2],
#   [1,3,1],
#   [1,1,1,1],
#   [1,3,1],
#   [2,2],
#   [5],
#   ]

from input_files import *

x = len(inp_v)
y = len(inp_h)

@cache
def generate(n, blocks):
  if len(blocks) == 0:
    return [[0]*n]
  l = []
  nblocks = len(blocks)
  max_shift = n - sum(blocks) - nblocks + 1
  for i in range(1,max_shift+1):
    l += [[0]*i + [1]*blocks[0] + j for j in generate(n-i-blocks[0],blocks[1:])]
  return l

pos = {'h':{},'v':{}}
for i in range(x):
  print("x",i/x)
  tmp = generate(y+1, tuple(inp_v[i]))
  tmp = [j[1:] for j in tmp]
  pos['v'][i] = tmp
for i in range(y):
  print("y",i/y)
  tmp = generate(x+1, tuple(inp_h[i]))
  tmp = [j[1:] for j in tmp]
  pos['h'][i] = tmp

solution = [[-1 for i in range(x)] for j in range(y)]

def t(x):
  return list(map(list, zip(*solution)))

def pr(s, ori):
  if ori == 'v':
    s = t(s)
  white = '█'
  black = ' '
  unknown = '·'
  s = [[white if i==0 else black if i==1 else unknown for i in j] for j in s]
  print('\n'.join(''.join(i) for i in s))
  
while any(i for j in solution for i in j if i== -1):
  for ori, pos0 in pos.items():
    for idx, line in pos0.items():
      # Update from solution
      for idx2, val in enumerate(solution[idx]):
        if val != -1:
          line = [i for i in line if i[idx2] == val]
      
      print("Look at", ori, idx)
      
      # Now see if these solutions have given values  
      uniques = [(idx2,i.pop()) for idx2,i in enumerate(map(set, zip(*line))) if len(i)==1]
      for idx2, val in uniques:
        solution[idx][idx2] = val
      pr(solution,ori)
    solution = t(solution)
  