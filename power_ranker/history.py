import os
import requests
import json
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path

BASE = 'http://games.espn.com/ffl'
ENDPOINT = 'tools/finalstandings'

def scrape_history(league_id, year, cookies=None):
  """Scrape from the ESPN league history page
  
  FIXME need to decide how to pass cookies for both requests
  :param league_id: unique espn league id 
  :param year: (int) current league year
  :param cookies: s2/swid dict for accessing private league
  :return: None, saves output to csv
  """
  # Scrape most recent league history page if it exists 
  params = {'leagueId': league_id,
            'seasonId': year-1}
  r = requests.get(f'{BASE}/{ENDPOINT}', params=params, cookies=cookies)
  s = BeautifulSoup(r.content, features='lxml')
  # Get list of years for league
  past_seasons = s.find_all(id='seasonHistoryMenu')
  if not past_seasons:
    print('No league history found!')
    # FIXME need to write empty csv
    return
  years = sorted([
    opt.get('value')
    for opt in past_seasons[0].find_all('option')
    if int(opt.get('value')) != year
  ])
  # Loop over each year, grab the table 
  print(f'\nRetrieving league history for years: {years}\n')
  df_season_list = []
  for y in years:
    params['seasonId'] = y
    r = requests.get(f'{BASE}/{ENDPOINT}', params=params, cookies=cookies)
    s = BeautifulSoup(r.content, features='lxml')
    # Get standings for this year
    # Returns a list, second item is table we want, use row index 1 as header
    df = pd.read_html(r.content, header=1)
    if len(df) < 1:
      print(f'\nNo league history found for year: {y}')
      continue
    df = df[1] 
    # Drop column 3 (NaN), row 0 (overall header)
    df = df.drop(columns='Unnamed: 3')
    # Add column for year
    df['season'] = [y for _ in range(len(df))]
    df_season_list.append(df)
  final_df = pd.concat(df_season_list, axis=0, ignore_index=True)
  # Save to output csv 
  out_dir = Path(f'output/{year}/history')
  out_dir.mkdir(parents=True, exist_ok=True)
  out_file = out_dir / 'history.csv'
  final_df.to_csv(out_file)
  print(f'Saved league history to local file: {out_file.resolve()}')

def make_history_table(year):
  """Read in the history csv and create html table

  :param year: current year
  :return: html tables with season history stats, and option menu
  """
  # Read in the history csv
  df= pd.read_csv(f'output/{year}/history/history.csv', index_col=0)
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
  return option_menu, all_tables

