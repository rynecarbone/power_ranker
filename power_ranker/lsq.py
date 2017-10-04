import os
from scipy.optimize import lsq_linear
from matplotlib import pylab as pl
import numpy as np

class LSQ(object):
  '''Calculates the LSQ based rankings'''
  def __init__(self, year, week, B_w=30., B_r=35., dS_max=35., beta_w=2.2, show=False):
    self.year   = year
    self.week   = week
    self.B_w    = B_w   		
    self.B_r    = B_r   
    self.dS_max = dS_max
    self.beta_w = beta_w
    self.show   = show
  def _calc_Rg(self, S_h, S_a):
    '''Returns R_g given home and away scores'''
    dS_ha = float(S_h - S_a)
    #dS_t  = self.dS_max * np.tanh(dS_ha/(2.*self.dS_max)) #FIXME should 2 be configurable?   
    dS_t  = self.dS_max * np.tanh(dS_ha/(self.dS_max)) #FIXME should 2 be configurable?   
    S_w   = S_h if dS_ha > 0 else S_a
    p_m   = 1   if dS_ha > 0 else -1
    R_g   = p_m*self.B_w + dS_t + self.B_r*(dS_ha/S_w)
    return R_g
  def _calc_Ng_list(self, teams):
    '''Returns vector of games with home team id [0], away team id[1]
       home score [2] and away score [3]'''
    N_g = []
    for w in range(self.week):
      for t in teams:
        if t.stats.home_away[w] == 0:
          opp = t.stats.schedule[w]
          score = t.stats.scores[w]
          opp_score = opp.stats.scores[w]
          N_g.append([t.teamId, opp.teamId, score, opp_score])
    return N_g
  def _calc_sig_g(self, prev_rank, N_g):
    '''Returns Sigma_g for each game given previous iterations rankings'''
    alpha_w = (max(prev_rank) - min(prev_rank))/np.log(self.beta_w*self.beta_w)
    sig_g = []
    for i,g in enumerate(N_g):
      h_g = g[0]-1 # home teamId
      a_g = g[1]-1 # away teamId
      w_g = np.exp( -np.fabs(prev_rank[h_g]-prev_rank[a_g])/alpha_w )
      #gweek = -(-int(i+1)//int(nteams/2)) # integer division, rounds up so you get the week number of the game
      #w_g *= np.exp( - np.fabs(week - gweek)/float(1.2*week) )
      sig_g.append(1./np.sqrt(w_g))
    return sig_g

  def _rank_pass(self, teams, passN=0, prev_rank=[] ):
    '''Returns list of rankings  using linear chi2
    For pass 0, set passN = 0, all weights are 1
    For all others, set passN = n and send prev_rank '''
    A   = []  # g x t array (games x teams)
    b   = []  # g list of game results R_g
    N_g = self._calc_Ng_list(teams)  # list of games with home/away ids
    # error of game measurement w = 1/sig^2
    if passN == 0:
      sig_g = np.ones(len(N_g)) # equal weight first iteration
    else:
      sig_g = self._calc_sig_g(prev_rank, N_g)
    # Loop over games & home/away team ids
    for g, h_a in enumerate(N_g):
      row_g = [] # row for game g in A matrix
      # loop over teams 
      for team in teams:
        if team.teamId == h_a[0]:
          r_tg = 1./sig_g[g] # home team
        elif team.teamId == h_a[1]:
          r_tg = -1./sig_g[g] #away
        else:
          r_tg = 0 #not in game
        row_g.append(r_tg)
      # add row to A matrix
      R_g = self._calc_Rg(h_a[2], h_a[3]) # send( score_home, score_away)
      b.append(R_g/sig_g[g])
      A.append(row_g)
    # Calculate the ranks
    rank = lsq_linear(A, b, bounds=(30,130))#,lsq_solver='exact')
    if rank.success == False:
      print('WARNING:\t%s'%rank.message)
    for i,r in enumerate(rank.x):
      teams[i].rank.lsq = r
    return rank.x

  def _plot_save_rank(self, rank_p, teams):
    '''Plot the ranking iterations for each team'''
    # Plot iterations
    fig = pl.figure(figsize=(10,6))
    t_ranks = []
    x = np.linspace(0, len(rank_p)-1, len(rank_p))
    # Loop over iterations and save ranks for each team
    for t in range(len(teams)):
      temp =[]
      for p in rank_p:
        temp.append(p[t])
      t_ranks.append(temp)
      pl.plot(x,t_ranks[t])
    # Save plot
    if self.show == True:
      pl.show()
    # make dir if it doesn't exist already
    out_name = 'output/%s/week%s/lsq_iter_rankings.png'%(self.year, self.week)
    os.makedirs(os.path.dirname(out_name), exist_ok=True)
    fig.savefig(out_name)
    pl.close()
    # Average last 70 elements to get final rank
    for i,t in enumerate(t_ranks):
      mean = sum(t[70:])/float(len(t[70:]))
      teams[i].rank.lsq = np.tanh( mean/75.) # save the rank again (100 approximately is 1.)

  def get_ranks(self, teams):
    '''Main function to calculate and plot lsq ranking'''
    rank_p = [] # List of rankings for each pass
    # Pass 0 has weight = 1
    rank_p.append( self._rank_pass(teams, passN=0) )
    # Iterate with previous ranks as input, recalculate weight
    for p in range(1,100):
      rank_p.append( self._rank_pass(teams, passN=p, prev_rank=rank_p[p-1]))
    # plot result of iterations
    self._plot_save_rank(rank_p, teams)
