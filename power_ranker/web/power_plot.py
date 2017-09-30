import matplotlib.pyplot as plt
import numpy as np

#_____________________________________
def make_power_plot(teams, year, week):
  '''Make plot of power ranking versus
    average score'''
  scores = []
  owners = []
  powers = []
  colors = []
  # Tier colors
  c = [(133/255.,205/255.,242/255.),
       (122/255.,201/255.,96/255.),
       (224/255.,183/255.,0/255.),
       (255/255.,106/255.,43/255.),
       (168/255.,106/255.,156/255.)]
  tiers = [1,2,3,4,5]   
  my_dpi = 96  
  minx=200
  maxx=0
  # Save scores, tiers, names
  for t in teams:
    t_scores = []
    for s in t.stats.scores[:week]:
      t_scores.append(s)
    scores.append(t_scores)
    owners.append(t.owner.split()[0].title())
    powers.append(float(t.rank.power))
    colors.append(c[t.rank.tier-1])
    t_min = min(t_scores)
    t_max = max(t_scores)
    if t_min < minx:
      minx = t_min
    if t_max > maxx:
      maxx = t_max
  # Set up plot
  f = plt.figure()
  f.set_size_inches(992./my_dpi,558./my_dpi)
  ax = f.add_subplot(111)
  ax.set_xlim(minx-10, maxx+30)
  plt.xlabel('Weekly Score')
  plt.ylabel('Power Rank')
  
  # create list of boxplots for each player 
  bp_dict = plt.boxplot(scores, vert=False, showfliers=False, showmeans=False, showcaps=False)
  
  # change color
  for i,w in enumerate(bp_dict['whiskers']):
    j= int(i/2) if i%2 else int((i+1)/2)
    w.set(color=colors[j],linestyle="solid")
  for i,b in enumerate(bp_dict['boxes']):
    b.set(color=colors[i])
  
  # show each score as red dot
  for i in range(len(teams)):
    x = scores[i]
    y = np.random.normal(i+1, 0.04, size=len(x))
    ax.plot(x, y, 'r.', alpha=0.4)
 
  # put name to left of boxplot
  for i,line in enumerate(bp_dict['whiskers']):
    x, y = line.get_xydata()[1] # bottom of line (1 is top)
    if(i%2):
      ax.text(x+5,y, '%s'%owners[int(i/2)], horizontalalignment='left', verticalalignment='center')
  
  # Add a legend
  ax.legend(loc=2,title='Tier',labels=tiers)
  for i,leg_item in enumerate(ax.get_legend().legendHandles):
    leg_item.set_color(c[i])
  plt.ylim(len(teams)+1,0)
  f.savefig('output/%s/week%d/power_plot.png'%(year, week),dpi=my_dpi*2,bbox_inches='tight')

