#_________________
class Team(object):
  '''Team objects store attributes for each team in the league'''

  def __init__(self, data):
    self.teamId        = data['teamId']
    self.teamAbbrev    = data['teamAbbrev']
    self.teamName      = "%s %s"%(data['teamLocation'], data['teamNickname'])
    self.owner         = "%s %s"%(data['owners'][0]['firstName'].title(), 
                                  data['owners'][0]['lastName'].title())
    self.logoUrl       = data['owners'][0]['photoUrl'] if 'logoUrl' not in data.keys() else data['logoUrl']
    self.divisionId    = data['division']['divisionId']
    self.divisionName  = data['division']['divisionName']
    self.faab          = data['teamTransactions']['acquisitionBudgetSpent']
    self.trans         = data['teamTransactions']['overallAcquisitionTotal']
    self.trades        = data['teamTransactions']['trades']
    self.waiver        = data['waiverRank']
    self.wins          = data['record']['overallWins']   # recomputed later based on week
    self.losses        = data['record']['overallLosses'] # recomputed later based on week
    self.streak        = data['record']['streakLength']  # recomputed later based on week
    self.streak_sgn    = 1 if data['record']['streakType'] == 1  else -1
    self.pointsFor     = data['record']['pointsFor']     # recomputed later based on week
    self.pointsAgainst = data['record']['pointsAgainst'] # recomputed later based on week
    self.schedule      = []
    self.home_away     = [] # 0: home 1: away
    self.scores        = []
    self.mov           = []
    self.awp           = 0.
    self.awins         = 0.
    self.alosses       = 0.
    self.sos           = 1.
    self.power_rank    = 1.
    self.dom_rank      = 1.
    self.colley_rank   = 1.
    self.lsq_rank      = 1.
    self.luck          = 1.
    self.tier          = 1.
    self.rank_overall  = 1.
    self.prev_rank     = 1.
    self.prev_rank_overall= 1.
    self._fetch_schedule(data)

  def __repr__(self):
    return 'Team: %s'%(self.teamName)
  
  def _dump(self):
    for attr in sorted(self.__dict__):
      if hasattr(self, attr):
        print('%20s:\t%s'%(attr, getattr(self,attr)))

  def _fetch_schedule(self, data):
    '''Fetch schedule and scores for team'''
    matchups = data['scheduleItems']
    for matchup in matchups:
      if matchup['matchups'][0]['isBye'] == False:
        if matchup['matchups'][0]['awayTeamId'] == self.teamId:
          score = matchup['matchups'][0]['awayTeamScores'][0]
          opponentId = matchup['matchups'][0]['homeTeamId']
          home_away = 1 # 1 for away
        else:
          score = matchup['matchups'][0]['homeTeamScores'][0]
          opponentId = matchup['matchups'][0]['awayTeamId']
          home_away = 0 # 0 for home
      else:
        score = matchup['matchups'][0]['homeTeamScores'][0]
        opponentId = matchup['matchups'][0]['homeTeamId']
        print('WARNING, BYE WEEK...Check!') #FIXME what to do here?

      self.scores.append(score)
      self.schedule.append(opponentId)
      self.home_away.append(home_away)
