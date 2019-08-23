#!/usr/bin/env python

"""Class to handle all information about team"""

import logging
from .rank import TeamRank
from .stats import TeamStats

__author__ = 'Ryne Carbone'

logger = logging.getLogger(__name__)


class Team(object):
  """Team objects store attributes for each team in the league"""

  def __init__(self, data):
    self.teamId = data['teamId']
    self.teamAbbrev = data['teamAbbrev']
    self.teamName = f"{data['teamLocation']} {data['teamNickname']}"
    self.owner = f"{data['owners'][0]['firstName'].title()} {data['owners'][0]['lastName'].title()}"
    self.logoUrl = data['owners'][0]['photoUrl'] if 'logoUrl' not in data.keys() else data['logoUrl']
    self.divisionId = data['division']['divisionId']
    self.divisionName = data['division']['divisionName']
    self.stats = TeamStats(data)
    self.rank = TeamRank()
    self._get_game_data(data)

  def __repr__(self):
    return f'Team Id: {self.teamId} Team: {self.teamName} Owner: {self.owner}'

  def _dump(self):
    for attr in sorted(self.__dict__):
      if hasattr(self, attr):
        print(f'{attr:20}:\t{getattr(self, attr)}')

  def _get_game_data(self, data):
    """Fetch schedule and scores for team"""
    logger.debug(f'Parsing schedule and match up data for team {self.teamId}')
    match_ups = data['scheduleItems']
    for match_up in match_ups:
      if not match_up['matchups'][0]['isBye']:
        if match_up['matchups'][0]['awayTeamId'] == self.teamId:
          score = match_up['matchups'][0]['awayTeamScores'][0]
          opp_id = match_up['matchups'][0]['homeTeamId']
          home_away = 1 # 1 for away
        else:
          score = match_up['matchups'][0]['homeTeamScores'][0]
          opp_id = match_up['matchups'][0]['awayTeamId']
          home_away = 0 # 0 for home
      else:
        score = match_up['matchups'][0]['homeTeamScores'][0]
        opp_id = match_up['matchups'][0]['homeTeamId']
        print('WARNING, BYE WEEK...Check!') #FIXME what to do here?
      self.stats.scores.append(score)
      self.stats.schedule.append(opp_id)
      self.stats.home_away.append(home_away)
