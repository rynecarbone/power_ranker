#!/usr/bin/env python

"""Utility functions to help with main classes"""

from pathlib import Path
import logging
import requests
from bs4 import BeautifulSoup
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from scipy.signal import argrelmin
from .exception import (PrivateLeagueException,
                        InvalidLeagueException,
                        UnknownLeagueException, )

__author__ = 'Ryne Carbone'

logger = logging.getLogger(__name__)


def fix_teamId(teams):
  """Sometimes teamIds skip numbers if people from your league have quit,
    For now, just redefining teamId by number of teams,
    Using that to also fix opponentId.
    Teams should be passed, ordered by ascending teamId"""
  logger.debug('Reordering teamId incase league members have left between seasons')
  old = [] # store old id to find in schedule
  new = [] # store new ids to replace
  for i,t in enumerate(teams):
    old.append(t.teamId)
    new.append(i+1)
    t.teamId = i+1 
  # Replace opponent id in schedule
  for t in teams:
    for w,o in enumerate(t.stats.schedule):
      new_opp = new[old.index(o)] 
      t.stats.schedule[w] = new_opp 


def calc_sos(teams, week, rank_power=2.37):
  """Calculates the strength of schedule,
     based on the lsq rank"""
  # Find avg of opponent rankings
  logger.debug(f'Calculating strength of schedule with rank_power: {rank_power}')
  for t in teams:
    rank_i = 0
    for w, o in enumerate(t.stats.schedule[:week]):
      rank_i += o.rank.lsq**rank_power
    t.rank.sos = rank_i/float(week)


def calc_luck(teams, week, awp_weight=0.5):
  """Calcualtes the luck index, considers:
    - Aggregate winning pct vs actual winning pct
    - Opponents score against you, vs their average score"""
  logger.debug('Calculating luck rankings')
  avg_score_weight = 1 - awp_weight # weight in the luck index
  for t in teams:
    # Calculate the ratio of opponents average score, 
    # over their week score
    o_avg_over_score = 0.
    for w, o in enumerate(t.stats.schedule[:week]):
      o_avg = sum(o.stats.scores[:week])/float(week)
      ratio = o_avg/float(o.stats.scores[w])
      o_avg_over_score += ratio
    # Normalize to numer of weeks
    o_avg_over_score /= float(week)
    # Calculate ratio of your win pct to awg, pad
    # with 0.01 in num and denom to protect against shitty teams
    # with divide by 0
    win_pct = float(t.stats.wins)/float(t.stats.wins+t.stats.losses)
    wpct_over_awp = (0.01 + float(win_pct) )/(0.01 + float(t.stats.awp) )
    # Calculate luck index
    luck_ind = o_avg_over_score*avg_score_weight + wpct_over_awp*awp_weight
    t.rank.luck = 1./luck_ind


def calc_cons(teams, week):
  """Calculate the consistency metric, based on your
     avg, minimum, and maximum scores"""
  logger.debug('Calculating consistency rankings')
  for t in teams:
    t_min = float(min(t.stats.scores[:week]))
    t_max = float(max(t.stats.scores[:week]))
    t_avg = float(sum(t.stats.scores[:week]))/float(week)
    t_cons = t_min+t_max+t_avg 
    t.rank.cons = t_cons


def calc_power(teams, week, w_dom=0.18, w_lsq=0.18, w_col=0.18, w_awp=0.18,
               w_sos=0.06, w_luck=0.06, w_cons=0.10, w_strk=0.06):
  """Calculates the final power rankings based on input metrics"""
  logger.debug('Aggregating all power rankings')
  for t in teams:
    dom  = float(t.rank.dom)
    lsq  = float(t.rank.lsq)
    col  = float(t.rank.col)
    awp  = float(t.stats.awp)
    sos  = float(t.rank.sos)
    luck = float(t.rank.luck)
    cons = float(t.rank.cons) 
    strk = float(t.stats.streak) * int(t.stats.streak_sgn)
    # Only count streaks longer than one game
    strk = 0.25*strk if strk > 1. else 0.
    # Weigh metrics according to the weights
    power = ( dom*w_dom + lsq*w_lsq + col*w_col + awp*w_awp + sos*w_sos +
              luck*w_luck + cons*w_cons + strk*w_strk )
    # Normalize with hyperbolic tangent #FIXME should this be configurable too?
    t.rank.power = 100*np.tanh(power/0.5)


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
