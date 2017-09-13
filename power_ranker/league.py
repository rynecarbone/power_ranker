import requests
import configparser
from team import Team
from two_step_dom import TwoStepDom
from lsq import LSQ
from colley import Colley
import utils as U

#___________________
class League(object):
  '''Given ESPN public league information, collects stats and creates
     team objects for all teams'''
  def __init__(self, config_file='default_config.cfg'):
    self.league_id   = '' 
    self.year        = ''
    self.week        = ''
    self.N_teams     = 0.
    self.teams       = []
    self.config_file = config_file
    self.ENDPOINT    = "http://games.espn.com/ffl/api/v2/"
    self._get_config()
    self._set_basic_info()
    self._fetch_teams()

  def __repr__(self):
    return 'League %s, %s Season' % (self.league_id, self.year)

  def _get_config(self):
    '''Read configuration file'''
    config = configparser.ConfigParser()
    config.read(self.config_file)
    self.config = config
  
  def _set_basic_info(self):
    '''Set league id, week, year'''
    self.league_id = self.config['League Info'].getint('league_id')
    self.year      = self.config['League Info'].getint('year')
    self.week      = self.config['League Info'].getint('week')

  def _fetch_teams(self):
    '''Scrape info for each team from ESPN'''
    url = "%sleagueSettings?leagueId=%s&seasonId=%s"
    r = requests.get(url%(self.ENDPOINT, self.league_id, self.year))
    data = r.json()
    teams = data['leaguesettings']['teams']
    self.N_teams = len(teams)
    for team in teams:
      self.teams.append(Team(teams[team]))
    # Replace opponent with team instance
    U.replace_opponents(self.teams)    
    # Calculate the MOV
    U.calc_mov(self.teams)
    # Calculate wins and loses based on week
    U.calc_wins_losses(self.week, self.teams)

  def sorted_teams(self, sort_key='teamId', reverse=False):
    '''Returns league teams sorted by the string <sort_key> 
       and optionally in <reverse> order'''
    return sorted(self.teams, key=lambda x: getattr(x,sort_key), reverse=reverse)

  def calc_dom(self, sq_weight=0.25, decay_penalty=0.5):
    '''Calculate the two step dominance rankings'''
    teams_sorted = self.sorted_teams(sort_key='teamId', reverse=False)
    dom = TwoStepDom( self.N_teams, self.week, sq_weight=sq_weight, decay_penalty=decay_penalty)
    dom.get_ranks(teams_sorted)
  
  def calc_lsq(self, B_w=30., B_r=35., dS_max=35., beta_w=2.2, show_plot=False):
    '''Calculate rankings based on iterative lsq method''' 
    teams_sorted = self.sorted_teams(sort_key='teamId', reverse=False)
    lsq = LSQ(self.week, B_w=B_w, B_r=B_r, dS_max=dS_max, beta_w=beta_w, show=show_plot)
    lsq.get_ranks(teams_sorted)
    
  def calc_colley(self, printMatrix=False):
    '''Calculates and assigns colley rankings for each team in the league'''
    teams_sorted = self.sorted_teams(sort_key='teamId', reverse=False)
    colley = Colley(self.week, self.N_teams, printM=printMatrix)
    colley.get_ranks(teams_sorted)

  def calc_sos(self, rank_power=2.37):
    '''Calculates the strength of schedule based on lsq rankings'''
    teams_sorted = self.sorted_teams(sort_key='teamId', reverse=False)
    U.calc_sos(teams_sorted, self.week, rank_power=rank_power)

  def calc_luck(self, awp_weight=0.5):
    '''Calculates the luck index'''
    teams_sorted = self.sorted_teams(sort_key='teamId', reverse=False)
    U.calc_luck(teams_sorted, self.week, awp_weight=awp_weight)

  def calc_power(self, w_dom=0.21, w_lsq=0.18, w_col=0.18, w_awp=0.15, 
                 w_sos=0.10, w_luck=0.08, w_cons=0.05, w_strk=0.05):
    '''Calculates the final weighted power index'''
    teams_sorted = self.sorted_teams(sort_key='teamId', reverse=False)
    U.calc_power(teams_sorted, self.week, w_dom=w_dom, w_lsq=w_lsq, w_col=w_col,
                 w_awp=w_awp, w_sos=w_sos, w_luck=w_luck, w_cons=w_cons, w_strk=w_strk)

  def save_ranks(self, getPrev=True):
    '''Save the power rankings, optionally calculate change from previous week'''
    teams_sorted = self.sorted_teams(sort_key='power_rank', reverse=True)
    U.save_ranks(teams_sorted, self.week, getPrev=getPrev)

  def calc_tiers(self, bw=0.09, order=4, show_plot=False):
    '''Calculates tiers based on the power rankings'''
    teams_sorted = self.sorted_teams(sort_key='power_rank', reverse=True)
    U.calc_tiers(teams_sorted, self.week, bw=bw, order=order, show=show_plot)

  def print_rankings(self):
    '''Print table of metrics and final power rankings'''
    print('\nWeek %d Power Rankings\n======================'%(self.week))
    # Sort teams based on power ranking
    s_teams = self.sorted_teams(sort_key='power_rank', reverse=True)
    print('%20s %7s  %8s  %3s  %3s  %3s  %3s  %5s  %5s  %6s  %5s'%('Owner','W-L',
          '# (Change)','Power','LSQ','Colley','2SD','SOS','AWP','Luck','Tier'))
    for i,t in enumerate(s_teams):
      delta = int(t.prev_rank) - (i+1)
      pm = '-' if delta < 0 else '+' 
      ch = '%s%2d'%(pm, abs(delta)) if delta != 0 else delta 
      rec = '%2d-%-2d'%(t.wins,t.losses)
      print('%20s %7s  %-8s  %.3f  %.3f  %.3f  %.3f  %.3f  %.3f  %.3f  %2d'%(t.owner, rec,
            i+1 if ch == 0 else '%-3s(%3s)'%(i+1, ch), t.power_rank,t.lsq_rank,t.colley_rank,t.dom_rank,t.sos,t.awp,t.luck,
            t.tier))
