"""Scripts to run power_ranker from the command line"""
import sys
import logging
import argparse
import os.path
import getpass
import pkg_resources
from power_ranker.league import League
from power_ranker.private import PrivateLeague

__author__ = 'Ryne Carbone'

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                    stream=sys.stdout,
                    level=logging.INFO)
logger = logging.getLogger('power_ranker_cli')


def run_cl_rankings(config_file, private_league=False):
  """Given local config file, run power rankings from CL

  :param config_file: configuration file
  :param private_league: flag if league is private
  :return: None
  """
  logger.info(f'Using {config_file} to generate power rankings')
  if private_league:
    # Overwrite cookies in config file with current login credentials
    copy_config(data_file=config_file, 
                local_file=f'{config_file}_tmp',
                private_league=private_league)
    os.rename(os.path.join(os.getcwd(), f'{config_file}_tmp'),
              os.path.join(os.getcwd(), config_file))
  my_league = League(config_file)
  my_league.get_power_rankings()
  my_league.make_website()


def set_local_cfg(leagueid, year, week, private_league=False):
  """Run rankings with user supplied leagueid, year, and week

  :param leagueid: numeric id of league
  :param year: season to run power rankings on
  :param week: week in season
  :param private_league: flag if league is private
  :return: None
  """
  logger.info(f'Using user input:\nLeague ID: {leagueid}\nYear: {year}\nWeek: {week}')
  src = ['league_id', 'year', 'week']
  rep = [leagueid, year, week]
  copy_config(src=src, rep=rep, private_league=private_league)
  run_cl_rankings('MY_LOCAL_CONFIG.cfg')


def copy_config(data_file=None,
                local_file=None, 
                src=None, rep=None, private_league=False):
  """Copy default configuration file locally for user to edit
    Optionally pass list of lines to replace in configuration file

  :param data_file: file with configurations
  :param local_file: local file to store configurations
  :param src: optional list of lines to replace
  :param rep: optional list of replacement lines
  :param private_league: flag if league is private
  :return: None
  """
  # Set src, rep to empty lists if none passed
  if not src:
    src = []
  if not rep:
    rep = []
  my_data = pkg_resources.resource_filename('power_ranker', "docs/default_config.cfg")
  my_local_data = os.path.join(os.getcwd(), 'MY_LOCAL_CONFIG.cfg')
  if data_file and local_file:
    my_data = os.path.join(os.getcwd(), data_file)
    my_local_data = os.path.join(os.getcwd(), local_file)
  logger.info(f'Creating copy of: {my_data}\nTo local destination: {my_local_data}')
  # If private league, get cookies
  if private_league:
    src += ['s2', 'swid']
    rep += get_private_cookies()
  # Make any specified changes to local copy of default config
  with open(my_data, 'r') as f_in, open(my_local_data, 'w') as f_out:
    for line in f_in:
      for (s, r) in zip(src, rep):
        if line.startswith(s) and '#' not in line:
          line = f'{s} = {r}\n'
      f_out.write(line)


def get_private_cookies():
  """User enters in log in information for private league,
    Cookies are returned so API can access private league info

    :return: cookies and id for accessing private league data
    """
  user = input('Username: ')
  pw = getpass.getpass('Password: ')
  pl = PrivateLeague(user, pw)
  pl.authorize()
  s2, swid = pl.get_cookies()
  return [s2, swid]


def main():
  """Run power_ranker from command line
     Can download configuration file to edit, and then
     pass it to run rankings"""
  parser = argparse.ArgumentParser()
  parser.add_argument('-l', '--leagueid',
                      help='ESPN public League ID')
  parser.add_argument('-y', '--year',
                      help='Year to retreive')
  parser.add_argument('-w', '--week',
                      help='Week to analyze')
  parser.add_argument('-dc', '--download-config',
                      help='Download local copy of configuration file',
                      dest='download', action='store_true')
  parser.add_argument('-c', '--config-file',
                      help='Use specified config file to run power_ranker',
                      dest='config')
  parser.add_argument('-p', '--private-league',
                      help='League is private league, log in to fetch cookies',
                      dest='private', action='store_true')
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


if __name__ == '__main__':
  main()
