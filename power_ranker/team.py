from .rank import TeamRank
from .stats import TeamStats

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
    self.stats         = TeamStats(data)
    self.rank          = TeamRank() 
    self._get_game_data(data)

  def __repr__(self):
    return 'Team Id: %s Team: %s Owner: %s'%(self.teamId, self.teamName, self.owner)

  def _dump(self):
    for attr in sorted(self.__dict__):
      if hasattr(self, attr):
        print('%20s:\t%s'%(attr, getattr(self,attr)))

  def _get_game_data(self, data):
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
      self.stats.scores.append(score)
      self.stats.schedule.append(opponentId)
      self.stats.home_away.append(home_away)
