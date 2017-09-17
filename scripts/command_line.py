import argparse
import shutil
import os.path
import pkg_resources
from power_ranker.league import League as League

#_______________________________
def run_cl_rankings(config_file):
  '''Given local config file, run power rankings from CL'''
  my_league = League(config_file)
  my_league.get_power_rankings()
  my_league.make_website()

#________________________________________________
def set_local_cfg(name, leagueid, year, week):
  '''Run rankings with user supplied name, leagueid, year and week'''
  #default_cfg = os.path.join(os.path.dirname(__file__),'docs/default_config.cfg')
  default_cfg = pkg_resources.resource_filename('power_ranker','docs/default_config.cfg')
  local_cfg = os.path.join(os.getcwd(),'MY_LOCAL_CONFIG.cfg')
  with open(default_cfg,'r') as f1, open(local_cfg,'w') as f2:
    for line in f1:
      if 'league_name' in line:
        line = 'league_name = %s\n'%name
      elif 'league_id' in line:
        line = 'league_id = %s\n'%leagueid
      elif 'year' in line:
        line = 'year = %s\n'%year
      elif 'week' in line:
        line = 'week = %s\n'%week
      f2.write('%s'%line)
  run_cl_rankings(local_cfg)


#________________
def copy_config():
  '''Copy default configuration file locally for user to edit'''
  my_data = pkg_resources.resource_filename('power_ranker', "docs/default_config.cfg")
  #my_data = os.path.join(os.path.dirname(__file__),'../docs/default_config.cfg')
  my_local_data = os.path.join(os.getcwd(),'MY_LOCAL_CONFIG.cfg')
  print('Creating local copy of: {}\nTo local destination: {}'.format(
    my_data,
    my_local_data
  ))
  shutil.copyfile(my_data, my_local_data)
  
#_________
def main():
  '''Run power_ranker from command line
     Can download configuration file to edit, and then
     pass it to run rankings'''
  parser = argparse.ArgumentParser()
  parser.add_argument('-n', '--name', help='League Name')
  parser.add_argument('-l', '--leagueid', help='ESPN public League ID')
  parser.add_argument('-y', '--year', help='Year to retreive')
  parser.add_argument('-w', '--week', help='Week to analyze')
  parser.add_argument('-dc', '--download-config', help='Download local copy of configuration file', dest='download', action='store_true')
  parser.add_argument('-c', '--config-file', help='Use specified config file to run power_ranker', dest='config')
  args = parser.parse_args()
  # Download local config file
  if args.download:
    copy_config()
  # Supplied config file to get rankings  
  elif args.config:
    print('Using {} to generate power rankings'.format(args.config))
    run_cl_rankings(args.config)
  # Supplied league information, use rest of default info
  elif args.name and args.leagueid and args.year and args.week:
    print('Using user input:\nLeague Name: {}\nLeague ID: {}\nYear: {}\nWeek: {}'.format(
      args.name, args.leagueid, args.year, args.week
    ))
    set_local_cfg(args.name, args.leagueid, args.year, args.week)
  # Incomplete information
  else:
    parser.print_help()
    parser.exit(1)

#________________________
if __name__ == '__main__':
  print('Here')
  main()
