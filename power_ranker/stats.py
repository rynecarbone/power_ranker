#!/usr/bin/env python

"""Class to handle statistics for each team"""

import logging

__author__ = 'Ryne Carbone'

logger = logging.getLogger(__name__)


class TeamStats:
  """Keep track of team stats"""
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
    print(f'             FAAB : {self.faab}')
    print(f'     Transactions : {self.trans}')
    print(f'           Trades : {self.trades}')
    print(f'           Waiver : {self.waiver}')
    print(f'             Wins : {self.wins}')
    print(f'           Losses : {self.losses}')
    print(f'           Streak : {self.streak}')
    print(f'      Streak Sign : {self.streak_sgn}')
    print(f'       Points For : {self.pointsFor}')
    print(f'   Points Against : {self.pointsAgainst}')
    print(f'         Schedule : {self.schedule}')
    print(f'Home (0) Away (1) : {self.home_away}')
    print(f'           Scores : {self.scores}')
    print(f'Margin of Victory : {self.mov}')
    print(f'   Aggregate wpct : {self.awp}')
    print(f'   Aggregate wins : {self.awins}')
    print(f' Aggregate losses : {self.alosses}')

  def _replace_opponents(self, teams):
    """Replace team id number with team object"""
    logger.debug('Replacing opponents in team schedule')
    for week, matchup in enumerate(self.schedule):
      for opponent in teams:
        if matchup == opponent.teamId:
          self.schedule[week] = opponent

  def _calc_mov(self):
    """Calculate the margin of victory"""
    logger.debug('Calculating the margin of victory for each game in schedule')
    for week, opponent in enumerate(self.schedule):
      mov = self.scores[week] - opponent.stats.scores[week]
      self.mov.append(mov)

  def _calc_wins_losses(self, teamId, week, teams):
    """Recalculates based on specified week:
       points for, points against
       wins, losses, streak
       aggregate wins, aggregate losses,
       aggregate wpct"""
    logger.debug('Recalculating points, wins/losses, aggregate wins/losses based on week')
    self.awins      = 0. # aggregate wins
    self.alosses    = 0. # aggregate losses
    self.pointsFor  = 0. # points for
    self.pointsAgainst = 0. # points against
    self.wins       = 0
    self.losses     = 0
    self.streak     = 0  # streak
    self.streak_sgn = 1  # sign of streak
    # Loop over weeks, retrieve score and week's opponent
    for w, (s, w_o) in enumerate(zip(self.scores[:week], self.schedule[:week])):
      # points for, against, wins, losses, streak, sign
      self.pointsFor += s
      self.pointsAgainst += w_o.stats.scores[w]
      # Update wins and streak
      self._update_streak(own_score=s, opp_score=w_o.stats.scores[w])
      # aggregate wins/losses
      for o in teams:
        if o.teamId != teamId:
          if s > o.stats.scores[w]:
            self.awins += 1
          else:
            self.alosses += 1
    # Update aggregate win pct
    self.awp = float(self.awins)/(float(self.awins)+float(self.alosses))

  def _update_streak(self, own_score, opp_score):
    """Update wins/losses and streaks
    :param own_score: team weekly score
    :param opp_score: opponents score that week
    :return: None
    """
    # Team scores more than opponent
    if own_score > opp_score:
      self.wins += 1
      if self.streak_sgn == -1:
        self.streak_sgn = 1
        self.streak = 1
      else:
        self.streak += 1
    else:
      self.losses += 1
      if self.streak_sgn == 1:
        self.streak_sgn = -1
        self.streak = 1
      else:
        self.streak += 1
