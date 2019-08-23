#!/usr/bin/env python

"""Calculate two step dominance matrix"""

import logging
import pandas as pd
from scipy.sparse import coo_matrix

__author__ = 'Ryne Carbone'

logger = logging.getLogger(__name__)


def get_two_step_dom_ranks(df_schedule, week, sq_weight=0.25, decay_penalty=0.5):
    """Calculate rankings using two step dominance matrix

    Note: No longer returning 'normed' dominance rankings
    Need to normalize by average rank after joining to team data
    :param df_schedule: daata frame with rows for each matchup
    :param week: current week
    :param sq_weight: weight for the squared wins matrix
    :param decay_penalty: weigh current wins more
    :return: data frame with rankings for each team
    """
    wins_matrix = calc_wins_matrix(df_schedule, week, decay_penalty)
    dom_matrix = (1-sq_weight)*wins_matrix + sq_weight*(wins_matrix@wins_matrix)
    # For each row, sum values across the columns
    dom_ranks = pd.DataFrame(dom_matrix.sum(axis=1), columns=['dom_rank'])
    # Add in team_id so we can join later
    dom_ranks['team_id'] = dom_ranks.index
    #pd.merge(df_teams, dom_ranks, on='team_id', how='inner')
    return dom_ranks


def calc_wins_matrix(df_schedule, week, decay_penalty):
    """Calculate wins matrix from season schedule

    Note: there will be some extra zero-filled rows if team ids
    are non-contiguous, for example from teams leaving/entering
    the league from year to year. This will be fine when we sum
    the rows later.

    :param df_schedule: data frame with rows for each matchup
    :param week: current week
    :param decay_penalty: weigh current wins more
    :return: n_teams x n_teams wins matrix
    """
    # Create COO formatted wins matrix
    # v, (x,y)  where:
    #   x: team id
    #   y: opponent id
    #   v: (1-decay) + decay * week_i/current_week if team wins else 0
    # Note: takes care of repeat (x,y) by summing v as expected
    df_schedule_coo = (
      df_schedule
      .query(f'matchupPeriodId<={week} & winner!="UNDECIDED"')
      [['away_id', 'home_id', 'matchupPeriodId', 'winner']]
    )
    # Calculate matrix values for away wins
    df_schedule_coo['away_value'] = df_schedule_coo.apply(
      lambda x: (1 - decay_penalty) + decay_penalty * x.get('matchupPeriodId') / week
      if x.get('winner') == 'AWAY' else 0,
      axis=1
    )
    # Calculate matrix values for home wins
    df_schedule_coo['home_value'] = df_schedule_coo.apply(
      lambda x: (1 - decay_penalty) + decay_penalty * x.get('matchupPeriodId') / week
      if x.get('winner') == 'HOME' else 0,
      axis=1
    )
    # Convert from series to sparse coo, add home and away values
    wins_matrix = coo_matrix(
      (df_schedule_coo.get('away_value').values,
       (df_schedule_coo.get('away_id').values,
        df_schedule_coo.get('home_id').values))
    )
    wins_matrix += coo_matrix(
      (df_schedule_coo.get('home_value').values,
       (df_schedule_coo.get('home_id').values,
        df_schedule_coo.get('away_id').values))
    )
    return wins_matrix



