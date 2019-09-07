#!/usr/bin/env python

"""Utility functions to help with main classes"""

from pathlib import Path
import logging
import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from scipy.signal import argrelmin
from .exception import (PrivateLeagueException,
                        InvalidLeagueException,
                        UnknownLeagueException, )

__author__ = 'Ryne Carbone'

logger = logging.getLogger(__name__)


def calc_sos(df_schedule, df_ranks, week, rank_power=2.37):
  """Calculate the strength of schedule based on lsq rank

  Normalize SOS by max SOS in league
  :param df_schedule: data frame with team ids for each matchup
  :param df_ranks: data frame with rankings from lsq metric
  :param week: current week
  :param rank_power: exponent to use in sos calculation
  :return: data frame of rankings with sos added
  """
  sos = lambda iteam, iweek: (
    df_schedule
    .query(f'(home_id=={iteam} | away_id=={iteam}) & (matchupPeriodId <= {iweek} & winner != "UNDECIDED")')
    .apply(lambda x: x.home_id if x.away_id == iteam else x.away_id, axis=1)
    .apply(lambda x: df_ranks.loc[df_ranks.team_id == x, 'lsq'].values[0])
    .agg(lambda x: sum(x ** rank_power) / len(x))
  )
  df_ranks['sos'] = df_ranks.get('team_id').apply(lambda x: sos(x, week))
  # Normalize SOS by max SOS calculated
  df_ranks['sos'] = df_ranks.get('sos') / df_ranks.get('sos').max()
  return df_ranks


def calc_luck(df_season_summary, df_schedule, week, awp_weight=0.5):
  """Calculate luck ranking

  Takes into account ratio of wins to aggregate wins and ratio
  of opponents average score to opponents week score.
  Higher luck ranking boosts un-lucky teams

  :param df_season_summary: data frame with win pct, agg win pct and team id
  :param df_schedule: data frame with scores for each matchup
  :param week: current week
  :param awp_weight: relative weight between awp ratio and opp score ratio
  :return: data frame with luck ranking
  """
  # Calculate ratio of wpct to aggregate wpct (Add .01 to num/denom to guard against shitty teams)
  df_luck = df_season_summary.apply(
    lambda x: pd.Series({'team_id': x.team_id,
                         'awp_ratio': (0.01+x.wins/x.games)/(0.01+x.agg_wpct)}),
    axis=1)
  df_luck['opp_ratio'] = df_luck.apply(lambda x: get_opp_score_ratio(df_schedule, x.team_id, week), axis=1)
  # Calculate the weighted sum of awp ratio and opp score ratio
  df_luck['luck_ind'] = df_luck.apply(lambda x: x.awp_ratio*awp_weight + x.opp_ratio*(1-awp_weight), axis=1)
  # Luck ranking is the inverse -- rewards unlucky teams
  df_luck['luck'] = df_luck.apply(lambda x: 1. / x.luck_ind, axis=1)
  # Normalize luck ranking by max ranking
  df_luck['luck'] = df_luck.get('luck') / df_luck.get('luck').max()
  return df_luck[['team_id', 'luck']].reset_index(drop=True)


def get_team_scores(df_schedule, team, week):
  """Get all scores for a team

  :param df_schedule: data frame with scores and team ids for each game
  :param team: id for team
  :param week: current week
  :return: series of scores for team up to week
  """
  return (
    df_schedule
    .query(f'(home_id=={team} | away_id=={team}) & (matchupPeriodId <= {week} & winner != "UNDECIDED")')
    .apply(lambda x: x.home_total_points if x.home_id == team else x.away_total_points, axis=1)
  )


def get_opp_score_ratio(df_schedule, team, week):
  """Calculate ratio of opponents average score to opponents score during week they play you

  :param df_schedule: data frame with scores and team ids for each matchup
  :param team: team id
  :param week: current week
  :return: ratio of opponents average score to score during current week
  """
  return (
    df_schedule
    .query(f'(home_id=={team} | away_id=={team}) & (matchupPeriodId <= {week} & winner != "UNDECIDED")')
    .apply(lambda x:
           pd.Series({'opp_score': x.home_total_points,
                      'opp_avg_score': get_team_scores(df_schedule, x.home_id, week).mean()})
           if x.away_id == team else
           pd.Series({'opp_score': x.away_total_points,
                      'opp_avg_score': get_team_scores(df_schedule, x.away_id, week).mean()}), axis=1)
    .apply(lambda x: x.opp_avg_score / x.opp_score, axis=1)
    .agg(lambda x: x.mean())
  )


def calc_cons(df_ranks, df_schedule, week):
  """Calculate the consistency metric, based on your
     avg, minimum, and maximum scores

  :param df_ranks: data frame with rankings for each metric
  :param df_schedule: data frame with scores and team ids for each game
  :param week: current week
  :return: data frame with rankings
  """
  logger.debug('Calculating consistency rankings')
  # Get scores for each team
  df_scores = df_ranks.apply(
    lambda x: pd.Series({'team_id': x.team_id,
                         'scores': get_team_scores(df_schedule, x.team_id, week).values})
    , axis=1)
  # Add min, max, and average score
  df_scores['cons'] = df_scores.apply(lambda x: x.scores.min() + x.scores.max() + x.scores.mean(), axis=1)
  # Normalize by highest cons score
  df_scores['cons'] = df_scores.get('cons') / df_scores.get('cons').max()
  # Merge back into rankings data frame
  df_ranks  = (
    pd.merge(df_ranks, df_scores[['team_id', 'cons']].reset_index(drop=True), on='team_id', how='left')
    .sort_values('team_id')
    .reset_index(drop=True)
  )
  return df_ranks


def calc_power(df_ranks, df_season_summary, w_dom=0.18, w_lsq=0.18, w_col=0.18,
               w_awp=0.18, w_sos=0.06, w_luck=0.06, w_cons=0.10, w_strk=0.06):
  """Calculates the final power rankings based on input metrics

  :param df_ranks: data frame with calculated rankings
  :param df_season_summary: data frame with summarised data for each team
  :param w_dom: weight for two step dominance ranking
  :param w_lsq: weight for lsq ranking
  :param w_col: weight for colley ranking
  :param w_awp: weight for aggregate winning percentage
  :param w_sos: weight for strength of schedule ranking
  :param w_luck: weight for luck ranking
  :param w_cons: weight for consistency ranking
  :param w_strk: weight for streak
  """
  logger.debug('Aggregating all power rankings')
  # Only count winning streaks greater than one game
  discount_streak = lambda streak: 0.25*streak if streak > 1. else 0
  # Combine all ranks with weights
  df_ranks['power'] = df_ranks.apply(
    lambda x:
    w_dom * x.get('dom') +
    w_lsq * x.get('lsq') +
    w_col * x.get('col') +
    w_awp * df_season_summary.loc[df_season_summary.team_id == x.team_id, 'agg_wpct'].values[0] +
    w_sos * x.get('sos') +
    w_luck * x.get('luck') +
    w_cons * x.get('cons') +
    w_strk * discount_streak(df_season_summary.loc[df_season_summary.team_id == x.team_id, 'streak'].values[0])
    , axis=1
  )
  # Normalize with hyperbolic tangent #FIXME should this be configurable too?
  df_ranks['power'] = 100.*np.tanh(df_ranks['power']/0.5)
  return df_ranks


def calc_tiers(teams, year, week, bw=0.09, order=4, show=False):
  """Calculate 3-5 tiers using Gaussian Kernal Density"""
  logger.info('Calculating tiers for power rankings')
  # Store rankings in list
  ranks = [t.rank.power for t in teams]
  # Calculate the Kernal Density Estimation
  kde = gaussian_kde(ranks, bw_method=bw)
  # Make plot
  x_grid = np.linspace(min(ranks)-10., max(ranks)+10., len(ranks)*10)
  f2 = plt.figure(figsize=(10,6))
  plt.plot(x_grid, kde(x_grid))
  if show: plt.show()
  # Create directory if it doesn't exist to save plot
  out_dir = Path(f'output/{year}/week{week}')
  out_dir.mkdir(parents=True, exist_ok=True)
  out_name = out_dir / 'tiers.png'
  f2.savefig(out_name)
  plt.close()
  logger.info(f'Saved tiers plot to local file {out_name.resolve()}')
  # Find minima to define tiers, separted by at least +/- order
  minima = x_grid[ argrelmin( kde(x_grid), order=order)[0] ]
  s_min = sorted(minima, reverse=True)
  tier = 1
  # Build tiers from minima
  for t in teams:
    # lowest tier
    if tier > len(s_min):
      tier += 0
    # if rank below current minima, create new tier
    elif t.rank.power < s_min[tier-1]:
      if tier < 5: tier += 1
    # Save tier
    t.rank.tier =  tier


def save_ranks(teams, year, week, getPrev=True):
  """Save the power rankings to a file,
    optionally retreive previous week's rankings"""
  # Save power rankings (teamId:rank)
  new_dir = Path(f'output/{year}/week{week}')
  new_dir.mkdir(parents=True, exist_ok=True)
  new_name = new_dir / 'ranks_power.txt'
  f_new = open(new_name, 'w')
  # Write to file (teams should be passed sorted by ranking)
  for i, t in enumerate(teams):
    f_new.write('%s:%s\n'%(t.teamId, i+1))
  f_new.close()
  logger.info(f'Saved power rankings (teamId:rank) to local file: {new_name.resolve()}')
  # Save ESPN overall rankings teamId:rank
  teams_sorted_overall = sorted(teams, key=lambda x: (x.stats.wins, x.stats.pointsFor), reverse=True)
  new_name = new_dir / 'ranks_overall.txt'
  f_new = open(new_name, 'w')
  # Write to file (sorted by ESPN rankings)
  for i, t in enumerate(teams_sorted_overall):
    f_new.write('%s:%s\n'%(t.teamId, i+1))
    t.rank.overall = i+1
  f_new.close()
  logger.info(f'Saved overall ESPN rankings (teamId:rank) to local file: {new_name.resolve()}')
  # Exit if not comparing to previous rankings
  if not getPrev: 
    return
  # Get prevoius power rankings
  old_dir = Path(f'output/{year}/week{week-1}')
  old_dir.mkdir(parents=True, exist_ok=True)
  old_name = old_dir / 'ranks_power.txt'
  f_old = open(old_name, 'r')
  for line in f_old:
    team_rank = (line.strip()).split(':')
    t_id = team_rank[0]
    t_rk = team_rank[1]
    # Sorted by this weeks power rankings
    for t in teams:
      if int(t.teamId) == int(t_id):
        t.rank.prev = t_rk
  f_old.close()
  logger.info(f'Read previous power rankings from local file: {old_name.resolve()}')
  # Get Previous overall rankings
  old_name = old_dir / 'ranks_overall.txt'
  f_old = open(old_name, 'r')
  for line in f_old:
    team_rank = (line.strip()).split(':')
    t_id = team_rank[0]
    t_rk = team_rank[1]
    # sorted by this week overall
    for t in teams_sorted_overall:
      if int(t.teamId) == int(t_id):
        t.rank.prev_overall = t_rk
  f_old.close()
  logger.info(f'Read previous overall ESPN rankings from local file: {old_name.resolve()}')


def fetch_page(endpoint, params, cookies, use_soup=True, use_json=False):
  """Handle the web scraping for specified endpoint

  :param endpoint: endpoint to retrieve from domain
  :param params: parameter dict to send to requests
  :param cookies: cookies for access to private league
  :param use_soup: flag to use soup to parse html
  :param use_json: flag to parse json
  :return: html parsed content
  """
  logger.debug(f'Fetching page {endpoint} with params: {params}, cookies: {cookies}')
  r = requests.get(endpoint, params=params, cookies=cookies)
  # Make sure our response was ok
  if r.status_code == 401:
    raise PrivateLeagueException(f'endpoint: {endpoint}, params: {params}, cookies: {cookies}')
  elif r.status_code == 404:
    raise InvalidLeagueException(f'endpoint: {endpoint}, params: {params}, cookies: {cookies}')
  elif r.status_code != 200:
    raise UnknownLeagueException(f'endpoint: {endpoint}, params: {params}, cookies: {cookies}')
  # Parse response into html
  if use_soup:
    return BeautifulSoup(r.content, features='lxml')
  elif use_json:
    return r.json()
  else:
    return r.content
