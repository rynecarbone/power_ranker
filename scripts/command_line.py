import argparse
import shutil
import os.path
import getpass
import pkg_resources
from power_ranker.league import League
from power_ranker.private import PrivateLeague

#_______________________________
def run_cl_rankings(config_file, private_league=False):
  '''Given local config file, run power rankings from CL'''
  print('Using {} to generate power rankings'.format(config_file))
  if private_league:
    # Overwrite cookies in config file with current login credentials
    copy_config(data_file=config_file, 
                local_file='%s_tmp'%config_file, 
                private_league=private_league)
    os.rename(os.path.join(os.getcwd(),'%s_tmp'%config_file), 
              os.path.join(os.getcwd(), config_file))
  my_league = League(config_file)
  my_league.get_power_rankings()
  my_league.make_website()

#________________________________________________
def set_local_cfg(leagueid, year, week, private_league=False):
  '''Run rankings with user supplied leagueid, year, and week'''
  print('Using user input:\nLeague ID: {}\nYear: {}\nWeek: {}'.format(
      leagueid, year, week
  ))
  src = ['league_id','year','week']
  rep = [leagueid, year, week]
  copy_config(src=src, rep=rep, private_league=private_league)
  run_cl_rankings('MY_LOCAL_CONFIG.cfg')

#_________________________________________________________
def copy_config(data_file=None, 
                local_file=None, 
                src=[], rep=[], private_league=False):
  '''Copy default configuration file locally for user to edit
    Optionally pass list of lines to replace in configuration file'''
  my_data = pkg_resources.resource_filename('power_ranker', "docs/default_config.cfg")
  my_local_data = os.path.join(os.getcwd(),'MY_LOCAL_CONFIG.cfg')
  if data_file and local_file:
    my_data = os.path.join(os.getcwd(), data_file)
    my_local_data = os.path.join(os.getcwd(), local_file)
  print('Creating copy of: {}\nTo local destination: {}'.format(
    my_data, my_local_data
  ))
  # If private league, get cookies
  if private_league:
    src += ['s2', 'swid']
    rep += get_private_cookies()
  # Make any specified changes to local copy of default config
  with open(my_data,'r') as f_in, open(my_local_data,'w') as f_out:
    for line in f_in:
      for (s,r) in zip(src, rep):
        if line.startswith(s) and '#' not in line:
          line = '%s = %s\n'%(s,r) 
      f_out.write(line)

#_______________________
def get_private_cookies():
  '''User enters in log in information for private league,
    Cookies are returned so API can access private league info'''
  user = input('Username: ')
  pw   = getpass.getpass('Password: ')
  pl = PrivateLeague(user, pw)
  pl.authorize()
  s2, swid = pl.get_cookies()
  return [s2, swid]

#_________
def main():
  '''Run power_ranker from command line
     Can download configuration file to edit, and then
     pass it to run rankings'''
  parser = argparse.ArgumentParser()
  parser.add_argument('-l', '--leagueid', help='ESPN public League ID')
  parser.add_argument('-y', '--year', help='Year to retreive')
  parser.add_argument('-w', '--week', help='Week to analyze')
  parser.add_argument('-dc', '--download-config', help='Download local copy of configuration file', dest='download', action='store_true')
  parser.add_argument('-c', '--config-file', help='Use specified config file to run power_ranker', dest='config')
  parser.add_argument('-p', '--private-league', help='League is private league, log in to fetch cookies', dest='private', action='store_true')
  args = parser.parse_args()
  # Download local config file
  if args.download:
    copy_config(private_league=args.private)
  # Supplied config file to get rankings  
  elif args.config:
    run_cl_rankings(args.config, private_league=args.private)
  # Supplied league information, use rest of default info
  elif args.leagueid and args.year and args.week:
    set_local_cfg(args.leagueid, args.year, args.week, private_league=args.private)
  # Incomplete information
  else:
    parser.print_help()
    parser.exit(1)

#________________________
if __name__ == '__main__':
  main()
