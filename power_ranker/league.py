#!/usr/bin/env python

"""Main class to handle scraped league stats"""

import logging
import configparser
from operator import attrgetter
from .team import Team
from .settings import Settings
from .two_step_dom import TwoStepDom
from .lsq import LSQ
from .colley import Colley
from .utils import (fix_teamId, 
                    calc_sos, 
                    calc_luck,
                    calc_cons,
                    calc_power, 
                    save_ranks, 
                    calc_tiers,
                    fetch_page)
from .rank import norm_by_zscore, norm_rank, norm_by_max
from .web.radar import make_radar
from .web.website import generate_web
from .web.power_plot import make_power_plot
from .playoff_odds import calc_playoffs 
from .history import scrape_history

__author__ = 'Ryne Carbone'

logger = logging.getLogger(__name__)


#___________________
class League(object):
  '''Given ESPN public league information, collects stats and creates
     team objects for all teams'''
  def __init__(self, config_file='default_config.cfg'):
    self.league_id   = '' 
    self.year        = ''
    self.week        = ''
    self.teams       = []
    self.config_file = config_file
    self.ENDPOINT    = "http://games.espn.com/ffl/api/v2/leagueSettings"
    self.s2          = None 
    self.swid        = None
    self._scrape_league()

  def __repr__(self):
    return 'League %s (%s), %s Season' % (self.settings.league_name, 
                                          self.league_id, self.year)
  def _scrape_league(self):
    '''Scrape league info from ESPN'''
    # Read config
    self._get_config()
    self._set_basic_info()
    # Scrape info
    try:
      data = fetch_page(league_id=self.league_id, year=self.year, cookies=self.cookies, 
                        ENDPOINT=self.ENDPOINT, use_soup=False, use_json=True)
    except Exception as e:
      logger.exception(e)
      raise(e)
    self._scrape_teams(data)
    self._scrape_settings(data)
    self._update_for_week(self.week)

  def _get_config(self):
    '''Read configuration file'''
    logger.info(f'Parsing config file: {self.config_file}')
    config = configparser.RawConfigParser(allow_no_value=True)
    config.read(self.config_file)
    self.config = config
  
  def _set_basic_info(self):
    '''Set league id, week, year'''
    self.league_id   = self.config['League Info'].getint('league_id')
    self.year        = self.config['League Info'].getint('year')
    self.week        = self.config['League Info'].getint('week')
    self.s2          = self.config['Private League'].get('s2', None)
    self.swid        = self.config['Private League'].get('swid', None)
    # Set cookies 
    self.cookies = {'espn_s2': self.s2, 'SWID': self.swid} if (self.s2 and self.swid) else None
    logger.debug(f'Parsed and saved basic info: league_id: {self.league_id}, year: {self.year}, '\
                f'week: {self.week}, cookies: {self.cookies}')

  def sorted_teams(self, sort_key='teamId', reverse=False):
    '''Returns league teams sorted by the string <sort_key> 
       and optionally in <reverse> order'''
    return sorted(self.teams, key=lambda x: attrgetter(sort_key)(x), reverse=reverse)

  def _scrape_teams(self, data):
    '''Scrape info for each team from ESPN'''
    logger.info('Collecting stats for all teams')
    raw_teams = data['leaguesettings']['teams']
    for t in raw_teams: self.teams.append(Team(raw_teams[t]))
    fix_teamId(self.sorted_teams(sort_key='teamId'))
    for t in self.teams: t.stats._replace_opponents(self.teams)
    for t in self.teams: t.stats._calc_mov()

  def _scrape_settings(self, data):
    '''Scrape league settings info'''
    self.settings = Settings(data)

  def _update_for_week(self, week):
    '''Update MOV, wins and loses, based on week Numer'''
    # Set the week number
    if week != self.week:
      print('Updating wins, losses, MOV for week %s (previous data was for week: %s)'%(week, self.week))
      self.week = week
    # Calculate wins and loses based on week
    for t in self.teams: t.stats._calc_wins_losses(t.teamId, self.week, self.teams)

  def _calc_dom(self, sq_weight=0.25, decay_penalty=0.5):
    '''Calculate the two step dominance rankings'''
    teams_sorted = self.sorted_teams(sort_key='teamId', reverse=False)
    dom = TwoStepDom( self.settings.n_teams, self.week, sq_weight=sq_weight, decay_penalty=decay_penalty)
    dom.get_ranks(teams_sorted)
    #norm_rank(teams_sorted, 'dom')
    norm_by_max(teams_sorted, 'dom')
  
  def _calc_lsq(self, B_w=30., B_r=35., dS_max=35., beta_w=2.2, show_plot=False):
    '''Calculate rankings based on iterative lsq method''' 
    teams_sorted = self.sorted_teams(sort_key='teamId', reverse=False)
    lsq = LSQ(self.year, self.week, B_w=B_w, B_r=B_r, dS_max=dS_max, beta_w=beta_w, show=show_plot)
    lsq.get_ranks(teams_sorted)
    #norm_rank(teams_sorted, 'lsq')
    norm_by_max(teams_sorted, 'lsq')
    
  def _calc_colley(self, printMatrix=False):
    '''Calculates and assigns colley rankings for each team in the league'''
    teams_sorted = self.sorted_teams(sort_key='teamId', reverse=False)
    colley = Colley(self.week, self.settings.n_teams, printM=printMatrix)
    colley.get_ranks(teams_sorted)
    #norm_rank(teams_sorted, 'col')
    norm_by_max(teams_sorted, 'col')

  def _calc_sos(self, rank_power=2.37):
    '''Calculates the strength of schedule based on lsq rankings'''
    teams_sorted = self.sorted_teams(sort_key='teamId', reverse=False)
    calc_sos(teams_sorted, self.week, rank_power=rank_power)
    norm_by_max(teams_sorted, 'sos')

  def _calc_luck(self, awp_weight=0.5):
    '''Calculates the luck index'''
    teams_sorted = self.sorted_teams(sort_key='teamId', reverse=False)
    calc_luck(teams_sorted, self.week, awp_weight=awp_weight)
    norm_by_max(teams_sorted, 'luck')

  def _calc_cons(self, cons_weight=0.5):
    '''Calculate the consistency index'''
    teams_sorted = self.sorted_teams(sort_key='teamId', reverse=False)
    calc_cons(teams_sorted, self.week)
    norm_by_max(teams_sorted, 'cons')

  def _calc_power(self, w_dom=0.18, w_lsq=0.18, w_col=0.18, w_awp=0.18, 
                 w_sos=0.06, w_luck=0.06, w_cons=0.10, w_strk=0.06):
    '''Calculates the final weighted power index'''
    teams_sorted = self.sorted_teams(sort_key='teamId', reverse=False)
    calc_power(teams_sorted, self.week, w_dom=w_dom, w_lsq=w_lsq, w_col=w_col,
               w_awp=w_awp, w_sos=w_sos, w_luck=w_luck, w_cons=w_cons, w_strk=w_strk)

  def _save_ranks(self, getPrev=True):
    '''Save the power rankings, optionally calculate change from previous week'''
    teams_sorted = self.sorted_teams(sort_key='rank.power', reverse=True)
    save_ranks(teams_sorted, self.year, self.week, getPrev=getPrev)

  def _calc_tiers(self, bw=0.09, order=4, show_plot=False):
    '''Calculates tiers based on the power rankings'''
    teams_sorted = self.sorted_teams(sort_key='rank.power', reverse=True)
    calc_tiers(teams_sorted, self.year, self.week, bw=bw, order=order, show=show_plot)

  def print_rankings(self):
    '''Print table of metrics and final power rankings'''
    print('\nWeek %d Power Rankings\n======================'%(self.week))
    # Sort teams based on power ranking
    s_teams = self.sorted_teams(sort_key='rank.power', reverse=True)
    print('%20s %7s  %8s  %3s  %3s  %3s  %3s  %5s  %5s  %6s  %6s %5s'%('Owner','W-L',
          '# (Change)','Power','LSQ','Colley','2SD','AWP','SOS','Luck','Cons','Tier'))
    for i,t in enumerate(s_teams):
      delta = int(t.rank.prev) - (i+1)
      pm = '-' if delta < 0 else '+' 
      ch = '%s%2d'%(pm, abs(delta)) if delta != 0 else delta 
      rec = '%2d-%-2d'%(t.stats.wins,t.stats.losses)
      print('%20s %7s  %-8s  %.3f  %.3f  %.3f  %.3f  %.3f  %.3f  %.3f  %.3f %2d'%(t.owner, rec,
            i+1 if ch == 0 else '%-3s(%3s)'%(i+1, ch), t.rank.power,t.rank.lsq,t.rank.col,
            t.rank.dom,t.stats.awp,t.rank.sos,t.rank.luck,t.rank.cons,t.rank.tier))

  def get_power_rankings(self, week=-1):
    '''Get the power rankings for the specified week
	     Configuration for all the metrix is passed via config
	     Default values are set if they are missing from config file
       If week is passed, rankings are updated for that week number'''
    logger.info('Calculating power rankings')
    # Update week
    if week > 0: self._update_for_week(week)
	  # Calculate two-step dominance rankings
    self._calc_dom(sq_weight     = self.config['2SD'].getfloat('sq_weight', 0.25),
	                 decay_penalty = self.config['2SD'].getfloat('decay_penalty', 0.5) )
	  # Calculate the least squares rankings
    self._calc_lsq(B_w       = self.config['LSQ'].getfloat('B_w', 30.),
	                 B_r       = self.config['LSQ'].getfloat('B_r', 35.),
	                 dS_max    = self.config['LSQ'].getfloat('dS_max', 35.),
	                 beta_w    = self.config['LSQ'].getfloat('beta_w', 2.2),
	                 show_plot = self.config['LSQ'].getboolean('show_plot', False) )
	  # Calculate Colley rankings
    self._calc_colley(printMatrix = self.config['Colley'].getboolean('printMatrix', False) )
	  # Calculate SOS
    self._calc_sos(rank_power = self.config['SOS'].getfloat('rank_power', 2.37) )
	  # Calculate Luck index
    self._calc_luck(awp_weight = self.config['Luck'].getfloat('awp_weight', 0.5) )
    # Calculate the Consistency index
    self._calc_cons()
	  # Calculate final power rankings
    self._calc_power(w_dom  = self.config['Power'].getfloat('w_dom', 0.18),
	                   w_lsq  = self.config['Power'].getfloat('w_lsq', 0.18),
	                   w_col  = self.config['Power'].getfloat('w_col', 0.18),
	                   w_awp  = self.config['Power'].getfloat('w_awp', 0.18),
	                   w_sos  = self.config['Power'].getfloat('w_sos', 0.06),
	                   w_luck = self.config['Power'].getfloat('w_luck', 0.06),
	                   w_cons = self.config['Power'].getfloat('w_cons', 0.10),
	                   w_strk = self.config['Power'].getfloat('w_strk', 0.06) )
	  # Calculate change from previous week
    self._save_ranks(getPrev = self.config['Tiers'].getboolean('getPrev', False))
	  # Get Tiers
    self._calc_tiers(bw        = self.config['Tiers'].getfloat('bw', 0.09),
	                   order     = self.config['Tiers'].getint('order', 4),
	                   show_plot = self.config['Tiers'].getboolean('show_plot', False) )
	  # Print Sorted team
    self.print_rankings()
    # Calc the playoff odds
    do_playoffs = self.config['Playoffs'].getboolean('doPlayoffs',False)
    if do_playoffs:
      calc_playoffs(self.teams, self.year, self.week, self.settings, 
                    n_sims = self.config['Playoffs'].getint('num_simulations', 200000))

  def make_website(self):
    '''Creates website based on current power rankings.
       Must run get_power_rankings() first'''
    # Make Radar plots of each teams stats
    logger.info('Creating radar plots to summarize team stats')
    Y_LOW  = [float(yl.strip()) for yl in self.config['Radar'].get('Y_LOW').split(',')]
    Y_HIGH = [float(yh.strip()) for yh in self.config['Radar'].get('Y_HIGH').split(',')]
    for t in self.teams:
      make_radar(t, self.year, self.week, Y_LOW, Y_HIGH)
    # Make welcome page power plot
    teams_sorted = self.sorted_teams(sort_key='rank.power', reverse=True)
    make_power_plot(teams_sorted, self.year, self.week)
    doSetup = self.config['Web'].getboolean('doSetup', True)
    # Scrape history
    if doSetup:
      scrape_history(league_id=self.league_id, year=self.year, cookies=self.cookies)
    # Generate html files for team and summary pages
    generate_web(self.teams, self.year, self.week, self.league_id, 
                 self.settings.league_name, self.settings, doSetup=doSetup)

