#!/usr/bin/env python

"""
Calculate the ratings matrix using linear win-difference ratio

Notation is used from the following paper:
   http://www.phys.utk.edu/sorensen/ranking/Documentation/Sorensen_documentation_v1.pdf
"""

from pathlib import Path
import logging
from scipy.optimize import lsq_linear
from scipy.sparse import coo_matrix
import numpy as np
import pandas as pd
from plotnine import ggplot, aes, geom_line, geom_label, theme_bw, labs, guides
import warnings

__author__ = 'Ryne Carbone'

logger = logging.getLogger(__name__)


def calc_n_g(df_schedule, week):
  """Calculate list of games i.e. Ng

  Each row has home_id, away_id, home_total_points, away_total_points
  :param df_schedule: data frame with each matchup
  :param week: current matchup period id
  :return: list of games with team ids and scores for home/away
  """
  df_scores = (
    df_schedule
    .query(f'matchupPeriodId <= {week} & winner!="UNDECIDED"')
    [['home_id', 'away_id', 'home_total_points', 'away_total_points']]
  )
  return df_scores


def calc_r_g(df_scores, dS_max=35., B_w=30., B_r=35.):
  """Calculates game result given home and away scores

  :param df_scores: data frame with columns home_id, away_id, home_total_points, away_total_points
  :param dS_max: maximum score differential for truncating
  :param B_w: bonus for win
  :param B_r: bonus for score ratio
  :return: game result, i.e. R_g
  """
  df_scores['home_mov'] = df_scores.get('home_total_points') - df_scores.get('away_total_points')
  df_scores['home_mov_trunc'] = dS_max * np.tanh(df_scores.get('home_mov') / dS_max)
  df_scores['score_winner'] = df_scores.apply(
    lambda x: x.get('home_total_points')
    if x.get('home_total_points') > x.get('away_total_points')
    else x.get('away_total_points')
    , axis=1)
  df_scores['home_bonus_sign'] = np.sign(df_scores.get('home_mov'))
  df_scores['R_g'] = df_scores.apply(
    lambda x: B_w*x.get('home_bonus_sign') + x.get('home_mov_trunc') + B_r*x.get('home_mov')/x.get('score_winner')
    , axis=1)
  return df_scores.get('R_g')


def calc_sig_g(N_g, df_ranks, beta_w):
  """Calculate sigma for each game

  :param N_g: data frame with record of home/away teams
  :param df_ranks: data frame with the previous ranks for each team
  :param beta_w: controls weighting of alpha_w
  :return: sigma for each game
  """
  alpha_w = (df_ranks.get('ranks').max(axis=0) - df_ranks.get('ranks').min(axis=0)) / np.log(beta_w * beta_w)
  N_g['home_rank'] = N_g.get('home_id').apply(lambda x: df_ranks.loc[df_ranks.team_id == x, 'ranks'].values[0])
  N_g['away_rank'] = N_g.get('away_id').apply(lambda x: df_ranks.loc[df_ranks.team_id == x, 'ranks'].values[0])
  w_g = np.exp(-np.fabs(N_g.get('home_rank') - N_g.get('away_rank')) / alpha_w)
  sig_g = 1 / np.sqrt(w_g)
  return sig_g


def calc_ranks_lsq_iter(df_teams, N_g, R_g, prev_ranks=None, beta_w=2.2, initial_pass=False):
  """Calculates new rankings based on previous rankings using linear lsq algorithm

  :param df_teams: data frame with team ids
  :param N_g: data frame with rows for each game and home/away ids
  :param R_g: game results based on score differential
  :param prev_ranks: data frame with previous iteration rankings for each team
  :param beta_w: control weighting of alpha_w
  :param initial_pass: flag to indicate first iteration of algorithm
  :return: list of new rankings
  """
  if initial_pass:
    sig_g = np.ones(N_g.index.size)
  else:
    sig_g = calc_sig_g(N_g=N_g, df_ranks=prev_ranks, beta_w=beta_w)
  # Calculate the coefficient vector
  b = R_g/sig_g
  # Get dimensions for matrix
  max_id = max(N_g.get('away_id').max(),
               N_g.get('home_id').max())
  n_games = N_g.get('home_id').size
  # Calculate the matrix using COO formatted matrix (n_games x n_teams dimensions)
  # Elements are +/- 1/sig_g if team is home/away else 0
  home_coo = coo_matrix((1/sig_g, (N_g.home_id.index, N_g.home_id.values)), shape=(n_games, max_id+1))
  away_coo = coo_matrix((-1/sig_g, (N_g.away_id.index, N_g.away_id.values)), shape=(n_games, max_id+1))
  A = home_coo + away_coo
  # Solve for the rankings
  res = lsq_linear(A=A, b=b, bounds=(30, 130))
  if res.success == False:
    logger.warning(f'WARNING: {res.message}')
  # Match the rankings to the teams and return a data frame
  new_ranks = pd.DataFrame(dict(team_id=df_teams.team_id, ranks = res.x[df_teams.team_id.values]))
  return new_ranks


def get_ranks_lsq(df_teams, df_schedule, year, week, B_w=30., B_r=35., dS_max=35., beta_w=2.2, show=False):
  """Calculate iterative LSQ rankings, and save plot

  :param df_teams: data frame wtih team_ids
  :param df_schedule: data frame with data for each matchup
  :param year: current year
  :param week: current week
  :param B_w: bonus for wins
  :param B_r: bonus for score ratio
  :param dS_max: max home mov for truncation
  :param beta_w: for measuring alpha_w
  :param show: flag for showing plot
  :return: data frame with team_id and rankings
  """
  logger.debug('Calculating ranks using LSQ method with 100 iterations')
  N_g = calc_n_g(df_schedule, week)
  R_g = calc_r_g(N_g, dS_max=dS_max, B_w=B_w, B_r=B_r)
  df_ranks = calc_ranks_lsq_iter(
    df_teams=df_teams,
    N_g=N_g,
    R_g=R_g,
    prev_ranks=None,
    beta_w=beta_w,
    initial_pass=True
  )
  prev_ranks = df_ranks
  # Iterate with previous ranks as input, recalculate weight
  for p in range(1, 100):
    prev_ranks = calc_ranks_lsq_iter(
      df_teams=df_teams,
      N_g=N_g,
      R_g=R_g,
      prev_ranks=prev_ranks,
      beta_w=beta_w,
      initial_pass=False
    )
    df_ranks = pd.concat([df_ranks, prev_ranks.ranks.rename(p)], axis=1)
  # plot_save_ranks
  df_final_ranks = plot_save_rank(
    df_ranks=df_ranks,
    df_teams=df_teams,
    year=year,
    week=week,
    show=show
  )
  return df_final_ranks


def plot_save_rank(df_ranks, df_teams, year, week, show=False):
  """Plot the ranking iterations for each team

  :param df_ranks: data frame with team_id, and rankings for each iteration
  :param df_teams: data frame with team_id and owner info
  :param year: year for data
  :param week: current week
  :param show: flag to display the plot
  :return: final summarised rankings data frame with columns for team_id and ranks
  """
  # Plot each iteration
  df_ranks_lsq = pd.merge(df_teams[['team_id', 'firstName']], df_ranks, on='team_id')
  # Space out labels on x-axis according to final rankings
  df_ranks_lsq['label_x_pos'] = df_ranks_lsq.get(99).rank() * 100 / df_ranks_lsq.get(99).size
  # Convert to long format for plotting ease
  df_ranks_lsq_long = (
    df_ranks_lsq
    .rename({'ranks': '0'}, axis='columns')
    .melt(id_vars=['team_id', 'firstName', 'label_x_pos'])
  )
  # Convert iteration variable to int
  df_ranks_lsq_long.variable = df_ranks_lsq_long.variable.astype(int)
  # Make the plot
  p = (
    ggplot(aes(x='variable', y='value', color='factor(team_id)', group='team_id'),
           data=df_ranks_lsq_long) +
    geom_line() +
    geom_label(aes(label='firstName', x='label_x_pos', y='value', color='factor(team_id)'),
               data=df_ranks_lsq_long[df_ranks_lsq_long.variable == 99],
               size=10) +
    labs(x='Iteration', y='LSQ rank') +
    theme_bw() +
    guides(color=False)
  )
  # Save plot
  if show:
    p.draw()
  # make dir if it doesn't exist already
  out_dir = Path(f'output/{year}/week{week}')
  out_dir.mkdir(parents=True, exist_ok=True)
  out_name = out_dir / 'lsq_iter_rankings.png'
  # plotnine is throwing too many warnings
  warnings.filterwarnings('ignore')
  p.save(out_name, width=9, height=6, dpi=300)
  warnings.filterwarnings('default')
  logger.info(f'Saved LSQ rankings plot to local file: {out_name.resolve()}')
  # Average last 70 elements to get final rank
  df_final_ranks = (
    df_ranks_lsq_long
    .query('variable>70')
    .groupby(['team_id'])[['value']]
    .agg(lambda x: np.tanh(np.mean(x) / 75.))
    .reset_index()
    .rename({'value': 'lsq'}, axis=1)
  )
  # Normalize by max score
  df_final_ranks['lsq'] = df_final_ranks.get('lsq') / df_final_ranks.get('lsq').max()
  return df_final_ranks


