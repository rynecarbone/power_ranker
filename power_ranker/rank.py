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

def get_avg_rank(teams, ranking):
  '''Get the league average ranking value
     for specified ranking'''
  return sum(getattr(t.rank,ranking) for t in teams)/float(len(teams))

def get_max_rank(teams, ranking):
  '''Get the max league ranking value
    for specified ranking'''
  return max(getattr(t.rank,ranking) for t in teams)

def get_min_rank(teams, ranking):
  '''Get the min league ranking value'''
  return min(getattr(t.rank,ranking) for t in teams)

def norm_rank(teams, ranking):
  '''Normalize the league ranks for 
    specified ranking by feature scaling
    Scales each ranking from 0 to 1 where 
    0 (1) corresponds to league min (max)'''
  l_max = float(get_max_rank(teams, ranking))
  l_min = float(get_min_rank(teams, ranking))
  if l_max == l_min: return
  for t in teams:
    old_val = float(getattr(t.rank,ranking))
    new_val = (old_val - l_min)/(l_max - l_min)
    setattr(t.rank, ranking, new_val) 
