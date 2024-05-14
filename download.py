import urllib.request
import os.path

def get_id(inp):  
  example = inp["example"]
  if   example == 1: # Owl                       30 x 35 x 2
    id0 = 241934     
  elif example == 2: # Dog                       40 x 45 x 2
    id0 = 252952    
  elif example == 3: # Maple leaf                30 x 30 x 2
    id0 = 202358     
  elif example == 4: # Beautiful eye             35 x 25 x 7
    id0 = 39756     
  elif example == 5: # Flamingo                  13 x 20 x 4
    id0 = 275510
  elif example == 6: # Rosebud                   27 x 45 x 8
    id0 = 236744
  elif example == 7: # Santorini                 40 x 50 x 8
    id0 = 233499    
  elif example == 8: # Lion                      45 x 45 x 2
    id0 = 88712
  elif example == 9: # Family in the Summer Heat 50 x 50 x 6 - NOT SOLVED
    id0 = 118315
  return id0

def get_title(id0):
  link = 'https://www.griddlers.net/nonogram/-/g/' + str(id0)
  try:
    s = str(urllib.request.urlopen(link).read())
    s2 = "Griddlers puzzle " + str(id0) + " - "
    idx = s.find(s2)
    idx1 = idx + len(s2)
    idx2 = idx + len(s2) + 50
    s3 = s[idx1:idx2]
    idx3 = s3.find('"')
    title = s3[:idx3]
  except:
    title = ''
  return title

def get_desc(id0, x, y, n_colors):
  return "{ttl} {x} x {y} x {n_colors}\n{id0}".format(ttl=get_title(id0),x=x,y=y,n_colors=n_colors,id0=id0)
      
def download_and_write_file(id0):
  s1 = 'https://www.griddlers.net/nonogram/-/g/t1709243262226/i01?p_p_lifecycle=2&p_p_resource_id=griddlerPuzzle&p_p_cacheability=cacheLevelPage&_gpuzzles_WAR_puzzles_id='
  s2 = '&_gpuzzles_WAR_puzzles_lite=false&_gpuzzles_WAR_puzzles_name=touchScreen'
  link = s1 + str(id0) + s2
  s = str(urllib.request.urlopen(link).read())
  f = open(str(id0),'w')
  f.write(s)
  f.close()
  
def get_input(inp):
  id0 = get_id(inp)
  fname = str(id0)
  if not os.path.isfile(fname):
    download_and_write_file(id0)
  
  s = open(fname, 'r').read().split('\\n')
    
  inp_v = eval('[' + s[66].strip('\\t') + ']')
  inp_h = eval('[' + s[69].strip('  ').strip('\\t') + ']')
  used_colors = eval('[' + s[63].strip('  ').strip('\\t') + ']')
  colors = eval('[' + s[57].strip('  ').strip('\\t') + ']')
  colors = [colors[i] for i in used_colors]
  
  status = {}
  status[0] = { idx: {"block_colors":[i[0]-1 for i in j], "block_lengths":[i[1] for i in j]} for idx, j in enumerate(inp_v)}
  status[1] = { idx: {"block_colors":[i[0]-1 for i in j], "block_lengths":[i[1] for i in j]} for idx, j in enumerate(inp_h)}
  
  x = len(inp_v)
  y = len(inp_h)
  n_colors= len(colors)
  
  inp["id0"] = id0
  inp["desc"] = get_desc(id0, x, y, n_colors)
  inp["status"] = status
  inp["colors"] = colors
  inp["n_colors"] = len(colors)
  inp["x"] = x
  inp["y"] = y
  
  return inp