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
  else:
    id0 = example # Assume that the user provided a direct id
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
  fname = os.path.join('raw_format', str(id0))
  f = open(fname,'w')
  f.write(s)
  f.close()

def parse_raw_file(id0):
  """Parse raw puzzle file and return components"""
  fname = os.path.join('raw_format', str(id0))
  
  with open(fname, 'r') as f:
    s = f.read().split('\\n')
    
  inp_v = eval('[' + s[66].strip('\\t') + ']')
  inp_h = eval('[' + s[69].strip('  ').strip('\\t') + ']')
  used_colors = eval('[' + s[63].strip('  ').strip('\\t') + ']')
  colors = eval('[' + s[57].strip('  ').strip('\\t') + ']')
  colors = [colors[i] for i in used_colors]
  
  return inp_v, inp_h, colors
  
  return inp