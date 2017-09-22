import argparse
import shutil
import os.path
import getpass
import pkg_resources
from power_ranker.league import League
from power_ranker.private import PrivateLeague

#_______________________________
def run_cl_rankings(config_file):
  '''Given local config file, run power rankings from CL'''
  my_league = League(config_file)
  my_league.get_power_rankings()
  my_league.make_website()

#________________________________________________
def set_local_cfg(name, leagueid, year, week):
  '''Run rankings with user supplied name, leagueid, year and week'''
  default_cfg = pkg_resources.resource_filename('power_ranker','docs/default_config.cfg')
  local_cfg = os.path.join(os.getcwd(),'MY_LOCAL_CONFIG.cfg')
  src = ['league_name','league_id','year','week']
  rep = [name, leagueid, year, week]
  with open(default_cfg,'r') as f1, open(local_cfg,'w') as f2:
    for line in f1:
      for (s,r) in zip(src, rep):
        if s in line: line = '%s = %s'%(s,r)
      f2.write('%s'%line)
  run_cl_rankings(local_cfg)

#________________
def copy_config(private_league=False):
  '''Copy default configuration file locally for user to edit'''
  my_data = pkg_resources.resource_filename('power_ranker', "docs/default_config.cfg")
  my_local_data = os.path.join(os.getcwd(),'MY_LOCAL_CONFIG.cfg')
  print('Creating local copy of: {}\nTo local destination: {}'.format(
    my_data,
    my_local_data
  ))
#  shutil.copyfile(my_data, my_local_data)
  if private_league:
    user = input('Username: ')
    pw   = getpass.getpass('Password: ') 
    pl = PrivateLeague(user, pw)
    pl.authorize()
    s2, swid = pl.get_cookies()
    src = ['s2', 'swid']
    rep = ['s2 = %s'%s2, 'swid = %s'%swid]
    with open(my_data,'r') as f_in, open(my_local_data,'w') as f_out:
      for line in f_in:
        for (s,r) in zip(src, rep):
          line = line.replace(s,r)
        f_out.write(line)
  
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
  parser.add_argument('-p', '--private-league', help='League is private league, log in to fetch cookies', dest='private', action='store_true')
  args = parser.parse_args()
  # Download local config file
  if args.download:
    copy_config(private_league=args.private)
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
