import os
import numpy as np
from matplotlib import pylab as pl

class Radar(object):
  '''Creates a radar plot for each team '''
  def __init__(self, fig, titles, labels, rect=None):
    if rect is None:
      rect = [0.05, 0.05, 0.85, 0.85]
    self.n = len(titles)
    self.angles = [a if a <=360. else a - 360. for a in np.arange(90, 90+360, 360.0/self.n)]
    self.axes = [fig.add_axes(rect, projection="polar", label="axes%d" % i) 
                     for i in range(self.n)]
    self.ax = self.axes[0]
    self.ax.set_thetagrids(self.angles, labels=titles, fontsize=12, weight='bold')
    for ax in self.axes[1:]:
      ax.patch.set_visible(False)
      ax.grid("off")
      ax.xaxis.set_visible(False)
    for ax, angle, label in zip(self.axes, self.angles, labels):
      ax.set_rgrids(range(1, 6), angle=angle, labels=label)
      ax.spines["polar"].set_visible(False)
      ax.set_ylim(0, 5)
  
  def plot(self, values, *args, **kw):
    '''plots the data'''
    angle = np.deg2rad(np.r_[self.angles, self.angles[0]])
    values = np.r_[values, values[0]]
    self.ax.plot(angle, values, *args, **kw)
    self.ax.fill(angle,values,*args,**kw)


#____________________________
def make_radar( team, year, week, Y_LOW=[0,0,.4,50,-60,-5], Y_HIGH=[1,1,1.4,150,40,5] ):
  '''Makes radar plots and saves them to folder
     y_low is list of minimum y values (win pct, awp, sos, ppg, mov, streak)
     y_high is list of maximum y values (win pct, awp, sos, ppg, mov, streak)'''
  fig = pl.figure(figsize=(6,6))

  titles = [ 'Win Pct',
             'AWP',
             'SOS',
             'PPG',
             'MOV',
             'Streak' ]
  Y_LOW2 = [ 0.2*(h-l)+l for (l,h) in zip(Y_LOW, Y_HIGH) ]
  labels = [ np.linspace(Y_LOW2[0], Y_HIGH[0], num=5),
             np.linspace(Y_LOW2[1], Y_HIGH[1], num=5),
             np.linspace(Y_LOW2[2], Y_HIGH[2], num=5),
             np.linspace(Y_LOW2[3], Y_HIGH[3], num=5),
             np.linspace(Y_LOW2[4] ,Y_HIGH[4], num=5),
             np.linspace(Y_LOW2[5], Y_HIGH[5], num=5)
            ]
  scale = [ 5./(Y_HIGH[x]-Y_LOW[x]) for x in range(6) ]
  offset = [ (0 - Y_LOW[x]) for x in range(6) ]

  t_ranks = [ float(team.stats.wins)/float(team.stats.wins + team.stats.losses),
              float(team.stats.awp),
              float(team.rank.sos),
              float(team.stats.pointsFor)/week,
              sum(team.stats.mov)/float(week),
              int(team.stats.streak) * int(team.stats.streak_sgn) ]
  t_ranks_norm = [(t_ranks[x]+offset[x])*scale[x] for x in range(6) ]

  radar = Radar(fig, titles, labels)
  radar.plot( t_ranks_norm , "-", lw=2, color="g", alpha=0.4,label=team.teamName)

  fig.set_size_inches(6,6, forward=True)
  out_dir = 'output/%s/week%s/radar_plots/radar_%s.png'%(year, week,team.teamId)
  os.makedirs(os.path.dirname(out_dir), exist_ok=True)
  fig.savefig(out_dir)
