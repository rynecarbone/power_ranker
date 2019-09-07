# coding=utf-8

"""Calculate colley matrix"""

import logging
import numpy as np
import pandas as pd
from scipy.linalg import solve
from scipy.sparse import coo_matrix

__author__ = 'Ryne Carbone'

logger = logging.getLogger(__name__)


def get_colley_ranks(df_schedule, week, printMatrix=False):
    """Calculate colley ranks

    :param df_schedule: data frame with row for each matchup
    :param week: current week
    :param printMatrix: flag to print colley matrix
    :return: data frame with colley rankings and team id
    """
    colley_matrix = build_colley_matrix(df_schedule=df_schedule, week=week, printMatrix=printMatrix)
    colley_b = build_colley_intercept(df_schedule=df_schedule, week=week)
    # Solve the matrix equation
    colley_ranks = pd.DataFrame(solve(colley_matrix, colley_b), columns=['col'])
    # Add in team_id
    colley_ranks['team_id'] = colley_matrix.index
    # Normalize by max rank
    colley_ranks['col'] = colley_ranks.get('col') / colley_ranks.get('col').max()
    return colley_ranks


def build_colley_matrix(df_schedule, week, printMatrix=False):
    """Build the colley matrix
    C_ij = -n_ij              (number of games team i played team j)
    C_ii = 2 + n_i            (total games team i played)
    :param df_schedule: data frame with rows for each matchup
    :param week: current week
    :param printMatrix: flag to print colley matrix
    :return: colley matrix
    """
    # Create COO formatted schedule matrix
    # v, (x,y)  where:
    #   x: team id
    #   y: opponent id
    #   v: (1-decay) + decay * week_i/current_week if team wins else 0
    # Note: takes care of repeat (x,y) by summing v as expected
    # First get max team_id
    max_id = max(df_schedule.get('away_id').max(),
                 df_schedule.get('home_id').max())
    df_schedule_coo = (
        df_schedule
        .query(f'matchupPeriodId<={week} & winner!="UNDECIDED"')
        [['away_id', 'home_id', 'matchupPeriodId', 'winner']]
    )
    # Off-diagonal elements are -1 for every matchup
    colley_coo = coo_matrix((
        -1 * np.ones(len(df_schedule_coo.get('away_id'))),
        (df_schedule_coo.get('away_id').values,
         df_schedule_coo.get('home_id').values)
    ), shape=(max_id+1, max_id+1))
    # Add transverse to itself -- count both home and away
    colley_coo += colley_coo.T
    colley_matrix = pd.DataFrame(colley_coo.toarray())
    # Calculate diagonal: 2+total games played
    tot_games_played = -1*np.array(colley_coo.sum(axis=0).flat)
    colley_diag = np.diag(
        [2 + n_g
         if n_g > 0 else n_g
         for n_g in tot_games_played]
    )
    # Add diagonal to the matrix
    colley_matrix = colley_matrix + colley_diag
    # Remove zero rows adn columns (teams no longer in the league)
    non_zero_rows = (colley_matrix != 0).any(axis=1)
    non_zero_cols = (colley_matrix != 0).any(axis=0)
    colley_matrix = colley_matrix.loc[non_zero_rows, non_zero_cols]
    # Optionally print matrix
    if printMatrix:
        print(colley_matrix)
    return colley_matrix


def build_colley_intercept(df_schedule, week):
    """Build b vector for weighted record
    b_i  = 1 + 0.5(w_i - l_i) (can introduce weights as well)
    :param df_schedule: data frame with rows for each matchup
    :param week: current week
    :return: weighted record vector
    """
    away_net_wins = (
        df_schedule
        .query(f'matchupPeriodId<={week} & winner!="UNDECIDED"')
        .groupby('away_id')
        .agg(away_net_wins=('winner', lambda x: sum(x == 'AWAY') - sum(x == 'HOME')))
        .reset_index()
        .rename({'away_id': 'team_id'}, axis=1)
    )
    home_net_wins = (
        df_schedule
        .query(f'matchupPeriodId<={week} & winner!="UNDECIDED"')
        .groupby('home_id')
        .agg(home_net_wins=('winner', lambda x: sum(x == 'HOME') - sum(x == 'AWAY')))
        .reset_index()
        .rename({'home_id': 'team_id'}, axis=1)
    )
    net_wins = (
        pd.merge(away_net_wins, home_net_wins, on='team_id', how='outer')
        .fillna(0)
        .sort_values('team_id')
        .reset_index(drop=True)
    )
    b = 1 + 0.5 * (net_wins.get('away_net_wins') + net_wins.get('home_net_wins'))
    return b



