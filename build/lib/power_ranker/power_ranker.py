#!/usr/bin/env python3
import configparser
from league import League
#_________________
def main():
  
  # Specify configuration
  my_config_file = 'default_config.cfg'

  # Retrieve league info 
  league = League( config_file=my_config_file )
  
  # Get power rankings for specified week
  get_power_rankings(league)

  # Generate website 
  make_website(league)  

  # Calculate playoff odds
  # po.calc_playoffs(teams, week)


#___________________________________________
def get_power_rankings(league):
  '''Get the power rankings for the specified week
     Configuration for all the metrix is passed via config
     Default values are set if they are missing from config file'''
   
  config = league.config

  # Set the week to compute the rankings for
  #league.week = config['League Info'].getint('week', 1)

  # Calculate two-step dominance rankings
  league.calc_dom(sq_weight     = config['2SD'].getfloat('sq_weight', 0.25), 
                  decay_penalty = config['2SD'].getfloat('decay_penalty', 0.5) )
  
  # Calculate the least squares rankings
  league.calc_lsq(B_w       = config['LSQ'].getfloat('B_w', 30.), 
                  B_r       = config['LSQ'].getfloat('B_r', 35.), 
                  dS_max    = config['LSQ'].getfloat('dS_max', 35.), 
                  beta_w    = config['LSQ'].getfloat('beta_w', 2.2), 
                  show_plot = config['LSQ'].getboolean('show_plot', False) )

  # Calculate Colley rankings 
  league.calc_colley(printMatrix = config['Colley'].getboolean('printMatrix', False) )

  # Calculate SOS
  league.calc_sos(rank_power = config['SOS'].getfloat('rank_power', 2.37) )
 
  # Calculate Luck index
  league.calc_luck(awp_weight = config['Luck'].getfloat('awp_weight', 0.5) )

  # Calculate final power rankings
  league.calc_power(w_dom  = config['Power'].getfloat('w_dom', 0.21),
                    w_lsq  = config['Power'].getfloat('w_lsq', 0.18), 
                    w_col  = config['Power'].getfloat('w_col', 0.18), 
                    w_awp  = config['Power'].getfloat('w_awp', 0.15), 
                    w_sos  = config['Power'].getfloat('w_sos', 0.10), 
                    w_luck = config['Power'].getfloat('w_luck', 0.08), 
                    w_cons = config['Power'].getfloat('w_cons', 0.05), 
                    w_strk = config['Power'].getfloat('w_strk', 0.05) )

  # Calculate change from previous week
  league.save_ranks(getPrev = config['Tiers'].getboolean('getPrev', False))

  # Get Tiers
  league.calc_tiers(bw        = config['Tiers'].getfloat('bw', 0.09), 
                    order     = config['Tiers'].getint('order', 4), 
                    show_plot = config['Tiers'].getboolean('show_plot', False) )

  # Print Sorted team
  league.print_rankings()


#______________________________
def make_website(league):
  print('Website...')
  # Make power rankings plot
  # TODO
  
  # Make website template
  # TODO
  
  # Make radar plots
  # TODO


#________________________
if __name__ == "__main__":
  main()
