#!/usr/bin/env python

"""Save fantasy football league settings

TODO: update use of divisions -> key changed from divisionId -> id
"""

import logging
import pandas as pd

__author__ = 'Ryne Carbone'

logger = logging.getLogger(__name__)


class Settings(object):
    """Creates Settings object"""
    def __init__(self, data):
        logger.info('Fetching and storing league settings')
        self.id = data.get('id')
        self.league_name = data.get('settings').get('name')
        self.year = data.get('seasonId')
        self.n_teams = data.get('status').get('teamsJoined')
        self.divisions = data.get('settings').get('scheduleSettings').get('divisions')# dict with keys: 'size', 'name', 'id'
        self.reg_season_count = data.get('settings').get('scheduleSettings').get('matchupPeriodCount')
        self.reg_season_period_length = data.get('settings').get('scheduleSettings').get('matchupPeriodLength')
        self.final_season_count = data.get('status').get('finalScoringPeriod')
        self.playoff_team_count = data.get('settings').get('scheduleSettings').get('playoffTeamCount')
        self.playoff_period_length = data.get('settings').get('scheduleSettings').get('playoffMatchupPeriodLength')
        self.matchup_periods = data.get('settings').get('scheduleSettings').get('matchupPeriods')
        self.status = pd.Series(data.get('status'))
        self.use_faab = data.get('settings').get('acquisitionSettings').get('isUsingAcquisitionBudget')
        self.max_faab = data.get('settings').get('acquisitionSettings').get('acquisitionBudget')
        self.min_bid = data.get('settings').get('acquisitionSettings').get('minimumBid')
        self.lineup_slot_counts = data.get('settings').get('rosterSettings').get('lineupSlotCounts')
        self._fetch_roster_settings()
        #self._fetch_tie_rules(data)

    def __repr__(self):
      s_out = ''
      for attr in sorted(self.__dict__):
        if hasattr(self, attr):
          s_out += '%20s: %s\n'%(attr, getattr(self,attr))
      return s_out

    def __iter__(self):
        for attr, value in self.__dict__.items():
            yield attr, value
    
    def _fetch_roster_settings(self):
        """Grabs roster settings"""
        roster_map = {
            '0': 'QB',
            '1': 'TQB',
            '2': 'RB',
            '3': 'RB/WR',
            '4': 'WR',
            '5': 'WR/TE',
            '6': 'TE',
            '7': 'OP',
            '8': 'DT',
            '9': 'DE',
            '10': 'LB',
            '11': 'DL',
            '12': 'CB',
            '13': 'S',
            '14': 'DB',
            '15': 'DP',
            '16': 'D/ST',
            '17': 'K',
            '18': 'P',
            '19': 'HC',
            '20': 'BE',
            '21': 'IR',
            '22': '',
            '23': 'RB/WR/TE',
            '24': 'ER',
            '25': 'Rookie'
        }
        self.roster = {
            roster_map[k]: self.lineup_slot_counts[k]
            for k in self.lineup_slot_counts.keys()
            if self.lineup_slot_counts[k] > 0
        }

    def _fetch_tie_rules(self, data):
        """Grabs matchup and playoff seeding tie info"""
        tie_map = {
           0: 'None',
           1: 'Home Team Wins',
           2: 'Most Bench Points',
           3: 'Most QB Points',
           4: 'Most RB Points'
        }
        tie_id = data['leaguesettings']['tieRule']
        try:
            self.tie_rule = tie_map[tie_id]
        except:
            self.tie_rule = 'Unknown'
        playoff_tie_map = {
           -1: 'Head to Head Record',
           0: 'Total Points For',
           1: 'Intra Division Record',
           2: 'Total Points Against'
        }
        playoff_id = data['leaguesettings']['playoffSeedingTieRuleRawStatId']
        try:
            self.playoff_seed_tie_rule = playoff_tie_map[playoff_id]
        except:
            self.playoff_seed_tie_rule = 'Unknown'
