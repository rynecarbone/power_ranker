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


def save_team_weekly_ranking_plots(year, week):
  """Create plot of historic team rankings this season

  :param year: current year
  :param week: current week
  :return: None
  """
  # Read in calculated rankings for the season
  input_dir = Path(f'output/{year}')
  f_rankings = input_dir / 'weekly_rankings.csv'
  df_ranks = pd.read_csv(f_rankings)
  # Create directory to save plots
  out_dir = Path(f'output/{year}/week{week}/ranking_plots')
  out_dir.mkdir(parents=True, exist_ok=True)
  # Convert from wide to long
  df_ranks = df_ranks.melt(id_vars=['team_id', 'week'], value_vars=['overall', 'power']).reset_index(drop=True)
  # Get team ids
  team_ids = df_ranks.get('team_id').unique().tolist()
  # Get max rank for plot
  max_rank = df_ranks.get('value').max()
  # Create power history plot for each team
  for team_id in team_ids:
    p = (ggplot(aes(x='factor(week)',
                    y='value',
                    color='variable',
                    group='variable'),
                data=df_ranks[df_ranks.team_id == team_id]) +
         geom_line(aes(linetype='variable'), alpha=0.7, size=2) +
         geom_point(size=3) +
         scale_y_reverse(breaks=[x for x in range(max_rank, 0, -1)],
                         minor_breaks=[],
                         limits=[max_rank, 1]) +
         labs(x='Week', y='Ranking', color='Ranking', linetype='Ranking') +
         theme_bw() +
         theme(legend_background=element_rect(alpha=0),
               plot_background=element_rect(fill='white'),
               panel_background=element_rect(fill='white'),
               legend_box_margin=0,
               strip_margin=0,
               legend_title=element_text(size=8),
               legend_text=element_text(size=7))
         )
    out_file = out_dir / f'ranking_{int(team_id)}.png'
    warnings.filterwarnings('ignore')
    p.save(out_file, width=8, height=2, dpi=300)
    warnings.filterwarnings('default')
  logger.info(f'Saved team power ranking history plots')

