class TeamStats:
  '''Keep track of team stats'''
  def __init__(self, data):
    self.faab          = data['teamTransactions']['acquisitionBudgetSpent']
    self.trans         = data['teamTransactions']['overallAcquisitionTotal']
    self.trades        = data['teamTransactions']['trades']
    self.waiver        = data['waiverRank']
    self.wins          = 0.
    self.losses        = 0.
    self.streak        = 0.
    self.streak_sgn    = 1.
    self.pointsFor     = 0.
    self.pointsAgainst = 0.
    self.schedule      = []
    self.home_away     = [] # 0: home 1: away 
    self.scores        = []
    self.mov           = []
    self.awp           = 0.
    self.awins         = 0.
    self.alosses       = 0.
  def __repr__(self):
    print('             FAAB : %s'%self.faab) 
    print('     Transactions : %s'%self.trans) 
    print('           Trades : %s'%self.trades) 
    print('           Waiver : %s'%self.wavier) 
    print('             Wins : %s'%self.wins) 
    print('           Losses : %s'%self.losses) 
    print('           Streak : %s'%self.streak) 
    print('      Streak Sign : %s'%self.streak_sgn) 
    print('       Points For : %s'%self.pointsFor) 
    print('   Points Against : %s'%self.pointsAgainst) 
    print('         Schedule : %s'%self.schedule) 
    print('Home (0) Away (1) : %s'%self.home_away) 
    print('           Scores : %s'%self.scores) 
    print('Margin of Victory : %s'%self.mov) 
    print('   Aggregate wpct : %s'%self.awp) 
    print('   Aggregate wins : %s'%self.awins) 
    print(' Aggregate losses : %s'%self.alosses)
  def _replace_opponents(self, teams):
    '''Replace team id number with team object'''
    for week, matchup in enumerate(self.schedule):
      for opponent in teams:
        if matchup == opponent.teamId:
          self.schedule[week] = opponent
  def _calc_mov(self):
    '''Calculate the margin of victory'''
    for week, opponent in enumerate(self.schedule):
      mov = self.scores[week] - opponent.stats.scores[week]
      self.mov.append(mov)
  def _calc_wins_losses(self,teamId, week, teams):
    '''Recalculates based on specified week:
       points for, ponits against
       wins, losses, streak
       aggregate wins, aggregate losses,
       aggregate wpct'''
    self.awins      = 0. # aggregate wins
    self.alosses    = 0. # aggregate losses
    self.pointsFor  = 0. # points for
    self.pointsAgainst = 0. # points against
    self.wins       = 0
    self.losses     = 0
    self.streak     = 0  # streak
    self.streak_sgn = 1  # sign of streak
    # Loop over weeks, retreive score and week's opponent
    for w, (s, w_o) in enumerate(zip(self.scores[:week], self.schedule[:week])):
      # points for, against, wins, losses, streak, sign
      self.pointsFor += s
      self.pointsAgainst += w_o.stats.scores[w]
      # Score more than opponent
      if s > w_o.stats.scores[w]:
        self.wins += 1
        if self.streak_sgn == -1:
          self.streak_sgn = 1
          self.streak = 1
        else: self.streak += 1
      # Score less than opponent
      else:
        self.losses += 1
        if self.streak_sgn == 1:
          self.streak_sgn = -1
          self.streak = 1
        else: self.streak += 1
      # aggregate wins/losses
      for o in teams:
        if o.teamId != teamId:
          if s > o.stats.scores[w]:
            self.awins += 1
          else:
            self.alosses += 1
    # Update aggregate win pct
    self.awp = float(self.awins)/(float(self.awins)+float(self.alosses))
