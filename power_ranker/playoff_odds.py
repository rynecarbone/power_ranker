#!/usr/bin/env python

"""Simulate the rest of season to calculate playoff odds"""

import logging
import warnings
from pathlib import Path
import pandas as pd
import numpy as np
from scipy.stats import norm
from plotnine import *
from .get_season_data import get_team_scores

__author__ = 'Ryne Carbone'

logger = logging.getLogger(__name__)


def calc_playoffs(df_teams, df_sum, df_schedule, year, week, settings, n_sims=200000):
  """Calculates playoff odds for each team using MC simulations
  
  :param df_teams: has scores and schedule for each team in league
  :param df_sum: summary data about each team
  :param df_schedule: data frame with scores for each team
  :param year: current year
  :param week: current week, needed to simulate rest of season
  :param settings: has settings for regular season, playoffs, divisions
  :param n_sims: number of simulations to run
  """
  logger.info('Calculating playoff odds')
  # Retrieve settings to determine playoff format
  reg_season = settings.reg_season_count
  spots      = settings.playoff_team_count
  divisions  = pd.DataFrame(settings.divisions).rename({'id': 'divisionId', 'name': 'division'}, axis=1)
  n_wc = spots - len(divisions)
  # Add in wins/points for to teams frame
  teams = pd.merge(
    df_teams,
    df_sum[['team_id', 'wins', 'points_for', 'points_against']], on='team_id'
  ).reset_index(drop=True)
  # Fit Gaussian to team scores
  teams['score_fit'] = teams.apply(
    lambda x: norm.fit(get_team_scores(df_schedule=df_schedule, team=x.get('team_id'), week=week)), axis=1
  ).reset_index(drop=True)
  # Run simulations for the remaining games to calculate playoff odds
  df_sim_results = run_simulation(
    teams=teams,
    schedule=df_schedule,
    week=week,
    reg_season=reg_season,
    n_sims=n_sims,
    n_wc=n_wc,
    year=year
  )
  # Calculate the current standings
  calc_standings(teams=teams, divisions=divisions, spots=spots, week=week, reg_season=reg_season)
  # Calculate the expected number of wins for each team
  logger.info('Calculating expected number of wins for remaining games')
  exp_wins = calc_exp_wins(teams, df_schedule, week, reg_season)
  # Print out the results of the simulations
  df_sim_results['playoff_pct'] = df_sim_results['wc_pct'] + df_sim_results['div_pct']
  df_sim_results = (
    pd.merge(df_teams[['team_id', 'firstName', 'lastName']],
             df_sim_results, on='team_id')
    .merge(exp_wins[['team_id', 'total_wins']], on='team_id')
    .sort_values(by=['playoff_pct', 'div_pct', 'wc_pct'], ascending=[False, False, False])
    .reset_index(drop=True)
    .rename({'total_wins': 'Exp. Wins',
             'wc_pct': 'Wildcard (%)',
             'div_pct': 'Div. Winner (%)',
             'playoff_pct': 'Make Playoffs (%)'}, axis=1)
  )
  logger.info(f'Playoff simulation results (n_sim={n_sims})')
  pd.set_option('precision', 3)
  pd.set_option('max_columns', 20)
  pd.set_option('display.expand_frame_repr', False)
  print(df_sim_results[['firstName', 'lastName', 'Exp. Wins', 'Wildcard (%)',
                        'Div. Winner (%)', 'Make Playoffs (%)']].to_string(index=False))
  return


def run_simulation(teams, schedule, week, reg_season, n_sims, n_wc, year):
  """Run simulations, aggregate and plot results

  :param teams: data frame with team data
  :param schedule: data frame with schedule data
  :param week: current week
  :param reg_season: length of regular season
  :param n_sims: number of simulations to run
  :param n_wc: number of wild card spots
  :param year: current year
  :return: results of simulation
  """
  logger.info(f'Generating simulated scores for {n_sims} seasons')
  df_sim = generate_simulations(
    teams=teams,
    schedule=schedule,
    week=week,
    reg_season=reg_season,
    n_sims=n_sims)
  logger.info('Summarising statistics in each simulated season')
  df_sum = summarise_simulations(
    df_sim=df_sim,
    teams=teams)
  logger.info('Calculating division winners and wildcards in each simulated season')
  df_div_winners = get_div_winners(
    df_sim=df_sum)
  df_wc = get_wildcards(
    df_sim=df_sum,
    df_div_winners=df_div_winners,
    n_wc=n_wc)
  logger.info('Summarising simulated playoff percentages for plotting')
  df_plot = calc_playoff_pct_by_iter(
    teams=teams,
    df_div_winners=df_div_winners,
    df_wc=df_wc,
    max_iters=n_sims,
    step_size=int(n_sims/100))
  df_plot = unnest(
    df=df_plot,
    explode=['x_vals', 'wc_pct', 'div_pct'])
  logger.info('Plotting playoff simulation results')
  plot_simulation_results(
    df_plot=df_plot,
    week=week,
    year=year)
  return df_plot.query('x_vals==x_vals.max()')[['team_id', 'wc_pct', 'div_pct']].reset_index(drop=True)


def generate_simulations(teams, schedule, week, reg_season, n_sims):
  """Generate simulated scores for rest of season

  :param teams: data frame with team data
  :param schedule: data frame with schedule data
  :param week: current week
  :param reg_season: length of regular season
  :param n_sims: number of simulations to run
  :return: data frame with simulated scores
  """
  # Get remaining schedule
  df_remaining = (
    schedule[['home_id', 'away_id', 'matchupPeriodId']]
    .query(f'matchupPeriodId > {week} & matchupPeriodId <= {reg_season}')
    .reset_index(drop=True))
  # Add in score profiles
  df_remaining['home_score_fit'] = df_remaining.apply(
    lambda x: teams[teams.get('team_id') == x.get('home_id')].get('score_fit').values[0], axis=1
  )
  df_remaining['away_score_fit'] = df_remaining.apply(
    lambda x: teams[teams.get('team_id') == x.get('away_id')].get('score_fit').values[0], axis=1
  )
  # Add in simulated scores
  df_remaining['home_scores'] = df_remaining.apply(
    lambda x: norm.rvs(x.home_score_fit[0], x.home_score_fit[1], n_sims).tolist(), axis=1
  )
  df_remaining['away_scores'] = df_remaining.apply(
    lambda x: norm.rvs(x.away_score_fit[0], x.away_score_fit[1], n_sims).tolist(), axis=1
  )
  return df_remaining


def unnest(df, explode):
  """Unnest columns that have lists into a row for each element

  :param df: input data frame with nested columns
  :param explode: list of columns to explode
  :return: data frame with long format
  """
  idx = df.index.repeat(df[explode[0]].str.len())
  # Get index in each list we want to explode
  idx2 = np.array([list(range(len(x))) for x in df[explode[0]]]).flatten()
  # Explode each column in 'explode', and concat into columns
  df1 = pd.concat([pd.DataFrame({x: np.concatenate(df[x].values)}) for x in explode], axis=1)
  # Add in column for labeling index in exploded lists
  df1 = pd.concat([df1, pd.DataFrame({'iteration': idx2})], axis=1)
  df1.index = idx
  return df1.join(df.drop(explode, 1), how='left')


def summarise_simulations(df_sim, teams):
  """Convert the wide format simulations into long format

  summarise each iteration
  :param df_sim: input data frame with simulated scores
  :param teams: data frame with team data
  :return: long format summarised by iteration
  """
  df_sim_long = unnest(df=df_sim, explode=['home_scores', 'away_scores']).reset_index(drop=True)
  # Add in indicators for win/loss
  df_sim_long['home_wins'] = df_sim_long['home_scores'] > df_sim_long['away_scores']
  df_sim_long['away_wins'] = df_sim_long['away_scores'] > df_sim_long['home_scores']
  # Aggregate by home/away and iteration
  df_home_sum = (
    df_sim_long
    .groupby(['home_id', 'iteration'], as_index=False)
    .agg({'home_scores': 'sum', 'home_wins': 'sum'})
    .astype(float)
    .rename({'home_id': 'team_id'}, axis=1)
  )
  df_away_sum = (
    df_sim_long
    .groupby(['away_id', 'iteration'], as_index=False)
    .agg({'away_scores': 'sum', 'away_wins': 'sum'})
    .astype(float)
    .rename({'away_id': 'team_id'}, axis=1)
  )
  # Combine home away summaries
  df_sim_sum = pd.merge(df_home_sum,
                        df_away_sum,
                        on=['team_id', 'iteration'], how='outer').fillna(0).reset_index(drop=True)
  # Add in season stats
  df_sim_sum = pd.merge(df_sim_sum,
                        teams[['team_id', 'divisionId', 'wins', 'points_for']],
                        on=['team_id']).reset_index(drop=True)
  # Add in total wins/points
  df_sim_sum['tot_wins'] = df_sim_sum['home_wins'] + df_sim_sum['away_wins'] + df_sim_sum['wins']
  df_sim_sum['tot_pts'] = df_sim_sum['home_scores'] + df_sim_sum['away_scores'] + df_sim_sum['points_for']
  # Drop unnecessary columns
  df_sim_sum = df_sim_sum.drop(['home_scores', 'home_wins', 'away_scores', 'away_wins', 'wins', 'points_for'], 1)
  return df_sim_sum


def get_div_winners(df_sim):
  """Calculate division winners with summarised simulation data

  :param df_sim: data frame with simulated scores summarised by iteration
  :return: data frame with division winners per iteration
  """
  return (
    df_sim
    .sort_values(by=['tot_wins', 'tot_pts'], ascending=[False, False])
    .groupby(['iteration', 'divisionId'])
    .head(1)
    .sort_values(by=['divisionId', 'iteration'])
    .reset_index(drop=True)
  )


def get_wildcards(df_sim, df_div_winners, n_wc):
  """Calculate wildcards per simulation

  :param df_sim: simulated data
  :param df_div_winners: data frame with div winners in each iteration
  :param n_wc: number of wildcard positions open
  :return: data frame with wildcard teams per iteration
  """
  return (
    df_sim
    .merge(df_div_winners[['team_id', 'iteration']], on=['team_id', 'iteration'], how='left', indicator=True)
    .query('_merge=="left_only"')
    .drop('_merge', 1)
    .sort_values(by=['tot_wins', 'tot_pts'], ascending=[False, False])
    .groupby('iteration')
    .head(n_wc)
    .sort_values(by='iteration')
    .reset_index(drop=True)
  )


def calc_playoff_pct_by_iter(teams, df_div_winners, df_wc, max_iters, step_size):
  """Calculate percentage of times team makes playoffs as function of simulation iteration

  :param teams: data frame with team data
  :param df_div_winners: division winners by iteration
  :param df_wc: wildcards by iteration
  :param max_iters: number of simulations run
  :param step_size: how often to calculate rolling percentage
  :return: summarised data frame for plotting
  """
  df_plot = teams[['team_id', 'firstName', 'divisionId']].reset_index(drop=True)
  # Get list of iterations where each team is wildcard
  df_plot['it_wc'] = df_plot.apply(lambda x: df_wc.query(f'team_id == {x.team_id}').iteration.tolist(), axis=1)
  # Get list of iterations where each team is division winner
  df_plot['it_div'] = df_plot.apply(lambda x: df_div_winners.query(f'team_id == {x.team_id}').iteration.tolist(), axis=1)
  # Calculate rolling pct at specified step size
  df_plot['wc_pct'] = df_plot['it_wc'].apply(
    lambda x: [100*sum([xi < iter_checkpoint for xi in x])/float(iter_checkpoint)
               for iter_checkpoint in list(range(step_size, max_iters+1, step_size))]
  )
  df_plot['div_pct'] = df_plot['it_div'].apply(
    lambda x: [100*sum([xi < iter_checkpoint for xi in x])/float(iter_checkpoint)
               for iter_checkpoint in list(range(step_size, max_iters+1, step_size))]
  )
  # Drop the list of wc/div iterations by team
  df_plot = df_plot.drop(['it_wc', 'it_div'], 1)
  # Add in iteration counter for plotting
  df_plot['x_vals'] = df_plot['team_id'].apply(lambda x: list(range(step_size, max_iters+1, step_size)))
  return df_plot


def plot_simulation_results(df_plot, week, year):
  """Make wildcard and division winner plots by simulation number

  :param df_plot: data frame with summarised simulation information
  :param week: current week
  :param year: current season
  :return: None
  """
  # Calculate label positions
  df_plot_label_pos = (
    df_plot
    .query('x_vals==x_vals.max()')[['team_id', 'firstName', 'wc_pct', 'div_pct', 'x_vals']]
    .reset_index(drop=True))
  x_scale_factor = df_plot_label_pos.x_vals.max() / df_plot_label_pos.team_id.size
  df_plot_label_pos['wc_pct_pos'] = df_plot_label_pos.wc_pct.rank(method='first') * x_scale_factor
  df_plot_label_pos['div_pct_pos'] = df_plot_label_pos.div_pct.rank(method='first') * x_scale_factor
  # Create wildcard plot
  df_plot_label_pos
  p_wc = (
    ggplot(aes(x='x_vals',
               y='wc_pct',
               color='factor(team_id)',
               group='team_id'),
           data=df_plot) +
    geom_line() +
    geom_label(aes(label='firstName',
                   x='wc_pct_pos',
                   y='wc_pct',
                   color='factor(team_id)'),
               data=df_plot_label_pos,
               size=10) +
    labs(x='Simulation', y='Simulations Team is Wildcard (%)') +
    theme_bw() +
    guides(color=False) +
    ylim(0, 100)
  )
  # Create division winner plot
  p_div = (
    ggplot(aes(x='x_vals',
               y='div_pct',
               color='factor(team_id)',
               group='team_id'),
           data=df_plot) +
    geom_line() +
    geom_label(aes(label='firstName',
                   x='div_pct_pos',
                   y='div_pct',
                   color='factor(team_id)'),
               data=df_plot_label_pos,
               size=10) +
    labs(x='Simulation', y='Simulations Team is Div. Winner (%)') +
    theme_bw() +
    guides(color=False) +
    ylim(0, 100)
  )
  # Create directory to save plots
  out_dir = Path(f'output/{year}/week{week}')
  out_dir.mkdir(parents=True, exist_ok=True)
  # Create file names
  out_file_wc = out_dir / 'playoffs_wildcard_pct_by_simulation.png'
  out_file_div = out_dir / 'playoffs_division_pct_by_simulation.png'
  # Save plots
  warnings.filterwarnings('ignore')
  p_wc.save(out_file_wc, width=10, height=6, dpi=300)
  p_div.save(out_file_div, width=10, height=6, dpi=300)
  warnings.filterwarnings('default')
  logger.info(f'Playoff simulation plots saved to: \n\t>{out_file_wc}\n\t>{out_file_div}')


def calc_standings(teams, divisions, spots, week, reg_season):
  """Calculate the current playoff standings

  Division winners make it, then enough playoff teams to fill wildcard
  :param teams: data frame with team data
  :param divisions: dictionary of divisions
  :param spots: number of playoff spots
  :param week: current week
  :param reg_season: length of the regular season
  :return: None
  """
  df_standings = teams[['team_id', 'location', 'nickname', 'abbrev', 'firstName', 'lastName',
                        'divisionId', 'wins', 'points_for', 'points_against']].reset_index(drop=True)
  df_standings = pd.merge(df_standings, divisions[['divisionId', 'division']], on='divisionId').reset_index(drop=True)
  # Find division winners first
  df_div_winners = (
    df_standings
    .sort_values(by=['wins', 'points_for'], ascending=[False, False])
    .groupby('divisionId')
    .head(1)
    .reset_index(drop=True)
  )
  # Get wild cards
  df_wc = (
    df_standings
    .query(f'team_id not in {df_div_winners.team_id.tolist()}')
    .sort_values(by=['wins', 'points_for'], ascending=[False, False])
    .head(spots - len(divisions))
    .reset_index(drop=True)
  )
  df_standings['div_winner'] = df_standings.apply(
    lambda x: 1 if x.team_id in df_div_winners.team_id.tolist() else 0, axis=1
  )
  df_standings['wildcard'] = df_standings.apply(
    lambda x: 1 if x.team_id in df_wc.team_id.tolist() else 0, axis=1
  )
  # Get eliminated
  df_eliminated = (
    df_standings
    .query(f'team_id not in {df_div_winners.team_id.tolist()+df_wc.team_id.tolist()}')
    .query(f'{df_wc.tail(1).wins.values[0]} - wins  > {reg_season - week}')
    .reset_index(drop=True)
  )
  # Select columns for printing
  df_div_winners['spot'] = 'Division Winner'
  df_wc['spot'] = 'Wild Card'
  df_eliminated['spot'] = 'Eliminated'
  playoff_cols = ['firstName', 'lastName', 'wins', 'points_for', 'spot', 'division']
  df_playoff_spots = pd.concat([df_div_winners[playoff_cols], df_wc[playoff_cols]]).reset_index(drop=True)
  # Print the Current standings
  logger.info(f'Current Playoff Standings:\n{df_playoff_spots.to_string(index=False)}')
  logger.info(f'Teams Eliminated from Playoffs:\n{df_eliminated[playoff_cols].to_string(index=False)}')


def calc_exp_wins(teams, schedule, week, reg_season):
  """Calculate expected wins for rest of season for each team

  Use fitted normal distribution for each team, combine distributions
  and calculate cdf(0) for probability to win
  :param teams: data frame with teams and score profile
  :param schedule: data frame with schedule data
  :param week: current week
  :param reg_season: weeks in regular season
  """
  # Get remaining schedule
  df_remaining = schedule.query(f'matchupPeriodId > {week} & matchupPeriodId <= {reg_season}').reset_index(drop=True)
  # Add in score profiles
  df_remaining['home_score_fit'] = df_remaining.apply(
    lambda x: teams[teams.get('team_id') == x.get('home_id')].get('score_fit').values[0], axis=1
  )
  df_remaining['away_score_fit'] = df_remaining.apply(
    lambda x: teams[teams.get('team_id') == x.get('away_id')].get('score_fit').values[0], axis=1
  )
  # Calc prob home wins: subtract normal distributions and find cdf at 0
  df_remaining['p_home_wins'] = df_remaining.apply(
    lambda x: norm(x.away_score_fit[0] - x.home_score_fit[0],
                   np.sqrt(x.home_score_fit[1] ** 2 + x.away_score_fit[1])).cdf(0), axis=1
  )
  # Get expected home/away wins
  df_expected_home_wins = (
    df_remaining
    .groupby('home_id')
    .agg(home_wins=('p_home_wins', lambda x: sum(x)))
    .reset_index()
    .rename({'home_id': 'team_id'}, axis=1)
  )
  df_expected_away_wins = (
    df_remaining
    .groupby('away_id')
    .agg(away_wins=('p_home_wins', lambda x: sum(1-x)))
    .reset_index()
    .rename({'away_id': 'team_id'}, axis=1)
  )
  # Combine home/away expected results and calculate total wins
  df_expected = (
    pd.merge(df_expected_home_wins, df_expected_away_wins, on='team_id', how='outer')
    .reset_index(drop=True)
    .fillna(0)
  )
  df_expected['total_wins'] = df_expected.apply(lambda x: x.home_wins+x.away_wins, axis=1)
  return df_expected




