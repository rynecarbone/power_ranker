import argparse
import shutil
import os.path
from power_ranker.league import League as League

#_______________________________
def run_cl_rankings(config_file):
  '''Given local config file, run power rankings from CL'''
  my_league = League(config_file)
  my_league.get_power_rankings()
  my_league.make_website()

#________________
def copy_config():
  '''Copy default configuration file locally for user to edit'''
  my_data = os.path.join(os.path.dirname(__file__),'../docs/default_config.cfg')
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
  parser.add_argument('-n', '--name', help='League Name', default='my_league')
  parser.add_argument('-l', '--leagueid', help='ESPN public League ID', default='123456')
  parser.add_argument('-y', '--year', help='Year to retreive', default='2016')
  parser.add_argument('-w', '--week', help='Week to analyze', default='1')
  parser.add_argument('-dc', '--download-config', help='Download local copy of configuration file', dest='download', action='store_true')
  parser.add_argument('-c', '--config-file', help='Use specified config file to run power_ranker', dest='config')
  args = parser.parse_args()
  print('League Name: {}\nLeague ID: {}\nYear: {}\nWeek: {}\nCopy Config: {}\nInput Config File: {}'.format(
    args.name,
    args.leagueid,
    args.year,
    args.week,
    args.download,
    args.config
  ))
  if args.download:
    copy_config()
  if args.config:
    print('Using {} to generate power rankings'.format(args.config))
    run_cl_rankings(args.config)

#________________________
if __name__ == '__main__':
  print('Here')
  main()
