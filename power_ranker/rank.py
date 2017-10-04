import numpy as np

class TeamRank:
  '''Store all ranks for a team'''
  def __init__(self):
    self.lsq     = 1.
    self.dom     = 1.
    self.col     = 1.
    self.sos     = 1.
    self.luck    = 1.
    self.cons    = 1.
    self.power   = 1.
    self.tier    = 1.
    self.overall = 1.
    self.prev    = 1.
    self.prev_overall = 1.
  def __repr__(self):
    print('         LSQ : %.3f'%self.lsq)
    print('         2SD : %.3f'%self.dom)
    print('      Colley : %.3f'%self.col)
    print('         SOS : %.3f'%self.sos)
    print('        Luck : %.3f'%self.luck)
    print(' Consistency : %.3f'%self.cons)
    print('       Power : %.3f'%self.power)
    print('        Tier : %.3f'%self.tier)
    print('     Overall : %.3f'%self.overall)
    print('    Previous : %.3f'%self.prev)
    print('Prev Overall : %.3f'%self.prev_overall)

def get_mu(teams, ranking):
  '''Get the league average ranking value
     for specified ranking'''
  return sum(getattr(t.rank,ranking) for t in teams)/float(len(teams))

def get_sigma(teams, ranking):
  '''Get the league std. dev for specified ranking'''
  ranks = [getattr(t.rank, ranking) for t in teams]
  return np.std(ranks)

def get_zscore(rank, mu, sigma):
  '''Return the z score given population mu and sigma
     for provided team rank'''
  return (float(rank)-float(mu)) / float(sigma)

def get_max_rank(teams, ranking):
  '''Get the max league ranking value
    for specified ranking'''
  return max(getattr(t.rank,ranking) for t in teams)

def get_min_rank(teams, ranking):
  '''Get the min league ranking value'''
  return min(getattr(t.rank,ranking) for t in teams)

def get_iqr(teams, ranking):
  '''Get the Interquartile range'''
  ranks = [getattr(t.rank, ranking) for t in teams]
  q75, q25 = np.percentile(ranks, [75, 25])
  return float(q75) - float(q25)

def norm_by_zscore(teams, ranking):
  '''Normalize the rank by it's z-score
   Has mean of 0.5, stdev  of 0.33'''
  mu = get_mu(teams, ranking)
  sigma = get_sigma(teams, ranking)
  for t in teams:
    z_score = get_zscore( getattr(t.rank, ranking), mu, sigma)
    setattr(t.rank, ranking, 0.5 + z_score/float(3) )

def norm_by_max(teams, ranking):
  '''Normalize league rankings by max score in league'''
  l_max = float(get_max_rank(teams, ranking))
  for t in teams:
    norm_rank = getattr(t.rank, ranking) *1./l_max
    setattr(t.rank, ranking, norm_rank)

def norm_rank(teams, ranking):
  '''Normalize the league ranks for 
    specified ranking by feature scaling
    Scales each ranking from 0.25 to ~1 where 
    0.25 (~1) corresponds to league min (max)
    Uses IQR instead of total range'''
  l_min = float(get_min_rank(teams, ranking))
  iqr = float(get_iqr(teams, ranking))
  for t in teams:
    old_val = getattr(t.rank, ranking)
    new_val = 0.25 + 0.375*(old_val - l_min)/float(iqr) if iqr != 0. else 0.25
    setattr(t.rank, ranking, new_val) 
