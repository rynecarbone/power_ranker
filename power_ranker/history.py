#!/usr/bin/env python

"""Collect and store fantasy football league history

    Note: primaryOwner is probably a better unique identifier, however in the few
    leagues I've seen it has occured that the same physical person has more than one
    primaryOwner id across years. I think this happens if the email/espn account changes.
    In all these cases team_id has stayed the same, so I use team_id-firstName-lastName as
    the unique identifier...
"""

import logging
import pandas as pd
from pathlib import Path
from .get_season_data import build_team_table, build_schedule_table, build_season_summary_table
from .utils import fetch_page

__author__ = 'Ryne Carbone'

logger = logging.getLogger(__name__)


def scrape_history(endpoint, params, cookies=None):
  """Scrape history stats from ESPN

  :param endpoint: history data endpoint
  :param params: api parameters
  :param cookies: cookies (for private league)
  :return: None
  """
  logger.info(f'Retrieving league history')
  # Set pandas precision
  pd.set_option('precision', 3)
  pd.set_option('max_columns', 20)
  pd.set_option('display.expand_frame_repr', False)
  # Scrape history
  try:
    h_data = fetch_page(
      endpoint=endpoint,
      params=params,
      cookies=cookies,
      use_soup=False,
      use_json=True
    )
  except Exception as e:
    logger.exception(e)
    raise
  # If data frame is empty, this is the first year for the league
  if not h_data:
      logger.warning('No league history found! History page will be empty')
      table = '<div class="text-center"><h3>Oh, my sweet summer child, there is no league history</h3></div>'
      return '', '', '', table
  # List which seasons are actually retrieved
  seasons_id = [data_y.get('seasonId') for data_y in h_data]
  logger.info(f'Retrieved league history for years {seasons_id}')
  # Get season schedule rules
  seasons_schedule_settings = [pd.Series(data_y.get('settings').get('scheduleSettings')) for data_y in h_data]
  # Final Regular season games
  seasons_final_reg_id = [settings_y.get('matchupPeriodCount') for settings_y in seasons_schedule_settings]
  # Get info about teams in each season
  seasons_teams = [build_team_table(data=data_y) for data_y in h_data]
  # Get each matchup and scores in each season
  seasons_schedule = [build_schedule_table(data=data_y) for data_y in h_data]
  # Build regular season summaries
  seasons_reg_summary = [build_season_summary_table(df_schedule=schedule_y, week=final_reg_id)
                         for (schedule_y, final_reg_id) in zip(seasons_schedule, seasons_final_reg_id)]
  # TODO: maybe add in 'start week' for season summary function?
  # Final scoring period
  #seasons_final_scoring_id = [max(pd.Series(settings_y.get('matchupPeriods'))[-1])
  #                            for settings_y in seasons_schedule_settings]
  #seasons_full_summary = [build_season_summary_table(df_schedule=schedule_y, week=final_scoring_id)
  #                        for (schedule_y, final_scoring_id) in zip(seasons_schedule, seasons_final_scoring_id)]
  # Add column for each year
  for y, teams in zip(seasons_id, seasons_teams):
    teams['year'] = y
  # Merge team info with regular season stats
  reg_cols = ['team_id', 'points_for', 'points_against', 'wins', 'games', 'agg_wins', 'agg_games', 'agg_wpct']
  df_reg_full = [pd.merge(teams, reg_summary[reg_cols].reset_index(drop=True), on='team_id')
                 for (teams, reg_summary) in zip(seasons_teams, seasons_reg_summary)]
  # Concat all teams data frames
  df_reg_full = pd.concat(df_reg_full).reset_index(drop=True)
  # Create summary tables
  medal_count = make_overall_medal_count(df=df_reg_full)
  overall_table = make_overall_standings(df=df_reg_full)
  option_menu, all_tables = make_history_table(df=df_reg_full)
  # Return tables
  return option_menu, all_tables, overall_table, medal_count


def make_history_table(df):
    """Create html table for each year in league history

    :param df: data frame with scores from every year
    """
    # Columns to output
    cols = ['Rank', 'Team', 'Abbrev', 'Owner', 'REC', 'WPCT', 'AWP', 'PF', 'PA', 'PF/G', 'PA/G', 'DIFF', 'year']
    # Standings by year
    df = df.sort_values(['year', 'rankCalculatedFinal']).reset_index(drop=True)
    df['Rank'] = df.apply(lambda x: x.get('rankCalculatedFinal'), axis=1)
    df['Team'] = df.apply(lambda x: f'{x.get("location")} {x.get("nickname")}', axis=1)
    df['Abbrev'] = df.apply(lambda x: f'{x.get("abbrev")}', axis=1)
    df = get_columns_for_table(df=df)
    df = df[cols]
    # Add in empty first column for adding icons to later
    df.insert(loc=0, column='', value='')
    # Make html tables and combine into one long string
    all_tables = ''
    groups = df.groupby('year')
    keys = sorted(list(groups.groups.keys()), reverse=True)
    for k, g in groups:
        table = g.drop('year', axis=1).to_html(
            index=False,
            border=0,
            classes="table",
            table_id="history_table_{}".format(k))
        style = 'style="display:none"' if k != max(keys) else ''
        table = f'<div id="{k}" class="col-md-12 table-responsive season" {style}>' + table + '</div>'
        all_tables += table
    # Build options dropdown menu for selection which history table
    option_menu = ''.join(['<option value="{}">{} Season</option>'.format(k, k) for k in keys])
    return option_menu, all_tables


def make_overall_standings(df):
    """Make overall regular season summary table

    :param df: data frame with regular season data for each team
    :return: html table
    """
    # Summary of all regular season
    df_sum = (
      df[['team_id', 'firstName', 'lastName', 'points_for', 'points_against', 'wins', 'games', 'agg_wins', 'agg_games']]
      .groupby(['team_id', 'firstName', 'lastName'])
      .agg('sum')
      .reset_index(drop=False)
    )
    # Calculate columns
    df_sum = get_columns_for_table(df=df_sum)
    # Select columns and sort
    sum_cols = ['Owner', 'W', 'L', 'WPCT', 'AWP', 'PF', 'PA', 'PF/G', 'PA/G', 'DIFF']
    df_sum = df_sum[sum_cols].sort_values(['WPCT', 'AWP'], ascending=[False, False])
    # Convert to html
    df_sum = df_sum.to_html(index=False, border=0, classes="table table-striped", table_id="aggregate_regular_season")
    return df_sum


def get_columns_for_table(df):
    """Calculate columns for summary table
    Team, Owner, W, L, WPCT, AWP, PF, PA, PF/G, PA/G, DIFF

    :param df: data frame with wins, agg_wins, team names, ranks, points
    :return: data frame with calcualted columns
    """
    df['Owner'] = df.apply(lambda x: f'{x.get("firstName")} {x.get("lastName")}', axis=1)
    df['W'] = df.apply(lambda x: x.get('wins'), axis=1).astype(int)
    df['L'] = df.apply(lambda x: x.get('games') - x.get('wins'), axis=1).astype(int)
    df['REC'] = df.apply(lambda x: f'{x.get("W")}-{x.get("L")}', axis=1)
    df['WPCT'] = df.apply(lambda x: f'{x.get("wins")/x.get("games"):.3f}', axis=1)
    df['AWP'] = df.apply(lambda x: f'{x.get("agg_wins")/x.get("agg_games"):.3f}', axis=1)
    df['PF'] = df.apply(lambda x: f'{x.get("points_for"):.1f}', axis=1)
    df['PA'] = df.apply(lambda x: f'{x.get("points_against"):.1f}', axis=1)
    df['PF/G'] = df.apply(lambda x: f'{x.get("points_for")/x.get("games"):.1f}', axis=1)
    df['PA/G'] = df.apply(lambda x: f'{x.get("points_against")/x.get("games"):.1f}', axis=1)
    df['DIFF'] = df.apply(lambda x: f'{(x.get("points_for") - x.get("points_against"))/x.get("games"):.1f}', axis=1)
    return df


def make_overall_medal_count(df):
    """Make summary of trophy counts

    :param df: data frame with teams and final places by year
    :return: html table
    """
    # Final rankings summary
    place_cols = ['team_id', 'firstName', 'lastName', 'rankCalculatedFinal', 'year']
    last_place = (df.sort_values('rankCalculatedFinal', ascending=False).drop_duplicates('year')[place_cols])
    trophies = df.query('rankCalculatedFinal <=3')[place_cols]
    all_owners = df[['team_id', 'firstName', 'lastName']].drop_duplicates().reset_index(drop=True)
    all_owners['first'] = all_owners.apply(lambda x: trophies.query(f'rankCalculatedFinal==1 & team_id == "{x.get("team_id")}" & firstName == "{x.get("firstName")}" & lastName=="{x.get("lastName")}"').get('year').size, axis=1)
    all_owners['second'] = all_owners.apply(lambda x: trophies.query(f'rankCalculatedFinal==2 & team_id == "{x.get("team_id")}" & firstName == "{x.get("firstName")}" & lastName=="{x.get("lastName")}"').get('year').size, axis=1)
    all_owners['third'] = all_owners.apply(lambda x: trophies.query(f'rankCalculatedFinal==3 & team_id == "{x.get("team_id")}" & firstName == "{x.get("firstName")}" & lastName=="{x.get("lastName")}"').get('year').size, axis=1)
    all_owners['last'] = all_owners.apply(lambda x: last_place.query(f'team_id == "{x.get("team_id")}" & firstName == "{x.get("firstName")}" & lastName=="{x.get("lastName")}"').get('year').size, axis=1)
    all_owners['PTS'] = all_owners.apply(lambda x: x['first']*3 + x['second']*2 + x['third'] - x['last'], axis=1)
    all_owners['Owner'] = all_owners.apply(lambda x: f'{x.get("firstName")} {x.get("lastName")}', axis=1)
    all_owners = all_owners[['Owner', 'first', 'second', 'third', 'last', 'PTS']]
    trophy_tooltip = '''
    <span class='footnote' data-placement="top" data-toggle="tooltip" title='
    <table class="table table-responsive">
        <thead> <tr style="text-align: right;">
            <th><i class="fa fa-trophy" style="color: #f1c40f"></i></th>
            <th><i class="fa fa-trophy" style="color: #95a5a6"></i></th>
            <th><i class="fa fa-trophy" style="color: #965A38"></i></th>
            <th>&#128701;</th></tr>
        </thead>
        <tbody><tr><td>3</td><td>2</td><td>1</td><td>-1</td></tr></tbody>
    </table>'></span>'''
    new_cols = ['Owner',
                '<i class="fa fa-trophy" style="color: #f1c40f"></i>',
                '<i class="fa fa-trophy" style="color: #95a5a6"></i>',
                '<i class="fa fa-trophy" style="color: #965A38"></i>',
                '&#128701;',
                f'PTS{trophy_tooltip}']
    all_owners.columns = new_cols
    all_owners = all_owners.to_html(index=False,
                                    border=0,
                                    classes="table table-striped",
                                    table_id="medal_count",
                                    escape=False)
    return all_owners


