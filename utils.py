import matplotlib.pyplot as plt 
import matplotlib.colors
import numpy as np

def totuple(x):
  return tuple(tuple(i) for i in x)

def hex2rgb(hx):
  return tuple(int(hx[i:i+2], 16)/256 for i in (0, 2, 4))

def nice_number(n):
  x = 6
  s = ' '*(x*3-len(str(n))) + str(n)
  s2 = '.'.join([s[3*i:3*i+3] for i in range(x)])
  return s2

def msg(ori, line, n, status, nold = None, verbose=True):
  if not verbose:
    return
  if type(status) is str:
    s3 = status
  elif status:
    s3 = 'Generated '
  else:
    s3 = 'Counted   '
  if n == 1:
    s3 = 'Finished  '
  line = '0'*(3-len(str(line))) + str(line)
  s2 = nice_number(n)
  
  if type(status) is str and status == 'Reduced to':
    if n == nold:
      s3 = 'Same at   '
    else:
      s2 += ' from ' + nice_number(nold)

  print("O"+str(ori)+"L"+str(line),s3,s2)

def create_data_from_color_possible(color_possible):
  x, y, _ = color_possible.shape
  data = -1 * np.ones((x, y), dtype=int)
  for i in range(x):
    for j in range(y):
      if sum(color_possible[i,j,:]) == 1:
        data[i,j] = np.where(color_possible[i,j,:])[0][0]
      else:
        data[i,j] = -1
  return data
  
def plot(title, iteration, color_possible, colors, ori):
  
  plt.clf()      
  
  data = create_data_from_color_possible(color_possible)
  
  if ori == 1:    
    data = np.transpose(data, axes=(1,0,2))
    
  colors = ['808080'] + colors
  cmap = [hex2rgb(i) for i in colors]
  cmap = matplotlib.colors.ListedColormap(cmap)

  plt.imshow(data, interpolation='nearest', cmap = cmap,  vmin=-1, vmax=len(colors)-1)
  plt.gca().get_xaxis().set_visible(False)
  plt.gca().get_yaxis().set_visible(False)
  plt.title(title+" - "+str(iteration))
  plt.draw()
  plt.pause(0.001)  # Brief pause to update the display
