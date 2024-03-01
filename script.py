import urllib.request
from functools import cache

s1 = 'https://www.griddlers.net/nonogram/-/g/t1709243262226/i01?p_p_lifecycle=2&p_p_resource_id=griddlerPuzzle&p_p_cacheability=cacheLevelPage&_gpuzzles_WAR_puzzles_id='
s2 = '&_gpuzzles_WAR_puzzles_lite=false&_gpuzzles_WAR_puzzles_name=touchScreen'
id0 = 241934
id0 = 252952
link = s1 + str(id0) + s2
s = str(urllib.request.urlopen(link).read()).split('\\n')

inp_v = inp_h = 0
exec('inp_v = [' + s[66].strip('\\t') + ']')
exec('inp_h = [' + s[69].strip('  ').strip('\\t') + ']')

inp_v = [[i[1] for i in j] for j in inp_v]
inp_h = [[i[1] for i in j] for j in inp_h]

x = len(inp_v)
y = len(inp_h)

@cache
def generate(n, blocks, start=False):
  if len(blocks) == 0:
    return [[0]*n]
  l = []
  nblocks = len(blocks)
  max_shift = n - sum(blocks) - nblocks + 1
  if start:
    i0 = 0
  else:
    i0 = 1
  for i in range(i0,max_shift+1):
    l += [[0]*i + [1]*blocks[0] + j for j in generate(n-i-blocks[0],blocks[1:])]
  return l

pos = {'h':{},'v':{}}
for i in range(x):
  print("x",i/x)
  pos['v'][i] = generate(y, tuple(inp_v[i]), True)
for i in range(y):
  print("y",i/y)
  pos['h'][i] = generate(x, tuple(inp_h[i]), True)

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
  