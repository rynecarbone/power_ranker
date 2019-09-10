#!/usr/bin/env python

"""Create box-plot of power rankings vs points scored"""

import logging
from pathlib import Path
import pandas as pd
from plotnine import *
import warnings

__author__ = 'Ryne Carbone'

logger = logging.getLogger(__name__)


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


def make_power_plot(df_ranks, df_schedule, df_teams, year, week):
  """Create plot of weekly scores and current power rankings

  :param df_ranks: data frame with current power rankings
  :param df_schedule: data frame with scores for each game
  :param df_teams: data frame with team names
  :param year: current year
  :param week: current week
  :return: None
  """
  # Grab team id and power score, convert power to ranking
  df_plot = df_ranks[['team_id', 'power', 'tier']].reset_index(drop=True)
  # Add power rankings as categorical variable for plot
  df_plot['power'] = pd.Categorical(
    df_plot.get('power').rank(ascending=False).astype(int),
    categories=[i for i in range(df_plot.team_id.size, 0, -1)],
    ordered=True
  )
  # Add in first names for each team
  df_plot['Name'] = df_plot.apply(
    lambda x: df_teams.loc[df_teams.team_id == x.get('team_id'), 'firstName'].values[0],
    axis=1)
  # Add in weekly scores
  df_plot['scores'] = df_plot.apply(
    lambda x: get_team_scores(df_schedule=df_schedule, team=x.get('team_id'), week=week).values,
    axis=1)
  # Add in where to put labels
  df_plot['label_pos'] = df_plot.scores.apply(lambda x: max(x) + 10)
  # Explode list into a row for each week
  df_plot = df_plot.explode('scores')
  df_plot.scores = df_plot.scores.astype(float)
  # noinspection PyTypeChecker
  p = (
    ggplot(aes(y='scores', x='factor(power)', group='factor(power)', color='factor(tier)'), data=df_plot) +
    geom_boxplot(alpha=.8, outlier_alpha=0) +
    geom_jitter(width=.1, alpha=.3, color='black') +
    geom_text(aes(label='Name', x='factor(power)', y='label_pos'),
              color='black',
              nudge_y=3,
              data=df_plot.groupby(['team_id']).agg(max).reset_index(drop=True)) +
    coord_flip() +
    labs(x='Power Ranking', y='Weekly Score') +
    theme_bw() +
    theme(legend_title=element_text(text='Tiers', size=10),
          legend_position=(0.18, .72),
          legend_background=element_rect(alpha=0),
          panel_grid_major_y=element_blank())
  )
  # Specify where to save the plot
  out_dir = Path(f'output/{year}/week{week}')
  out_dir.mkdir(parents=True, exist_ok=True)
  out_name = out_dir / 'power_plot.png'
  warnings.filterwarnings('ignore')
  p.save(out_name, width=10, height=5.6, dpi=300)
  warnings.filterwarnings('default')
  logger.info(f'Saved power ranking plot to local file: {out_name.resolve()}')

