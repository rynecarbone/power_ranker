import os
import shutil
from distutils.dir_util import copy_tree
import pkg_resources
import numpy as np

#__________________
def get_arrow(i, j):
  '''Create glyphicon chevron
     i: previous rank
     j: current rank'''
  
  snu = '  <span class="text-success">'
  snd = '  <span class="text-danger">'
  ns = '</span>'
  up = '<span class="glyphicon glyphicon-chevron-up"></span>'
  dn = '<span class="glyphicon glyphicon-chevron-down"></span>'
  
  arrow = ''
  change = int(i) - int(j)
  if change > 0:
    arrow += snu + up + ' %d'%np.fabs(change) + ns
  elif change < 0:
    arrow += snd + dn + ' %d'%np.fabs(change) + ns

  return arrow

#________________________________________
def make_progress_bar(title, value, rank, max_FAAB=100):
  '''Makes progress bar with label and value'''
  tr = '<tr>'
  td = '<td>'
  p  = '<p class="h4">'
  dp = '<div class="progress">'
  db = '<div class="progress-bar %s" role="progressbar" aria-value-now="%d" aria-valuemin="0" aria-valuemax="100" style="width: %d%%">'
  sp = '<span>'
  ps = '</span>'
  vd = '</div>'
  pp = '</p>'
  dt = '</td>'
  rt = '</tr>'
  s  = 'progress-bar-success'
  w  = 'progress-bar-warning'
  d  = 'progress-bar-danger'

  progress_bar = tr + td + p + title + pp + dp
  if value < 33.33: progress_bar += db%(d,value,value)
  elif value < 66.66: progress_bar += db%(w,value,value)
  else:  progress_bar += db%(s,value,value)
  if "FAAB" in title:
    progress_bar += sp+'$%d of $%d'%(rank, max_FAAB) + ps 
  else:
    progress_bar += sp+'(%s)'%rank + ps
  progress_bar += vd + vd +dt + rt
  return progress_bar  


#_______________________________
def make_game_log(t, week):
  '''Returns table body for game log'''
  tr = '<tr>'
  td = '<td>'
  dt = '</td>'
  rt = '</tr>'
  win = '<span class="text-success">W</span>'
  loss = '<span class="text-danger">L</span>'
  game_log = ''

  for w,o in enumerate(t.stats.schedule[:week]):
    game_log += tr + td + '%s'%(w+1) + dt
    game_log += td + '%s'%(o.teamName) + dt
    game_log += td + '%s'%(o.owner.title()) + dt
    game_log += td + '%.2f &mdash; %.2f'%(float(o.stats.scores[w]),float(t.stats.scores[w])) + dt
    game_log += td + (win if float(t.stats.scores[w]) > float(o.stats.scores[w]) else loss ) + dt + rt

  return game_log


#________________________________
def make_power_table(teams,week):
  '''Creates simple table with rankings'''
  tr = '<tr>'
  td = '<td>'
  dt = '</td>'
  rt = '</tr>'
  table = ''
  
  for i,t in enumerate(sorted(teams, key=lambda x: x.rank.power, reverse=True)):
    arrow = get_arrow(int(t.rank.prev), int(i+1))
    table += tr
    table += td + str(i+1) + dt
    table += td + t.owner.title() + arrow + dt
    table += td + '%s-%s'%(t.stats.wins,t.stats.losses) + dt
    table += td + "{0:.3f}".format(float(t.rank.power)) + dt
    table += td + "{0:.3f}".format(float(t.rank.lsq)) + dt
    table += td + "{0:.3f}".format(float(t.rank.dom)) + dt
    table += td + "{0:.3f}".format(float(t.rank.col)) + dt
    table += td + "{0:.3f}".format(float(t.rank.sos)) + dt
    table += td + "{0:.3f}".format(float(t.rank.luck)) + dt
    table += td + str(t.rank.tier) + dt
    table += rt

  return table

#__________________________
def get_player_drop(teams, level=''):
  '''Link in drop down list of player pages
     FIXME - what if duplicates? '''
  li = '<li>'
  il = '</li>'
  a  = '<a href="%s%s_%s/index.html">%s</a>'

  new_line = ''

  for t in sorted(teams, key=lambda x: x.owner):
    first = t.owner.split()[0].title()
    last = t.owner.split()[1].title()
    new_line += li + a%(level,first,last,t.owner.title()) + il

  return new_line

#__________________________________
def get_index(teams_sorted, teamId):
  '''Return ranking from ordered list of teamId'''
  for i,t in enumerate(teams_sorted):
    if t.teamId == teamId:
      return i+1

#_______________________________
def make_teams_page(teams, year, week, league_name, settings):
  '''Make teams page with stats, standings, game log, radar plots'''
  # Ordinal makes numbers like 2nd, 3rd, 4th etc 
  ordinal   = lambda n: "%d%s" % (n,"tsnrhtdd"[(n/10%10!=1)*(n%10<4)*n%10::4])
  # Use if player has no ESPN image ...
  stock_url = 'http://www.suttonsilver.co.uk/wp-content/uploads/blog-stock-03.jpg'  
  # Make team page for each owner
  for i,t in enumerate(sorted(teams, key=lambda x: x.rank.power, reverse=True)):
    logo  = t.logoUrl if len(t.logoUrl) > 4 else stock_url
    first = t.owner.split()[0].title()
    last  = t.owner.split()[1].title()
    out_name = 'output/%s/%s_%s/index.html'%(year, first, last)
    template = pkg_resources.resource_filename('power_ranker','docs/template/player.html')
    # create output and directory if it doesn't exist
    os.makedirs(os.path.dirname(out_name), exist_ok=True)
    src = ['INSERTOWNER',
           'INSERTLEAGUENAME',
           'INSERTWEEK',
           'IMAGELINK',
           'TEAMNAME',
           'TEAMABBR',
           'INSERTRECORD',
           'INSERTACQUISITIONS',
           'INSERTTRADES',
           'INSERTWAIVER',
           'OVERALLRANK',
           'POWERRANK',
           'AGGREGATEPCT',
           'RADARPLOT',
           'PLAYERDROPDOWN']
    rep = [t.owner,
           league_name,
           'week%s'%week,
           logo,
           t.teamName,
           t.teamAbbrev,
           '%s-%s'%(t.stats.wins, t.stats.losses),
           '%d'%int(t.stats.trans),
           '%d'%int(t.stats.trades),
           '%s'%ordinal(t.stats.waiver),
           '%s <small>%s</small>'%(ordinal(t.rank.overall), get_arrow(int(t.rank.prev_overall), int(t.rank.overall))),
           '%s <small>%s</small>'%(ordinal(int(i+1)), get_arrow(int(t.rank.prev), int(i+1))),
           '%.3f <small>(%d-%d)</small>'%(t.stats.awp,t.stats.awins,t.stats.alosses),
           'radar_%s.png'%t.teamId,
           get_player_drop(teams, level='../')]
    with open(template,'r') as f_in, open(out_name,'w') as f_out:
      for line in f_in:
        for (s,r) in zip(src, rep):
          line = line.replace(s,r)
        if 'INSERT_TPF_PB' in line:
          pf_sort = sorted(teams, key=lambda x: x.stats.pointsFor, reverse=True)
          pf_rank = get_index(pf_sort, t.teamId)
          # want 1st to be 100%
          line = make_progress_bar('Total Points For: %.2f'%float(t.stats.pointsFor),
                                  100.*float( settings.n_teams+1-pf_rank )/float(settings.n_teams), 
                                  ordinal(int(pf_rank))  )
        elif 'INSERT_TPA_PB' in line:
          pa_sort = sorted(teams, key=lambda x: x.stats.pointsAgainst, reverse=True)
          pa_rank = get_index(pa_sort, t.teamId)
          line = make_progress_bar('Total Points Against: %.2f'%float(t.stats.pointsAgainst), 
                                  100.*float( settings.n_teams+1-pa_rank )/float(settings.n_teams),  
                                  ordinal(int(pa_rank))  )
        elif 'INSERT_HS_PB' in line:
          hs_sort = sorted(teams, key=lambda x: max(x.stats.scores[:week]), reverse=True)
          hs_rank = get_index(hs_sort, t.teamId)
          line = make_progress_bar('High Score: %.2f'%max(t.stats.scores[:week]), 
                                  100.*float( settings.n_teams+1-hs_rank)/float(settings.n_teams), 
                                  ordinal(int(hs_rank))  )
        elif 'INSERT_LS_PB' in line:
          ls_sort = sorted(teams, key=lambda x: min(x.stats.scores[:week]), reverse=True)
          ls_rank = get_index(ls_sort, t.teamId)
          line = make_progress_bar('Low Score: %.2f'%min(t.stats.scores[:week]), 
                                  100.*float( settings.n_teams+1-ls_rank)/float(settings.n_teams), 
                                  ordinal(int(ls_rank))  )
        elif 'INSERT_FAAB_PB' in line:
          if settings.use_faab:
            max_FAAB = float(settings.max_faab)
            line = make_progress_bar('FAAB Remaining', 
                                     float(max_FAAB-t.stats.faab)*(100./max_FAAB), 
                                     int(max_FAAB-t.stats.faab), max_FAAB )
          else:
            line = make_progress_bar('Waiver Priority',
                                     100*float(settings.n_teams+1-t.stats.waiver)/float(settings.n_teams),
                                     ordinal(int(t.stats.waiver)) )
        elif 'INSERTTABLEBODY' in line:
          line = make_game_log(t, week)
        # after checking all substitutions, finally write each line
        f_out.write(line)


#________________________________
def make_power_page(teams, year, week, league_name):
  '''Produces power rankings page'''
  local_file = 'output/%s/power.html'%year
  template   = pkg_resources.resource_filename('power_ranker','docs/template/power.html')
  src = ['INSERT WEEK',
         'INSERTLEAGUENAME',
        'PLAYERDROPDOWN',
        'INSERT TABLE']
  rep = ['Week %s'%(week+1),
         league_name,
         get_player_drop(teams, level=''),
         make_power_table(teams,week)]
  # Write from template to local, with replacements
  output_with_replace(template, local_file, src, rep)


#________________________________
def make_about_page(teams, year, league_name):
  '''Produces about page, updating week for power rankings'''  
  local_file = 'output/%s/about/index.html'%year
  template   = pkg_resources.resource_filename('power_ranker','docs/template/about.html')
  src = ['PLAYERDROPDOWN',
         'INSERTLEAGUENAME']
  rep = [get_player_drop(teams, level='../'),
         league_name]
  # Write from template to local, with replacements
  output_with_replace(template, local_file, src, rep)
  # Copy default images
  in_pics = ['dom_graph.png','tiers_example.png']
  for pic in in_pics:
    p = pkg_resources.resource_filename('power_ranker','docs/template/%s'%pic)
    local_p = os.path.join(os.getcwd(), 'output/%s/about/%s'%(year,pic))
    shutil.copyfile(p, local_p)
  
  
#________________________________
def make_welcome_page(year, week, league_id, league_name):
  '''Produces welcome page, with power plot'''
  local_file = 'output/%s/index.html'%year
  template   = pkg_resources.resource_filename('power_ranker','docs/template/welcome.html')
  # Source and replacement strings from template
  src = ['INSERTWEEK',
         'INSERTNEXT',
         'INSERTLEAGUEID',
         'INSERTLEAGUENAME']
  rep = ['week%d'%week,
         'Week %d'%(week+1),
         str(league_id),
         str(league_name)]
  # Write from template to local, with replacements
  output_with_replace(template, local_file, src, rep)

  
#_______________________________________________
def output_with_replace(template, local_file, src, rep):
  '''Write the <template> file contents to <local_file>
     Replace all instances from list <src> with parallel
     entry in list <rep>'''
  # create directory if doesn't already exist
  os.makedirs(os.path.dirname(local_file), exist_ok=True)
  with open(template, 'r') as f_in, open(local_file, 'w') as f_out:
    for line in f_in:
      for (s, r) in zip(src, rep):
        line = line.replace(s,r)
      f_out.write(line)

#___________________________________________
def copy_css_js_themes(year):
  '''Copy the css and js files to make website 
     look like it is not from 1990'''
  # Specific themes
  in_files = ['about.js','theme.js','theme.css','cover.css']
  for f in in_files:
    template = pkg_resources.resource_filename('power_ranker','docs/template/%s'%f)
    local_file = os.path.join(os.getcwd(), 'output/%s/%s'%(year,f))
    shutil.copyfile(template, local_file)
  # Bootstrap dist and assets
  boostrap_dirs = ['dist','assets','images']
  for b in boostrap_dirs:
    template_dir = pkg_resources.resource_filename('power_ranker','docs/template/%s'%b)
    local_dir = os.path.join(os.getcwd(), 'output/%s'%(b))
    copy_tree(template_dir, local_dir)

#_________________________
def generate_web(teams, year, week, league_id, league_name, settings, doSetup=True):
  '''Makes power rankings page
           team summary page
           about page
    doSetup: flag to download bootstrap css/js themes to make html pretty
             and create the about page'''
  make_power_page(teams, year, week, league_name)
  make_teams_page(teams, year, week, league_name, settings)
  make_welcome_page(year, week, league_id, league_name)
  if doSetup:
    copy_css_js_themes(year)
    make_about_page(teams, year, league_name)
