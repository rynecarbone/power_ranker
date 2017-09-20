import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from scipy.signal import argrelmin

#___________________________
def replace_opponents(teams):
  '''Replace team id number with team object'''
  for t in teams:
    for week, matchup in enumerate(t.schedule):
      for opponent in teams:
        if matchup == opponent.teamId:
          t.schedule[week] = opponent

#__________________
def calc_mov(teams):
  '''Calculate the margin of victory'''
  for t in teams:
    for week, opponent in enumerate(t.schedule):
      mov = t.scores[week] - opponent.scores[week]
      t.mov.append(mov)

#_________________________________
def calc_wins_losses(week, teams):
  '''Recalculates based on specified week:
        points for
        ponits against
        wins
        losses
        streak
        aggregate wins
        aggregate losses
        aggregate winning percentage'''
  for t in teams:
    aw_i   = 0. # aggregate wins
    al_i   = 0. # aggregate losses
    pf     = 0. # points for
    pa     = 0. # points against
    wins   = 0  
    losses = 0
    st     = 0  # streak
    st_sgn = 1  # sign of streak
    # Loop over weeks, retreive score and week's opponent
    for w, (s,w_o) in enumerate(zip(t.scores[:week],t.schedule[:week]) ):
      # points for, against, wins, losses, streak, sign
      pf += s
      pa += w_o.scores[w]
      # Score more than opponent 
      if s > w_o.scores[w]:
        wins += 1
        if st_sgn == -1:
          st_sgn = 1
          st = 1
        else:
          st += 1
      # Score less than opponent
      else:
        losses += 1
        if st_sgn == 1:
          st_sgn = -1
          st = 1
        else:
          st += 1
      # aggregate wins/losses
      for o in teams:
        if o.teamId != t.teamId:
          if s > o.scores[w]:
            aw_i += 1
          else:
            al_i += 1
    # Update aggregate win pct, agg. wins, agg. losses,
    # points for, points against, wins, losses, streak 
    t.awp            = float(aw_i)/(float(aw_i)+float(al_i))
    t.awins          = aw_i
    t.alosses        = al_i
    t.pointsFor      = pf
    t.pointsAgainst  = pa
    t.wins           = wins
    t.losses         = losses
    t.streak         = st
    t.streak_sgn     = st_sgn

#_________________________________________
def calc_sos(teams, week, rank_power=2.37):
  '''Calculates the strength of schedule, 
     based on the lsq rank'''
  # Find avg of opponent rankings
  for t in teams:
    rank_i = 0
    for w, o in enumerate(t.schedule[:week]):
      rank_i += o.lsq_rank**rank_power
    t.sos = rank_i/float(week)
  # Find avg sos in league
  sos_list = [x.sos for x in teams]
  avg_sos = sum(sos_list)/float(len(sos_list))
  # Normalize so average sos is 1
  for t in teams:
    t.sos = np.sqrt(t.sos * 1./avg_sos)

#_________________________________________
def calc_luck(teams, week, awp_weight=0.5):
  '''Calcualtes the luck index, considers:
    - Aggregate winning pct vs actual winning pct
    - Opponents score against you, vs their average score'''
  avg_score_weight = 1 - awp_weight # weight in the luck index
  for t in teams:
    # Calculate the ratio of opponents average score, 
    # over their week score
    o_avg_over_score = 0.
    for w, o in enumerate(t.schedule[:week]):
      o_avg = sum(o.scores[:week])/float(week)
      ratio = o_avg/float(o.scores[w])
      o_avg_over_score += ratio
    # Normalize to numer of weeks
    o_avg_over_score /= float(week)
    # Calculate ratio of your win pct to awg, pad
    # with 0.01 in num and denom to protect against shitty teams
    # with divide by 0
    win_pct = float(t.wins)/float(t.wins+t.losses)
    wpct_over_awp = (0.01 + float(win_pct) )/(0.01 + float(t.awp) )
    # Calculate luck index
    luck_ind = o_avg_over_score*avg_score_weight + wpct_over_awp*awp_weight
    t.luck = luck_ind

#__________________________________________________________________________
def calc_power(teams, week, w_dom=0.21, w_lsq=0.18, w_col=0.18, w_awp=0.15, 
               w_sos=0.10, w_luck=0.08, w_cons=0.05, w_strk=0.05):
  '''Calculates the final power rankings based on input metrics'''
  for t in teams:
    dom  = float(t.dom_rank)
    lsq  = float(t.lsq_rank)
    col  = float(t.colley_rank)
    awp  = float(t.awp)
    sos  = float(t.sos)
    luck = 1./float(t.luck)
    strk = float(t.streak) * int(t.streak_sgn)
    avg_score = sum(t.scores[:week]) / float(week)
    t_min     = float(min(t.scores[:week]))
    t_max     = float(max(t.scores[:week]))
    min_max   = 0.5*t_min + 0.5*t_max
    # Only count streaks longer than one game
    strk = 0.25*strk if strk > 1. else 0.
    cons = min_max/float(avg_score) # consistency metric
    # Weigh metrics according to the weights
    power = ( dom*w_dom + lsq*w_lsq + col*w_col + awp*w_awp + sos*w_sos +
              luck*w_luck + cons*w_cons + strk*w_strk )
    # Normalize with hyperbolic tangent #FIXME should this be configurable too?
    t.power_rank = 100*np.tanh(power/0.5)

#________________________________________________________
def calc_tiers(teams, year, week, bw=0.09, order=4, show=False):
  '''Calculate 3-5 tiers using Gaussian Kernal Density'''
  # Store rankings in list
  ranks = [t.power_rank for t in teams]
  # Calculate the Kernal Density Estimation
  kde = gaussian_kde(ranks, bw_method=bw)
  # Make plot
  x_grid = np.linspace(min(ranks)-10., max(ranks)+10., len(ranks)*10)
  f2 = plt.figure(figsize=(10,6))
  plt.plot(x_grid, kde(x_grid))
  if show: plt.show()
  # Create directory if it doesn't exist to save plot
  out_name = 'output/%s/week%s/tiers.png'%(year, week)
  os.makedirs(os.path.dirname(out_name), exist_ok=True)
  f2.savefig(out_name)
  plt.close()
  # Find minima to define tiers, separted by at least +/- order
  minima = x_grid[ argrelmin( kde(x_grid), order=order)[0] ]
  s_min = sorted(minima, reverse=True)
  tier = 1
  # Build tiers from minima
  for t in teams:
    # lowest tier
    if tier > len(s_min):
      tier += 0
    # if rank below current minima, create new tier
    elif t.power_rank < s_min[tier-1]:
      if tier < 5: tier += 1
    # Save tier
    t.tier =  tier

#________________________________________
def save_ranks(teams, year, week, getPrev=True):
  '''Save the power rankings to a file, 
    optionally retreive previous week's rankings'''
  # Save power rankings (teamId:rank)
  new_name = 'output/%s/week%s/ranks_power.txt'%(year, week)
  os.makedirs(os.path.dirname(new_name), exist_ok=True)
  f_new = open(new_name, 'w')
  # Write to file (teams should be passed sorted by ranking)
  for i, t in enumerate(teams):
    f_new.write('%s:%s\n'%(t.teamId, i+1))
  f_new.close()
  # Save ESPN overall rankings teamId:rank
  teams_sorted_overall = sorted(teams, key=lambda x: (x.wins, x.pointsFor), reverse=True)
  new_name = 'output/%s/week%s/ranks_overall.txt'%(year, week)
  os.makedirs(os.path.dirname(new_name), exist_ok=True)
  f_new = open(new_name, 'w')
  # Write to file (sorted by ESPN rankings)
  for i, t in enumerate(teams_sorted_overall):
    f_new.write('%s:%s\n'%(t.teamId, i+1))
    t.rank_overall = i+1
  f_new.close()
  # Exit if not comparing to previous rankings
  if not getPrev: 
    return
  # Get prevoius power rankings
  old_name = 'output/%s/week%s/ranks_power.txt'%(year, week-1)
  os.makedirs(os.path.dirname(old_name), exist_ok=True)
  f_old = open(old_name, 'r')
  for line in f_old:
    team_rank = (line.strip()).split(':')
    t_id = team_rank[0]
    t_rk = team_rank[1]
    # Sorted by this weeks power rankings
    for t in teams:
      if int(t.teamId) == int(t_id):
        t.prev_rank = t_rk
  f_old.close()
  # Get Previous overall rankings
  old_name = 'output/%s/week%s/ranks_overall.txt'%(year, week-1)
  os.makedirs(os.path.dirname(old_name), exist_ok=True)
  f_old = open(old_name, 'r')
  for line in f_old:
    team_rank = (line.strip()).split(':')
    t_id = team_rank[0]
    t_rk = team_rank[1]
    # sorted by this week overall
    for t in teams_sorted_overall:
      if int(t.teamId) == int(t_id):
        t.prev_rank_overall = t_rk
  f_old.close()
