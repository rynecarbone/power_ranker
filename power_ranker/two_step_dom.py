import numpy as np

class TwoStepDom(object):
  '''Class to get the two step dominance matrix and rankings'''
  
  def __init__(self, N_teams, week, sq_weight=0.25, decay_penalty=0.5):
    self.w_sq       = sq_weight
    self.w_l        = 1. - sq_weight
    self.win_matrix = np.zeros(shape=(N_teams,N_teams))
    self.week       = week
    self.dp         = decay_penalty

  def _calc_win_matrix(self, teams):
    '''Calculate the win matrix for specified week'''
    # Loop over the teams to find the wins versus other opponents
    for t_index, t in enumerate(teams):
      # Loop over each week, retreive MOV and opponent instance
      for w, (mov, opponent) in enumerate(zip(t.stats.mov[:self.week], t.stats.schedule[:self.week])):
        o_index = int(opponent.teamId) - 1
        # Positive MOV is a win, weight older games less using decay penalty
        # Oldest game will be weighted by (1.0 - decay penalty). Nominal value is 0.5
        if mov > 0:
          self.win_matrix[t_index][o_index] += (1-self.dp) + (self.dp*w)/float(self.week)

  def _calc_two_step_dom(self, teams):
    '''Calculate the two step dominance matrix and save rankings'''
    # Square the win matirx, and apply weight
    m_sq = np.linalg.matrix_power(self.win_matrix, 2)
    m_sq *= self.w_sq
    # Weigh the linear dominance matrix
    m_lin = self.win_matrix * self.w_l
    # Get the 2SD matrix
    tsd_matrix = m_sq + m_lin
    # Calc the dominance rank by summing rows
    for row, t in zip(tsd_matrix, teams):
      t.rank.dom = sum(row)
    # Normalize avg dom rank to 1
    dom_list = [x.rank.dom for x in teams]
    avg_dom = float(sum(dom_list))/len(dom_list)
    for t in teams:
      t.rank.dom /= avg_dom

  def get_ranks(self, teams):
    '''Get the rankings for each team from two step dominance matrix'''
    self._calc_win_matrix(teams)
    self._calc_two_step_dom(teams)

