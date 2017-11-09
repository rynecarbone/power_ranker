import os
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter
import numpy as np
from scipy.stats import norm

#_____________________________
def calc_playoffs(teams, year, week, settings, n_sims=1000000):
  '''Calculates playoff odds for each team
     Change reg_season to number of weeks
     Change spots to number of spots available (1 division)'''
  
  # See how many teams left:
  reg_season = settings.reg_season_count
  spots      = settings.playoff_team_count
  divisions  = len(settings.divisions)

  # Sort teams by current standings
  sorted_teams = sorted(teams, key=lambda x: (x.stats.wins, sum(x.stats.scores[:week])), reverse= True )
  for t in sorted_teams:
    # fit gaus to team scores
    t.stats.score_fit = norm.fit(t.stats.scores[:week]) 
  
  # Calculate the current standings
  _, __ = calc_standings(teams, divisions, spots, week, reg_season, print_current=True)
  # Calculate the expected number of wins for each team
  exp_wins = calc_exp_wins(teams, week, reg_season)
  # Simulate the rest of the season to find pct of times each team makes playoffs
  div, wc = simulate_season(teams, year, divisions, spots, week, reg_season, n_sims=n_sims)

  print('\nRest of Season Projections\n{:>20s}\tExp. Wins\tDiv. Winner (%)\tWild Card (%)\tMake Playoffs (%)'.format('Team'))
  for t in sorted_teams: 
    ew      = exp_wins[t.teamId - 1]
    d_wins  = 100.*div[t.teamId -1]
    wc_wins = 100.*wc[t.teamId -1]
    print('{:>20s}\t{:.3f}    \t{:.3f}         \t{:.3f}        \t{:.3f}'.format(t.owner, ew, d_wins, wc_wins, d_wins+wc_wins ) )
  return


#____________________________________________________________________
def simulate_season(teams, year, divisions, spots, week, reg_season, n_sims=1):
  '''Simulate the rest of the season'''
  
  # Keep track of how many times each team is division winner or wc
  div_tot = [0]*len(teams)
  wc_tot  = [0]*len(teams)

  div_tot_plot = np.zeros((len(teams),int(n_sims/1000)))
  wc_tot_plot = np.zeros((len(teams),int(n_sims/1000)))
  print('\nSimulating Rest of Season...')
  # Loop over number of simulated seasons
  for season in range(n_sims):
    if (season+1) % 1000 == 0:
      progress(season+1, n_sims, suffix='Complete')
      for i, (curr_d, curr_w) in enumerate(zip(div_tot, wc_tot)):
        div_tot_plot[i,int(season/1000)] = curr_d /(season+1)
        wc_tot_plot[i,int(season/1000)] = curr_w /(season+1)
    # need to erase number of wins added for each season sim   
    temp_wins = [0]*len(teams) # store num of wins by team Id
    
    # Loop over remaining games
    for i in range(reg_season-week):
      w = i + week # simulated week number
      simulated = [] # keep track of which games have already been simulated
      
      # Loop over teams in this week
      for t in teams:
        # Only simulate game and opponent if havent already done so
        if t.teamId not in simulated:
          # Generate random score from reg season score profile
          t.stats.scores[w] = np.random.normal(t.stats.score_fit[0], t.stats.score_fit[1],1)[0]
          simulated.append(t.teamId) # already simulated this game
          # simulate opponent
          for op in teams:
            if op.teamId == t.stats.schedule[w].teamId:
              # Generate random score from reg season score profile
              op.stats.scores[w] = np.random.normal(op.stats.score_fit[0], op.stats.score_fit[1],1)[0]
              simulated.append(op.teamId) # already simulated this game
              
              # Figure out who won this week
              if t.stats.scores[w] > op.stats.scores[w]:
                t.stats.wins += 1
                temp_wins[t.teamId-1] += 1
              else:
                op.stats.wins += 1
                temp_wins[op.teamId-1] += 1
    
    # Finished simulating the season
    div, wc = calc_standings(teams, divisions, spots, reg_season, reg_season, print_current=False)
    div_tot[:] = [sum(x) for x in zip(div_tot, div)]
    wc_tot[:]  = [sum(x) for x in zip(wc_tot, wc)]
    # Reset wins for remaining part of season
    for t in  sorted(teams, key=lambda x: (x.stats.wins, sum(x.stats.scores[:])), reverse= True ):
      t.stats.wins -= temp_wins[t.teamId-1]
  # Normalize by number of simulations
  div_tot[:] = [ x/float(n_sims) for x in div_tot]
  wc_tot[:]  = [ x/float(n_sims) for x in wc_tot]
  d_order = sorted(range(len(div_tot)), key=lambda k: div_tot[k], reverse=True)
  w_order = sorted(range(len(wc_tot)), key=lambda k: wc_tot[k], reverse=True)

  # Plot the pct as funciton of simulation
  plt.figure(1)
  ax1 = plt.subplot(211, xlabel='Simulation / 1000', ylabel='Win Division %', yscale='logit')
  xx = [x for x in range(int(n_sims/1000.))]
  # Make division subplot
  for i in d_order:
    owner = ''
    for t in teams:
      if t.teamId == i+1:
        owner = t.owner.split(' ')[0]
    plt.plot(xx, div_tot_plot[i,:], label=owner)
  box1 = ax1.get_position()
  ax1.set_position([box1.x0, box1.y0, box1.width*0.87, box1.height])
  #plt.gca().yaxis.set_minor_formatter(NullFormatter())
  ax1.yaxis.set_minor_formatter(NullFormatter())
  ax1.legend(bbox_to_anchor=(1.01,1), loc=2, ncol=1,borderaxespad=0., prop={'size':10})
  # Make WC subplot
  ax2 = plt.subplot(212, xlabel = 'Simulation / 1000', ylabel='Wild Card %', yscale='logit')
  for i in w_order:
    owner = ''
    for t in teams:
      if t.teamId == i+1:
        owner = t.owner.split(' ')[0]
    plt.plot(xx, wc_tot_plot[i,:], label=owner)
  box2 = ax2.get_position()
  ax2.set_position([box2.x0, box2.y0, box2.width*0.87, box2.height])
  ax2.legend(bbox_to_anchor=(1.01,1), loc=2, ncol=1,borderaxespad=0.,prop={'size':10})
  ax2.yaxis.set_minor_formatter(NullFormatter())
  out_dir = 'output/%s/week%s/playoff_odds.png'%(year,week)
  os.makedirs(os.path.dirname(out_dir), exist_ok=True)
  plt.savefig(out_dir)

  return div_tot, wc_tot


#_____________________________________________________________________
def calc_standings(teams, divisions, spots, week, reg_season, print_current=False):
  '''Calculate the current playoff standings
     Division winners make it, then enough playoff teams to fill wildcard
     Return two lists, of length number of teams
       index for (teamId-1) = 1 if team in list:
       ex: division_winners = [0,1,0,...,0,1,0,...,0]'''
  
  division_winners = []
  wildcards        = []
  ret_div          = [0]*len(teams)
  ret_wc           = [0]*len(teams)
  eliminated       = []

  # Find division winners first
  for d in range(divisions):
    sorted_teams = sorted(teams, key=lambda x: (x.divisionId == d, x.stats.wins, sum(x.stats.scores[:week])), reverse= True )
    division_winners.append(sorted_teams[0])
    ret_div[sorted_teams[0].teamId-1]=1
  
  # Sort by record, then points for
  sorted_teams = sorted(teams, key=lambda x: (x.stats.wins, sum(x.stats.scores[:week])), reverse= True )
  for t in sorted_teams:
    if t not in division_winners and spots - len(wildcards) - divisions > 0:
      wildcards.append(t)
      ret_wc[t.teamId-1] = 1
  # No need to compute eliminated teams and print results
  if not print_current:
    return ret_div, ret_wc

  # Find eliminated teams
  last_wc = wildcards[-1]
  for t in sorted_teams:
    if t not in division_winners and t not in wildcards and last_wc.stats.wins - t.stats.wins > (reg_season-week):
      eliminated.append(t)
  
  # Print the results
  print('\nCurrent Playoff Seeding')
  for i,t in enumerate(division_winners):
    print('{}) {:20s}Div Winner ({})'.format(i, t.owner, t.divisionName))
  for j,t in enumerate(wildcards):  
    print('{}) {:20s} '.format(j+divisions, t.owner))
  # Print who is mathematically eliminated
  if len(eliminated) > 0 : 
    print('\nEliminated:')
    for e in eliminated:
      print('{}'.format(e.owner))
  return ret_div, ret_wc


#______________________________________________
def calc_exp_wins(teams, week, reg_season):
  '''Create matrix where rows are teams i, 
     and columns are opponents j for each team i in rest of season'''
  # Store prob for each team to win remaining games, using gaussian mixture
  odds_matrix = np.zeros((len(teams), reg_season-week))
  sorted_teams = sorted(teams, key=lambda x: x.teamId, reverse= False )
  ret_wins = [0]*len(teams)
  # Loop over teams for each row
  for i,t in enumerate(sorted_teams):
    # Loop over weeks left in the season
    for j in range(reg_season-week):
      w = j+week
      op_id  = t.stats.schedule[w].teamId
      # Find opponent for team i in week j
      for op in sorted_teams:
        if op.teamId == op_id:
          # Extract team and opponent point dist parameters
          t_mu, t_std = t.stats.score_fit
          op_mu, op_std = op.stats.score_fit
          # Define new gaussian variable as diff of these two point dist
          Z = norm( t_mu-op_mu, np.sqrt(t_std**2 + op_std**2) )
          # Prob( t > op ) <=> Prob (Z > 0) == 1- Z.cdf(0)
          odds_matrix[i,j] = 1.-Z.cdf(0)
  # Expected number of wins is sum of prob of winning rest of games
  exp_wins = np.sum(odds_matrix, axis=1)
  # Return list of expected number of wins, by teamId index
  for ew,t in zip(exp_wins, sorted_teams):
    ret_wins[t.teamId-1] = ew
  return ret_wins

def progress(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='='):
  '''
  iteration: current iteration
  tot: total iterations
  prefix: prefix string
  suffix: suffix string
  decimals: positive number of decimals in percent complete
  length: character length of bar
  fill: bar fill character
  '''
  prefix = 'Season {:7d}/{:7d}'.format(iteration, total)
  percent = ('{0:.'+str(decimals)+'f}').format(100.*(iteration/float(total)))
  filledLength = int(length*iteration // total)
  bar = fill*filledLength + '>'+'-' *(length -filledLength-1)
  print('\r%s |%s| %s%% %s'%(prefix, bar, percent, suffix), end='\r')
  if iteration == total:
    print() # new line on complete

