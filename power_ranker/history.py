#!/usr/bin/env python

"""Collect and store fantasy football league hisory

FIXME: New history endpoint: 'https://fantasy.espn.com/apis/v3/games/ffl/leagueHistory/'
"""

import logging
import pandas as pd
from pathlib import Path
from .utils import fetch_page

__author__ = 'Ryne Carbone'

logger = logging.getLogger(__name__)

history_endpoint = 'https://fantasy.espn.com/apis/v3/games/ffl/leagueHistory/'


def scrape_history(league_id, year, cookies=None):
  """Scrape from the ESPN league history page
  
  FIXME need to decide how to pass cookies for both requests
  :param league_id: unique espn league id 
  :param year: (int) current league year
  :param cookies: s2/swid dict for accessing private league
  :return: None, saves output to csv
  """
  logger.info('Beginning league history scraping,')
  try:
    history_page = fetch_page(league_id=league_id, year=(year-1), 
                              cookies=cookies, ENDPOINT=history_endpoint)
  except Exception as e:
    logger.exception(e)
    raise(e)
  # Get list of previous years for league
  past_seasons = history_page.find_all(id='seasonHistoryMenu')
  # If unable to find list, save empty data frame
  if not past_seasons:
    logger.warning('No league history found!')
    # Write an empty csv
    save_dataframe_to_csv(df=pd.DataFrame(), 
                          dest=f'output/{year}/history', 
                          f_name='history.csv')
    return
  # Parse history menu opions to get previous years
  years = sorted([
    opt.get('value')
    for opt in past_seasons[0].find_all('option')
    if int(opt.get('value')) < year
  ])
  df_season_list = []
  logger.info(f'Retrieving league history for years: {years} (league_id: {league_id})')
  # Loop over each year, grab the table 
  for y in years:
    try:
      history_page = fetch_page(league_id=league_id, year=y, 
                                cookies=cookies, ENDPOINT=history_endpoint, use_soup=False)
    except Exception as e:
      logger.exception(e)
      raise(e)
    # Get standings for this year, use row_index=1 as header
    html_table_list = pd.read_html(history_page, header=1)
    # Returns a list, second item is table we want 
    if len(html_table_list) < 1:
      logger.warning(f'No league history found for year: {y} (league_id: {league_id})')
      continue
    df = html_table_list[1] 
    # Drop column 3 (NaN), row 0 (overall header)
    df = df.drop(columns='Unnamed: 3')
    # Add column for year
    df['season'] = [y for _ in range(len(df))]
    df_season_list.append(df)
  final_df = pd.concat(df_season_list, axis=0, ignore_index=True)
  # Save to output csv 
  save_dataframe_to_csv(df=final_df, 
                        dest=f'output/{year}/history', 
                        f_name='history.csv')


def save_dataframe_to_csv(df, dest, f_name):
  """Safely store dataframe to local csv
  
  :param df: dataframe with data
  :param dest: location to save csv 
  :param f_name: name of file
  :return: None
  """
  dest = Path(dest)
  # Create output directory file structure if it doesnt exist already 
  dest.mkdir(parents=True, exist_ok=True)
  out_file = dest / f_name
  df.to_csv(out_file)
  logger.info(f'Saved league history to local file: {out_file.resolve()}')


def make_history_table(year):
  """Read in the history csv and create html table

  :param year: current year
  :return: html tables with season history stats, and option menu
  """
  # Read in the history csv
  df= pd.read_csv(f'output/{year}/history/history.csv', index_col=0)
  # If data frame is empty, this is the first year for the league
  if df.empty:
    logger.warning('No league history found! History page will be empty')
    table = '<div class="text-center"><h3>Oh, my sweet summer child, there is no league history</h3></div>'
    return '', '', '', table
  # Fix owner column (FIXME do I want to be more careful here?)
  df['OWNER(S)'] = df['OWNER(S)'].apply(lambda x: x.split(',')[0].title())
  # Add in empty first column for adding icons to later
  df.insert(loc=0, column='', value='')
  # Make html tables and combine into one long string
  all_tables = ''
  groups = df.groupby('season')
  keys = sorted(list(groups.groups.keys()), reverse=True)
  for k, g in groups:
    table = g.drop('season', axis=1).to_html(index=False, 
                                             border=0,
                                             classes="table",
                                             table_id="history_table_{}".format(k))
    style = 'style="display:none"' if k!=max(keys) else ''
    table = f'<div id="{k}" class="col-md-12 table-responsive season" {style}>' +\
            table + '</div>'
    all_tables += table
  # Build options dropdown menu for selection which history table
  option_menu = ''.join(['<option value="{}">{} Season</option>'.format(k, k) 
                         for k in keys])
  overall_table = make_overall_standings(df=df)
  medal_count = make_overall_medal_count(df=df)
  return option_menu, all_tables, overall_table, medal_count


def make_overall_standings(df):
  """Create aggregate table for regular season
  
  :param df: input df with regular season and final standings
  :return: tables summarize aggregate stats for reg season 
  """
  df['W'] = df['REC'].apply(lambda x: int(x.split('-')[0]))
  df['L'] = df['REC'].apply(lambda x: int(x.split('-')[1]))
  summary = df.groupby('OWNER(S)').agg({'W':'sum', 'L':'sum','PF':'sum', 'PA':'sum', 
                                        'PF/G':'mean', 'PA/G':'mean', 'DIFF':'mean'})
  wpct = summary.apply(lambda x: x['W']/(x['L']+x['W']), axis=1)
  summary.insert(2, 'PCT', wpct)
  summary = summary.round({'PF/G':2,'PA/G':2, 'DIFF':2, 'PCT':3})
  summary.insert(0, 'OWNER(S)', summary.index)
  return summary.to_html(index=False, border=0, classes="table table-striped", table_id="aggregate_regular_season")


def make_overall_medal_count(df):
  """Create aggregate table for post-season medal count"""
  df['First'] = df['RANK'].apply(lambda x: 1 if x==1 else 0)
  df['Second'] = df['RANK'].apply(lambda x: 1 if x==2 else 0)
  df['Third'] = df['RANK'].apply(lambda x: 1 if x==3 else 0)
  df['NumTeams'] = df.groupby('season')['RANK'].transform(max)
  df['Last'] = df.apply(lambda x: 1 if x['RANK'] == x['NumTeams'] else 0, axis=1)
  summary = df.groupby('OWNER(S)').agg({'First':'sum', 'Second':'sum','Third':'sum','Last':'sum'})
  summary['PTS'] = summary.apply(lambda x: x['First']*3 + x['Second']*2 + x['Third'] - x['Last'], axis=1)
  trophy_tooltip='''<span class='footnote' data-placement="top" data-toggle="tooltip" title='
		<table class="table table-responsive">
			<thead> <tr style="text-align: right;">
    		<th><i class="fa fa-trophy" style="color: #f1c40f"></i></th>
    		<th><i class="fa fa-trophy" style="color: #95a5a6"></i></th>
    		<th><i class="fa fa-trophy" style="color: #965A38"></i></th>
    		<th>&#128701;</th></tr>
      </thead>
		  <tbody><tr><td>3</td>
                 <td>2</td>
							   <td>1</td>
							   <td>-1</td></tr>
      </tbody>
		</table>'></span>'''
  new_cols = ['<i class="fa fa-trophy" style="color: #f1c40f"></i>',
              '<i class="fa fa-trophy" style="color: #95a5a6"></i>',
              '<i class="fa fa-trophy" style="color: #965A38"></i>',
              '&#128701;',
              f'PTS{trophy_tooltip}']
  summary.columns = new_cols
  summary.insert(0, 'OWNER(S)', summary.index)
  return summary.to_html(index=False, border=0, classes="table table-striped", table_id="medal_count", escape=False)
