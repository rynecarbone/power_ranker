#!/usr/bin/env python3
from league import League

#_________________
def main():
  
  # Specify configuration
  my_config_file = 'default_config.cfg'

  # Retrieve league info 
  league = League( config_file=my_config_file )
  
  # Get power rankings for specified week,
  # Default week read from config file
  # league.get_power_rankings(week=week_N)
  league.get_power_rankings()

  # Generate website 
  league.make_website()  

  # Calculate playoff odds
  # po.calc_playoffs(teams, week)


#________________________
if __name__ == "__main__":
  main()
