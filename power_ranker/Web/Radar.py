import os
import numpy as np
from matplotlib import pylab as pl

class Radar(object):
  '''Creates a radar plot for each team'''
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
def make_radar( team, week ):
  '''Makes radar plots and saves them to folder'''
  fig = pl.figure(figsize=(6,6))

  titles = [ 'Win Pct',
             'AWP',
             'SOS',
             'PPG',
             'MOV',
             'Streak' ]
  labels = [ np.linspace(0.2,1.,num=5),
             np.linspace(0.2,1.,num=5),
             np.linspace(.6,1.4,num=5),
             np.linspace(70,150,num=5),
             np.linspace(-40,40,num=5),
             np.linspace(-3,5,num=5)
            ]
  ymin = [ 0, 0,   .4,  50, -60, -5]
  ymax = [ 1, 1, 1.4, 150,  40,  5]
  scale = [ 5./(ymax[x]-ymin[x]) for x in range(6) ]
  offset = [ (0 - ymin[x]) for x in range(6) ]

  t_ranks = [ float(team.wins)/float(team.wins + team.losses),
              float(team.awp),
              float(team.sos),
              float(team.pointsFor)/week,
              sum(team.mov)/float(week),
              int(team.streak) * int(team.streak_sgn) ]
  t_ranks_norm = [(t_ranks[x]+offset[x])*scale[x] for x in range(6) ]

  radar = Radar(fig, titles, labels)
  radar.plot( t_ranks_norm , "-", lw=2, color="g", alpha=0.4,label=team.teamName)

  fig.set_size_inches(6,6, forward=True)
  out_dir = 'output/week%s/radar_plots/radar_%s.png'%(week,team.teamId)
  os.makedirs(os.path.dirname(out_dir), exist_ok=True)
  fig.savefig(out_dir)
