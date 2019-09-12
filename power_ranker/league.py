#!/usr/bin/env python

"""Main class to handle scraped league stats"""

import logging
import configparser
import pandas as pd
from .get_season_data import(
  build_team_table,
  build_schedule_table,
  build_season_summary_table
)
from .settings import Settings
from .two_step_dom import get_two_step_dom_ranks
from .lsq import get_ranks_lsq
from .colley import get_colley_ranks
from .utils import (
  calc_sos,
  calc_luck,
  calc_cons,
  calc_power,
  save_ranks,
  calc_tiers,
  fetch_page)
from .web.radar import save_team_radar_plots
from .web.website import generate_web
from .web.power_plot import make_power_plot
from .playoff_odds import calc_playoffs
from .history import scrape_history

__author__ = 'Ryne Carbone'

logger = logging.getLogger(__name__)


class League:
  """Given ESPN public league information, collects stats and creates
     team objects for all teams"""
  def __init__(self, config_file='default_config.cfg'):
    self.league_id = ''
    self.year = ''
    self.week = ''
    self.teams = []
    self.config_file = config_file
    self.base = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons'
    self.base_history = 'https://fantasy.espn.com/apis/v3/games/ffl/leagueHistory'
    self.params = {'view': ['mTeam', 'mMatchup', 'mSettings']}
    self.s2 = None
    self.swid = None
    self._scrape_league()

  def __repr__(self):
    return f'League {self.settings.league_name} ({self.league_id}), {self.year} Season'

  def _scrape_league(self):
    """Scrape league info"""
    # Read config
    self._get_config()
    self._set_basic_info()
    # Scrape info
    try:
      data = fetch_page(
        endpoint=self.endpoint,
        params=self.params,
        cookies=self.cookies,
        use_soup=False,
        use_json=True
      )
    except Exception as e:
      logger.exception(e)
      raise
    self._scrape_season(data)
    self._scrape_settings(data)

  def _get_config(self):
    """Read configuration file"""
    logger.info(f'Parsing config file: {self.config_file}')
    config = configparser.RawConfigParser(allow_no_value=True)
    config.read(self.config_file)
    self.config = config
  
  def _set_basic_info(self):
    """Set league id, week, year"""
    self.league_id = self.config['League Info'].getint('league_id')
    self.year = self.config['League Info'].getint('year')
    self.week = self.config['League Info'].getint('week')
    self.endpoint = f'{self.base}/{self.year}/segments/0/leagues/{self.league_id}'
    self.endpoint_history = f'{self.base_history}/{self.league_id}'
    self.s2 = self.config['Private League'].get('s2', None)
    self.swid = self.config['Private League'].get('swid', None)
    # Set cookies 
    self.cookies = {'espn_s2': self.s2, 'SWID': self.swid} if (self.s2 and self.swid) else None
    logger.debug(
      f'Parsed and saved basic info: league_id: {self.league_id}, year: {self.year}, '
      f'week: {self.week}, cookies: {self.cookies}'
    )

  def _scrape_season(self, data):
    """Scrape data for season"""
    self.df_teams = build_team_table(data)
    self.df_schedule = build_schedule_table(data)
    self.df_season_summary = build_season_summary_table(df_schedule=self.df_schedule, week=self.week)
    self.df_ranks = self.df_season_summary[['team_id', 'overall']].reset_index(drop=True)

  def _scrape_settings(self, data):
    """Scrape league settings info"""
    self.settings = Settings(data)

  def _calc_dom(self, sq_weight=0.25, decay_penalty=0.5):
    """Calculate the two step dominance rankings"""
    dom = get_two_step_dom_ranks(self.df_schedule, self.week, sq_weight=sq_weight, decay_penalty=decay_penalty)
    self.df_ranks = (
      pd.merge(self.df_ranks, dom, on='team_id', how='left')
      .sort_values('team_id')
      .reset_index(drop=True)
    )

  def _calc_lsq(self, B_w=30., B_r=35., dS_max=35., beta_w=2.2, show_plot=False):
    """Calculate rankings based on iterative lsq method"""
    lsq = get_ranks_lsq(
      df_teams=self.df_teams,
      df_schedule=self.df_schedule,
      year=self.year,
      week=self.week,
      B_w=B_w, B_r=B_r, dS_max=dS_max, beta_w=beta_w, show=show_plot
    )
    self.df_ranks = (
      pd.merge(self.df_ranks, lsq, on='team_id', how='left')
      .sort_values('team_id')
      .reset_index(drop=True)
    )

  def _calc_colley(self, printMatrix=False):
    """Calculates and assigns colley rankings for each team in the league"""
    col = get_colley_ranks(df_schedule=self.df_schedule, week=self.week, printMatrix=printMatrix)
    self.df_ranks = (
      pd.merge(self.df_ranks, col, on='team_id', how='left')
      .sort_values('team_id')
      .reset_index(drop=True)
    )

  def _calc_sos(self, rank_power=2.37):
    """Calculates the strength of schedule based on the lsq rankings"""
    self.df_ranks = calc_sos(
      df_schedule=self.df_schedule,
      df_ranks=self.df_ranks,
      week=self.week,
      rank_power=rank_power
    )

  def _calc_luck(self, awp_weight=0.5):
    """Calculates the luck index"""
    luck = calc_luck(
      df_schedule=self.df_schedule,
      df_season_summary=self.df_season_summary,
      week=self.week,
      awp_weight=awp_weight
    )
    self.df_ranks = (
      pd.merge(self.df_ranks, luck, on='team_id', how='left')
      .sort_values('team_id')
      .reset_index(drop=True)
    )

  def _calc_cons(self):
    """Calculate the consistency index"""
    self.df_ranks = calc_cons(self.df_ranks, self.df_schedule, self.week)

  def _calc_power(self, w_dom=0.18, w_lsq=0.18, w_col=0.18, w_awp=0.18,
                  w_sos=0.06, w_luck=0.06, w_cons=0.10, w_strk=0.06):
    """Calculates the final weighted power index"""
    self.df_ranks = calc_power(
      df_ranks=self.df_ranks,
      df_season_summary=self.df_season_summary,
      w_dom=w_dom,
      w_lsq=w_lsq,
      w_col=w_col,
      w_awp=w_awp,
      w_sos=w_sos,
      w_luck=w_luck,
      w_cons=w_cons,
      w_strk=w_strk
    )

  def _calc_tiers(self, bw=0.09, order=4, show_plot=False):
    """Calculates tiers based on the power rankings"""
    self.df_ranks = calc_tiers(
      df_ranks=self.df_ranks,
      year=self.year,
      week=self.week,
      bw=bw,
      order=order,
      show=show_plot)

  def _save_ranks(self):
    """Save the power rankings, optionally calculate change from previous week"""
    ranks_change = save_ranks(self.df_ranks, self.year, self.week)
    if ranks_change is not None:
      self.df_ranks = (
        pd.merge(self.df_ranks, ranks_change, on='team_id', how='left')
          .sort_values('team_id')
          .reset_index(drop=True)
      )
    else:
      self.df_ranks['d_power'] = 0
      self.df_ranks['d_overall'] = 0
      self.df_ranks['d_tier'] = 0

  def print_rankings(self):
    """Print table of metrics and final power rankings"""
    print(f'\nWeek {self.week} Power Rankings\n======================')
    pd.set_option('precision', 3)
    pd.set_option('max_columns', 20)
    pd.set_option('display.expand_frame_repr', False)
    # Get team names
    df_out = (
      pd.merge(self.df_teams[['team_id', 'firstName', 'lastName']],
               self.df_ranks, on='team_id')
      .reset_index(drop=True)
    )
    # Get aggregate win pct
    df_out = (
      pd.merge(df_out, self.df_season_summary[['team_id', 'agg_wpct', 'wins', 'games', 'points_for', 'points_against']])
      .sort_values('power', ascending=False)
      .reset_index(drop=True)
      .rename({'agg_wpct': 'awp', 'points_for': 'PF', 'points_against': 'PA'}, axis=1)
    )
    # Combine names
    df_out['Team'] = df_out.apply(lambda x: f'{x.get("firstName")} {x.get("lastName")}', axis=1)
    # Add record
    df_out['rec'] = df_out.apply(lambda x: f'{int(x.get("wins"))}-{int(x.get("games"))-int(x.get("wins"))}', axis=1)
    # Convert changes to strings
    df_out[['d_power', 'd_overall', 'd_tier']] = (
      df_out[['d_power', 'd_overall', 'd_tier']]
      .applymap(lambda x: f'(+{abs(x)}) ' if x > 0 else f'(-{abs(x)}) ' if x < 0 else '')
    )
    # Add in string changes next to rankings
    df_out['#'] = df_out.get('power').rank(ascending=False).astype(int)
    df_out['#'] = df_out.apply(lambda x: f'{x.get("d_power")}{x.get("#"):2}', axis=1)
    df_out['overall'] = df_out.apply(lambda x: f'{x.get("d_overall")}{x.get("overall"):2}', axis=1)
    df_out['tier'] = df_out.apply(lambda x: f'{x.get("d_tier")}{x.get("tier")}', axis=1)
    print(df_out[['Team', 'rec', '#', 'power', 'lsq', 'col', 'dom', 'awp',
                  'sos', 'luck', 'cons', 'tier', 'PF', 'PA', 'overall']].to_string(index=False))

  def get_power_rankings(self):
    """
    Get the power rankings for the specified week
    Configuration for all the metrics is passed via config
    Default values are set if they are missing from config file
    If week is passed, rankings are updated for that week number
    """
    logger.info('Calculating power rankings')
    # Calculate two-step dominance rankings
    self._calc_dom(
      sq_weight     = self.config['2SD'].getfloat('sq_weight', 0.25),
      decay_penalty = self.config['2SD'].getfloat('decay_penalty', 0.5)
    )
    # Calculate the least squares rankings
    self._calc_lsq(
      B_w       = self.config['LSQ'].getfloat('B_w', 30.),
      B_r       = self.config['LSQ'].getfloat('B_r', 35.),
      dS_max    = self.config['LSQ'].getfloat('dS_max', 35.),
      beta_w    = self.config['LSQ'].getfloat('beta_w', 2.2),
      show_plot = self.config['LSQ'].getboolean('show_plot', False)
    )
    # Calculate Colley rankings
    self._calc_colley(printMatrix = self.config['Colley'].getboolean('printMatrix', False))
    # Calculate SOS
    self._calc_sos(rank_power = self.config['SOS'].getfloat('rank_power', 2.37))
    # Calculate Luck index
    self._calc_luck(awp_weight = self.config['Luck'].getfloat('awp_weight', 0.5))
    # Calculate the Consistency index
    self._calc_cons()
    # Calculate final power rankings
    self._calc_power(
      w_dom  = self.config['Power'].getfloat('w_dom', 0.18),
      w_lsq  = self.config['Power'].getfloat('w_lsq', 0.18),
      w_col  = self.config['Power'].getfloat('w_col', 0.18),
      w_awp  = self.config['Power'].getfloat('w_awp', 0.18),
      w_sos  = self.config['Power'].getfloat('w_sos', 0.06),
      w_luck = self.config['Power'].getfloat('w_luck', 0.06),
      w_cons = self.config['Power'].getfloat('w_cons', 0.10),
      w_strk = self.config['Power'].getfloat('w_strk', 0.06)
    )
    # Get Tiers
    self._calc_tiers(
      bw        = self.config['Tiers'].getfloat('bw', 0.09),
      order     = self.config['Tiers'].getint('order', 4),
      show_plot = self.config['Tiers'].getboolean('show_plot', False)
    )
    # Calculate change from previous week
    self._save_ranks()
    # Print Sorted team
    self.print_rankings()
    # Calc the playoff odds
    # FIXME not updated yet
    #do_playoffs = self.config['Playoffs'].getboolean('doPlayoffs',False)
    #if do_playoffs:
    #  calc_playoffs(self.teams, self.year, self.week, self.settings,
    #                n_sims = self.config['Playoffs'].getint('num_simulations', 200000))

  def make_website(self):
    """Creates website based on current power rankings. Must run get_power_rankings() first"""
    doSetup = self.config['Web'].getboolean('doSetup', True)
    # Make Radar plots of each teams stats
    logger.info('Creating radar plots to summarize team stats')
    Y_LOW  = [float(yl.strip()) for yl in self.config['Radar'].get('Y_LOW').split(',')]
    Y_HIGH = [float(yh.strip()) for yh in self.config['Radar'].get('Y_HIGH').split(',')]
    save_team_radar_plots(
      df_rank=self.df_ranks,
      df_season_summary=self.df_season_summary,
      year=self.year,
      week=self.week,
      Y_LOW=Y_LOW,
      Y_HIGH=Y_HIGH)
    # Make welcome page power plot
    make_power_plot(
      df_ranks=self.df_ranks,
      df_schedule=self.df_schedule,
      df_teams=self.df_teams,
      year=self.year,
      week=self.week)
    # Generate html files for team and summary pages
    generate_web(
      df_teams=self.df_teams,
      df_ranks=self.df_ranks,
      df_season_summary=self.df_season_summary,
      df_schedule=self.df_schedule,
      year=self.year,
      week=self.week,
      league_id=self.league_id,
      league_name=self.settings.league_name,
      settings=self.settings,
      endpoint_history=self.endpoint_history,
      params=self.params,
      cookies=self.cookies,
      doSetup=doSetup
    )


