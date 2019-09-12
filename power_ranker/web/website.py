#!/usr/bin/env python

"""Create all html, css, js content for displaying power rankings on a website"""

import os
import logging
import shutil
from distutils.dir_util import copy_tree
import pkg_resources
import numpy as np
import pandas as pd
from ..history import scrape_history

__author__ = 'Ryne Carbone'

logger = logging.getLogger(__name__)


def get_arrow(delta):
    """Create glyphicon chevron

    :param delta: change in rankings from previous week
    :return: html code for arrow
    """
    # Define html snippets to build arrow code
    snu = '  <span class="text-success">'
    snd = '  <span class="text-danger">'
    ns = '</span>'
    up = '<span class="glyphicon glyphicon-chevron-up"></span>'
    dn = '<span class="glyphicon glyphicon-chevron-down"></span>'
    # Build html string
    arrow = ''
    if delta > 0:
        arrow += snu + up + f' {np.abs(int(delta))}' + ns
    elif delta < 0:
        arrow += snd + dn + f' {np.abs(int(delta))}' + ns
    return arrow


def make_progress_bar(title, value, rank, max_FAAB=100):
    """Makes progress bar with label and value

    :param title: string label for progress bar
    :param value: value for bar
    :param rank: rank to label the value
    :param max_FAAB: max FAAB budget if using faab
    :return: html progress bar
    """
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
    if value < 33.33:
        progress_bar += db % (d, value, value)
    elif value < 66.66:
        progress_bar += db % (w, value, value)
    else:  progress_bar += db % (s, value, value)
    if "FAAB" in title:
        progress_bar += sp + f'${rank} of ${max_FAAB}' + ps
    else:
        progress_bar += sp + f'({rank})' + ps
    progress_bar += vd + vd + dt + rt
    return progress_bar


def make_game_log(team_id, df_schedule, df_teams, week):
    """Returns table body for game log

    :param team_id: team id for game log
    :param df_schedule: data frame with all game data
    :param df_teams: data frame with team information
    :param week: current week
    :return: html table with game log
    """
    logger.debug(f'Creating game log for team {team_id}')
    # Html code for green W or red L
    win = '<span class="text-success">W</span>'
    loss = '<span class="text-danger">L</span>'
    # Filter schedule for games with team_id
    df_log = (df_schedule
              .query(f'(away_id=={team_id} | home_id=={team_id}) & matchupPeriodId<={week} & winner!="UNDECIDED"')
              .reset_index(drop=True))
    # Define opponent
    df_log['opp_id'] = df_log.apply(
        lambda x: x.get('away_id') if x.get('home_id') == team_id else x.get('home_id'), axis=1
    )
    # Define home/away
    df_log['loc'] = df_log.apply(lambda x: '@' if x.get('away_id') == team_id else '', axis=1)
    #  Format score for each matchup
    df_log['Score'] = df_log.apply(
        lambda x: f'{x.get("away_total_points"):.2f} &mdash; {x.get("home_total_points"):.2f}'
        if x.get('home_id') == team_id
        else f'{x.get("home_total_points"):.2f} &mdash; {x.get("away_total_points"):.2f}', axis=1
    )
    # Create html formated W/L
    df_log['Outcome'] = df_log.apply(
        lambda x: win
        if ((x.get('home_id') == team_id) & (x.get('winner') == 'HOME')) |
           ((x.get('away_id') == team_id) & (x.get('winner') == 'AWAY'))
        else loss, axis=1
    )
    # Add in opponent team information
    df_log = pd.merge(
        df_log,
        df_teams[['team_id', 'firstName', 'lastName', 'location', 'nickname']]
        .reset_index(drop=True),
        left_on='opp_id',
        right_on='team_id',
        how='left'
    )
    # Format opponent name and team name
    df_log['Owner'] = df_log.apply(
        lambda x: f'{x.get("firstName")} {x.get("lastName")}', axis=1
    )
    df_log['Opponent'] = df_log.apply(
        lambda x: f'{x.get("loc"):1}{x.get("location")} {x.get("nickname")}', axis=1
    )
    df_log['Week'] = df_log['matchupPeriodId']
    return (df_log
            [['Week', 'Opponent', 'Owner', 'Score', 'Outcome']]
            .to_html(border=0, index=False, escape=False,
                     classes=['table', 'table-striped', 'col-md-6'],
                     table_id='progress_table'))


def make_power_table(df_teams, df_ranks, df_sum):
    """Creates simple table with rankings

    :param df_teams: data frame with owner names
    :param df_ranks: data frame with rankings
    :param df_sum: data frame with season summary
    :return: string representation of html rankings table
    """
    logger.debug('Creating html table to display power rankings')
    # Set pandas options
    pd.set_option('precision', 3)
    pd.set_option('display.max_colwidth', 10000)
    # Output columns
    out_cols = ['#', '&Delta;', 'Owner', 'Record', 'Power', 'LSQ',
                '2SD', 'Colley', 'AWP', 'SOS', 'Luck', 'Cons', 'Tier']
    # Rename columns for output
    rename_dict = dict(
        power='Power', lsq='LSQ', dom='2SD', col='Colley',
        sos='SOS', luck='Luck', cons='Cons', tier='Tier'
    )
    # Get team owners
    df_power = df_teams[['team_id', 'firstName', 'lastName']].reset_index(drop=True)
    # Concat into 'owner'
    df_power['Owner'] = df_power.apply(
        lambda x: f'{x.get("firstName")} {x.get("lastName")}', axis=1
    )
    # Add in awp and wins/losses
    df_power = pd.merge(
        df_power,
        df_sum[['team_id', 'agg_wpct', 'wins', 'games']]
        .reset_index(drop=True)
        .rename({'agg_wpct': 'AWP'}, axis=1),
        on='team_id'
    )
    # Calculate record
    df_power['Record'] = df_power.apply(
        lambda x: f'{int(x.get("wins"))}-{int(x.get("games"))-int(x.get("wins"))}', axis=1
    )
    # Merge in rankings
    df_power = pd.merge(df_power, df_ranks.rename(rename_dict, axis=1), on='team_id')
    # Get the number ranking for power, add in arrow for movement from previous week
    df_power['#'] = df_power.get('Power').rank(ascending=False).astype(int)
    df_power['&Delta;'] = df_power.apply(
        lambda x: get_arrow(delta=x.get('d_power')), axis=1
    )
    # Build the table
    return (
        df_power[out_cols]
        .to_html(border=0, index=False, escape=False,
                 classes=['table'],
                 table_id='power_table')
    )


def get_player_drop(teams, level=''):
    """Link in drop down list of player pages
     FIXME - what if duplicates

    :param teams: data frame with first and last names
    :param level: define site depth level
    :return: string with html code for player drop down
    """
    li = '<li>'
    il = '</li>'
    a  = '<a href="{}{}_{}/index.html">{}</a>'
    pd.set_option('display.max_colwidth', 10000)
    return (
        teams[['firstName', 'lastName']]
        .reset_index(drop=True)
        .sort_values(['firstName', 'lastName'])
        .apply(lambda x: li + a.format(level, x.firstName, x.lastName, x.firstName + " " + x.lastName) + il,
               axis=1)
        .to_string(index=False)
    )


def make_teams_page(df_teams, df_sum, df_ranks, df_schedule, year, week, league_name, settings):
    """Make teams page with stats, standings, game log, radar plots

    :param df_teams: data frame with basic data about each team
    :param df_sum: data frame with season summary statistics
    :param df_ranks: data frame with rankings for each team
    :param df_schedule: data frame with all game scores
    :param year: current year
    :param week: current week
    :param league_name: league name
    :param settings: dictionary with league settings
    :return: None
    """
    logger.debug('Creating team html pages')
    # local_file: fill {year}, {firstName}, {lastName}
    local_file = 'output/{}/{}_{}/index.html'
    # Define template team page location
    template = pkg_resources.resource_filename('power_ranker', 'docs/template/player.html')
    # Use if player has no ESPN image ...
    stock_url = 'http://www.suttonsilver.co.uk/wp-content/uploads/blog-stock-03.jpg'
    # Ordinal makes numbers like 2nd, 3rd, 4th etc
    ordinal   = lambda n: f'{n}{"tsnrhtdd"[(np.floor(n/10)%10!=1)*(n%10<4)*n%10::4]}'
    # Define columns to grab
    team_cols = ['team_id', 'firstName', 'lastName', 'logo', 'abbrev', 'location', 'nickname',
                 'waiverRank', 'trades', 'acquisitions', 'acquisitionBudgetSpent']
    sum_cols = ['team_id', 'wins', 'games', 'agg_wins', 'agg_games', 'agg_wpct',
                'points_for', 'points_against', 'max_score', 'min_score']
    rank_cols = ['team_id', 'power', 'overall', 'd_power', 'd_overall']
    df_page = df_teams[team_cols].reset_index(drop=True)
    # Merge in summary stats
    df_page = pd.merge(df_page, df_sum[sum_cols].reset_index(drop=True), on='team_id')
    # Merge in rank columns
    df_page = pd.merge(df_page, df_ranks[rank_cols].reset_index(drop=True), on='team_id')
    # Fill missing team logo
    df_page['logo'] = df_page.get('logo').fillna(stock_url)
    # Create owner field
    df_page['owner'] = df_page.apply(lambda x: f'{x.get("firstName")} {x.get("lastName")}', axis=1)
    # Calculate record
    df_page['rec'] = df_page.apply(
        lambda x: f'{int(x.get("wins"))}-{int(x.get("games"))-int(x.get("wins"))}', axis=1
    )
    # Calculate power ranking from power points
    df_page['power_rank'] = df_page.get('power').rank(ascending=False).astype(int)
    # Add in power bar rankings
    df_page['pf_rank'] = df_page.get('points_for').rank(ascending=False).astype(int)
    df_page['pa_rank'] = df_page.get('points_against').rank(ascending=False).astype(int)
    df_page['hs_rank'] = df_page.get('max_score').rank(ascending=False).astype(int)
    df_page['ls_rank'] = df_page.get('min_score').rank(ascending=False).astype(int)
    # Make power bar html codes
    df_page['faab_pb'] = df_page.apply(
        lambda x: make_progress_bar(
            title='FAAB Remaining',
            value=(float(settings.max_faab)-float(x.get('acquisitionBudgetSpent')))*(100./float(settings.max_faab)),
            rank=(int(settings.max_faab)-int(x.get('acquisitionBudgetSpent'))),
            max_FAAB=int(settings.max_faab))
        if settings.use_faab else
        make_progress_bar(
            title='Waiver Priority',
            value=100*float(settings.n_teams+1-x.get('waiverRank'))/float(settings.n_teams),
            rank=ordinal(int(x.get('waiverRank')))), axis=1
    )
    df_page['pf_pb'] = df_page.apply(lambda x: make_progress_bar(
        title=f'Total Points For: {x.get("points_for"):.2f}',
        value=100.*float(settings.n_teams+1-x.get('pf_rank'))/float(settings.n_teams),
        rank=ordinal(int(x.get('pf_rank')))), axis=1)
    df_page['pa_pb'] = df_page.apply(lambda x: make_progress_bar(
        title=f'Total Points Against: {x.get("points_against"):.2f}',
        value=100.*float(settings.n_teams+1-x.get('pa_rank'))/float(settings.n_teams),
        rank=ordinal(int(x.get('pa_rank')))), axis=1)
    df_page['hs_pb'] = df_page.apply(lambda x: make_progress_bar(
        title=f'High Score: {x.get("max_score"):.2f}',
        value=100.*float(settings.n_teams+1-x.get('hs_rank'))/float(settings.n_teams),
        rank=ordinal(int(x.get('hs_rank')))), axis=1)
    df_page['ls_pb'] = df_page.apply(lambda x: make_progress_bar(
        title=f'Low Score: {x.get("min_score"):.2f}',
        value=100.*float(settings.n_teams+1-x.get('ls_rank'))/float(settings.n_teams),
        rank=ordinal(int(x.get('ls_rank')))), axis=1)
    # Define path for each team's local file
    df_page['local_file'] = df_page.apply(
        lambda x: local_file.format(year, x.get('firstName').strip(), x.get('lastName').strip()), axis=1
    )
    # create output and directory if it doesn't exist
    src = ['INSERTOWNER', 'INSERTLEAGUENAME', 'INSERTWEEK', 'IMAGELINK', 'TEAMNAME', 'TEAMABBR',
           'INSERTRECORD', 'INSERTACQUISITIONS', 'INSERTTRADES', 'INSERTWAIVER', 'OVERALLRANK',
           'POWERRANK', 'AGGREGATEPCT', 'RADARPLOT', 'PLAYERDROPDOWN',
           'INSERT_TPF_PB', 'INSERT_TPA_PB', 'INSERT_HS_PB', 'INSERT_LS_PB', 'INSERT_FAAB_PB',
           'INSERTTABLEBODY']
    df_page['rep'] = df_page.apply(
        lambda x: [
            f'{x.get("owner")}',
            league_name,
            f'week{week}',
            f'{x.get("logo")}',
            f'{x.get("location")} {x.get("nickname")}',
            f'{x.get("abbrev")}',
            f'{x.get("rec")}',
            f'{x.get("acquisitions")}',
            f'{x.get("trades")}',
            f'{ordinal(x.get("waiverRank"))}',
            f'{ordinal(x.get("overall"))} <small>{get_arrow(x.get("d_overall"))}</small>',
            f'{ordinal(x.get("power_rank"))} <small>{get_arrow(x.get("d_power"))}</small>',
            f'{x.get("agg_wpct"):.3f} <small>({x.get("agg_wins"):.0f}-{x.get("agg_games")-x.get("agg_wins"):.0f})</small>',
            f'radar_{x.get("team_id"):.0f}.png',
            get_player_drop(teams=df_teams, level='../'),
            x.get('pf_pb'),
            x.get('pa_pb'),
            x.get('hs_pb'),
            x.get('ls_pb'),
            x.get('faab_pb'),
            make_game_log(team_id=x.get('team_id'), df_schedule=df_schedule, df_teams=df_teams, week=week)
        ], axis=1)
    # Output template with replacements
    _ = df_page.apply(
        lambda x: output_with_replace(template=template,
                                      local_file=x.get('local_file'),
                                      src=src,
                                      rep=x.get('rep')), axis=1
    )


def make_power_page(df_teams, df_ranks, df_sum, year, week, league_name):
    """Produces power rankings page

    :param df_teams: data frame with team names
    :param df_ranks: data frame with team rankings
    :param df_sum: data frame with season summary stats
    :param year: current year
    :param week: current week
    :param league_name: name of league
    :return: None
    """
    logger.debug('Creating full power ranking page, inserting league data into template')
    local_file = f'output/{year}/power.html'
    template   = pkg_resources.resource_filename('power_ranker', 'docs/template/power.html')
    src = ['INSERT WEEK', 'INSERTLEAGUENAME', 'PLAYERDROPDOWN', 'INSERT TABLE']
    rep = [f'Week {week+1}',
           league_name,
           get_player_drop(teams=df_teams, level=''),
           make_power_table(df_teams=df_teams, df_ranks=df_ranks, df_sum=df_sum)]
    # Write from template to local, with replacements
    output_with_replace(template, local_file, src, rep)


def make_about_page(df_teams, year, league_name):
    """Produces about page, updating week for power rankings

    :param df_teams: data frame with team names
    :param year: current year
    :param league_name: name of league
    """
    logger.debug('Creating full about page')
    local_file = f'output/{year}/about/index.html'
    template   = pkg_resources.resource_filename('power_ranker', 'docs/template/about.html')
    src = ['PLAYERDROPDOWN', 'INSERTLEAGUENAME']
    rep = [get_player_drop(teams=df_teams, level='../'), league_name]
    # Write from template to local, with replacements
    output_with_replace(template, local_file, src, rep)
    # Copy default images
    in_pics = ['dom_graph.png', 'tiers_example.png']
    for pic in in_pics:
        p = pkg_resources.resource_filename('power_ranker', f'docs/template/{pic}')
        local_p = os.path.join(os.getcwd(), f'output/{year}/about/{pic}')
        shutil.copyfile(p, local_p)


def make_welcome_page(year, week, league_id, league_name):
    """Produces welcome page, with power plot"""
    logger.debug('Creating full welcome page with box plot, filling in weekly data')
    local_file = f'output/{year}/index.html'
    template   = pkg_resources.resource_filename('power_ranker', 'docs/template/welcome.html')
    # Source and replacement strings from template
    src = ['INSERTWEEK', 'INSERTNEXT', 'INSERTLEAGUEID', 'INSERTLEAGUENAME']
    rep = [f'week{week}', f'Week {week+1}', str(league_id), str(league_name)]
    # Write from template to local, with replacements
    output_with_replace(template, local_file, src, rep)


def make_history_page(df_teams, year, league_name, endpoint, params, cookies=None):
    """Produces league history page

    :param df_teams: data frame with team names
    :param year: current year
    :param league_name: name of league
    :param endpoint: history endpoint
    :param params: api params
    :param cookies: cookies for private leagues
    :return: None
    """
    logger.debug('Creating full league history page, filling in league data')
    local_file = f'output/{year}/history/index.html'
    template   = pkg_resources.resource_filename('power_ranker', 'docs/template/history.html')
    option_menu, history_tables, overall_table, medal_table = scrape_history(
        endpoint=endpoint,
        params=params,
        cookies=cookies
    )
    src = ['INSERT_LEAGUE_NAME',
           'PLAYER_DROPDOWN',
           'INSERT_OPTIONS',
           'INSERT_HISTORY_TABLES',
           'INSERT_OVERALL_TABLE',
           'INSERT_MEDAL_TABLE']
    rep = [league_name,
           get_player_drop(teams=df_teams, level='../'),
           option_menu,
           history_tables,
           overall_table,
           medal_table]
    # Write from template to local, with replacements
    output_with_replace(template, local_file, src, rep)


def output_with_replace(template, local_file, src, rep):
    """Write the <template> file contents to <local_file>

    Replace all instances from list <src> with parallel entry in list <rep>
    :param template: template file to be copied
    :param local_file: location to store output
    :param src: source strings to replace
    :param rep: replacement strings to write
    :return: None
    """
    # create directory if doesn't already exist
    os.makedirs(os.path.dirname(local_file), exist_ok=True)
    with open(template, 'r') as f_in, open(local_file, 'w') as f_out:
        for line in f_in:
            for (s, r) in zip(src, rep):
                line = line.replace(s, r)
            f_out.write(line)


def copy_css_js_themes(year):
    """Copy the css and js files to make website look like it is not from 1990

    :param year: current year
    :return: None
    """
    logger.debug('Copying all necessary css and js files for styling output')
    # Specific themes
    in_files = ['about.js', 'theme.js', 'history.js', 'theme.css', 'cover.css']
    for f in in_files:
        template = pkg_resources.resource_filename('power_ranker', f'docs/template/{f}')
        local_file = os.path.join(os.getcwd(), f'output/{year}/{f}')
        shutil.copyfile(template, local_file)
    # Bootstrap dist and assets
    boostrap_dirs = ['dist', 'assets', 'images']
    for b in boostrap_dirs:
        template_dir = pkg_resources.resource_filename('power_ranker', f'docs/template/{b}')
        local_dir = os.path.join(os.getcwd(), f'output/{b}')
        copy_tree(template_dir, local_dir)


def generate_web(df_teams, df_ranks, df_season_summary, df_schedule, year, week, league_id, league_name,
                 settings, endpoint_history, params, cookies=None, doSetup=True):
    """
    Makes power rankings page, team summary page, about page

    :param df_teams: data frame with info about each team
    :param df_ranks: data frame with power rankings
    :param df_season_summary: data frame with summarised season stats
    :param df_schedule: data frame with game data
    :param year: current year
    :param week: current week
    :param league_id: league id
    :param league_name: name of league
    :param settings: league settings
    :param endpoint_history: history api endpoint
    :param params: api parameters
    :param cookies: cookies for private league
    :param doSetup: flag to download bootstrap css/js themes to make html pretty and create the about page
    :return: None
    """
    if doSetup:
        copy_css_js_themes(year=year)
        make_about_page(df_teams=df_teams, year=year, league_name=league_name)
        make_history_page(
            df_teams=df_teams,
            year=year,
            league_name=league_name,
            endpoint=endpoint_history,
            params=params,
            cookies=cookies
        )
    make_power_page(
        df_teams=df_teams,
        df_ranks=df_ranks,
        df_sum=df_season_summary,
        year=year,
        week=week,
        league_name=league_name)
    make_teams_page(
        df_teams=df_teams,
        df_sum=df_season_summary,
        df_ranks=df_ranks,
        df_schedule=df_schedule,
        year=year,
        week=week,
        league_name=league_name,
        settings=settings)
    make_welcome_page(
        year=year,
        week=week,
        league_id=league_id,
        league_name=league_name)

