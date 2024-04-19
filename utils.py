import matplotlib.pyplot as plt 
import matplotlib.colors
import numpy as np

def totuple(x):
  return tuple(tuple(i) for i in x)

def hex2rgb(hx):
  return tuple(int(hx[i:i+2], 16)/256 for i in (0, 2, 4))

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
