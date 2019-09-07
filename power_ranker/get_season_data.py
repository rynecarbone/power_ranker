#!/usr/bin/env python

"""Retrieve Season Data

FIXME maybe want to sort by team_id for all built tables?
"""

import logging
import pandas as pd
import numpy as np
from itertools import *
from operator import itemgetter

__author__ = 'Ryne Carbone'

logger = logging.getLogger(__name__)


def build_owner_table(data):
    """Create data frame with league owner information

    :param data: json data from api with 'members' keyword
    :return: data frame with columns first, last, and id
    """
    member_cols = ['firstName', 'lastName', 'id']
    df_members = pd.DataFrame(data.get('members'), columns=member_cols)
    return df_members


def build_team_table(data):
    """Create data frame with team information

    :param data: json data from api with 'teams' keyword
    :return: data frame with team data
    """
    teams_cols = [
        'id', 'location', 'nickname', 'abbrev', 'logo', 'divisionId', 'transactionCounter',
        'waiverRank', 'primaryOwner', 'draftDayProjectedRank', 'currentProjectedRank', 'playoffSeed'
    ]
    df_teams = pd.DataFrame(data.get('teams'), columns=teams_cols)
    # Expand transaction columns to grab trades, acquisitions, and faab spent
    df_teams = pd.concat([
        df_teams.drop(['transactionCounter'], axis=1),
        df_teams.transactionCounter.apply(pd.Series)[['trades', 'acquisitions', 'acquisitionBudgetSpent']]
    ], axis=1)
    # Grab owner information
    df_members = build_owner_table(data=data)
    # Combine team information with owners
    df_teams = (
        df_teams
        .merge(df_members, how='left', left_on='primaryOwner', right_on='id')
        .rename(columns={'id_x': 'team_id'})
        .drop('id_y', axis=1)
    )
    # Extract primary owner SWID (inside braces {})
    df_teams.primaryOwner = df_teams.primaryOwner.str.extract('.*{(.*)}.*')
    return df_teams


def build_schedule_table(data):
    """Build table with matchup data

    Include home/away, scores, result, matchup period ids
    :param data: json data from api with 'schedule' keyword
    :return: data frame with row for each matchup and summary of results
    """
    # Define columns to select
    schedule_cols = ['id', 'matchupPeriodId', 'home', 'away', 'winner']
    home_away_cols = ['teamId', 'pointsByScoringPeriod', 'totalPoints']
    # Rename columns for more clarity
    rename_dict_away = {
        'teamId': 'away_id',
        'pointsByScoringPeriod': 'away_points_scoring_period',
        'totalPoints': 'away_total_points'
    }
    rename_dict_home = {
        'teamId': 'home_id',
        'pointsByScoringPeriod': 'home_points_scoring_period',
        'totalPoints': 'home_total_points'
    }
    # Plop data into a frame
    df_schedule = pd.DataFrame(data.get('schedule'), columns=schedule_cols)
    # Identify rows where teams are listed as nan -- looks like bye weeks
    missing_teams = (df_schedule.away.isnull() | df_schedule.home.isnull())
    #bye_weeks = df_schedule[missing_teams].get(['id', 'matchupPeriodId'])
    df_schedule = df_schedule[~missing_teams].reset_index(drop=True)
    # Extract the relevant columns from nested home/away dicts and concat
    # Note: 'pointsByScoringPeriod' only appears after the games have been played
    df_schedule = pd.concat([
        (pd.DataFrame(df_schedule.away.tolist(), columns=home_away_cols).rename(rename_dict_away, axis=1)),
        (pd.DataFrame(df_schedule.home.tolist(), columns=home_away_cols).rename(rename_dict_home, axis=1)),
        df_schedule.drop(['away', 'home'], axis=1)
    ], axis=1)
    # For completed games, extract home/away pointsByScoringPeriod
    completed_games = (df_schedule.winner != 'UNDECIDED')
    if sum(completed_games) == 0:
        logger.warning('No games have been completed, schedule is empty.')
        raise ValueError('No games have been completed, schedule is empty.')
    df_schedule.loc[completed_games, 'away_points_scoring_period'] = \
        df_schedule[completed_games].apply(lambda x: x.away_points_scoring_period.get(str(x.matchupPeriodId)), axis=1)
    df_schedule.loc[completed_games, 'home_points_scoring_period'] = \
        df_schedule[completed_games].apply(lambda x: x.home_points_scoring_period.get(str(x.matchupPeriodId)), axis=1)
    return df_schedule


def build_season_summary_table(df_schedule, week):
    """Build a summary view of season results

    :param df_schedule: schedule table with all matchup data
    :param week: matchup id of current week
    """
    away_sum = (
        df_schedule
        .query(f'matchupPeriodId <= {week} & winner!="UNDECIDED"')
        .groupby('away_id')
        .agg(away_wins=('winner', lambda x: sum(x == 'AWAY')),
             away_games=('matchupPeriodId', 'size'),
             away_points_for=('away_total_points', 'sum'),
             away_points_against=('home_total_points', 'sum'))
        .reset_index()
        .rename({'away_id': 'team_id'}, axis=1)
    )
    home_sum = (
        df_schedule
        .query(f'matchupPeriodId <= {week} & winner!="UNDECIDED"')
        .groupby('home_id')
        .agg(home_wins=('winner', lambda x: sum(x == 'HOME')),
             home_games=('matchupPeriodId', 'size'),
             home_points_for=('home_total_points', 'sum'),
             home_points_against=('away_total_points', 'sum'))
        .reset_index()
        .rename({'home_id': 'team_id'}, axis=1)
    )
    df_sum = pd.merge(home_sum, away_sum, on='team_id', how='outer').fillna(0)
    if df_sum.empty:
        logger.info('No games have been logged yet')
        raise ValueError('No games have been logged yet')
    df_sum['wins'] = df_sum.apply(lambda x: x.get('home_wins') + x.get('away_wins'), axis=1)
    df_sum['games'] = df_sum.apply(lambda x: x.get('home_games') + x.get('away_games'), axis=1)
    df_sum['points_for'] = df_sum.apply(lambda x: x.get('home_points_for') + x.get('away_points_for'), axis=1)
    df_sum['points_against'] = df_sum.apply(lambda x: x.get('home_points_against') + x.get('away_points_against'), axis=1)
    df_sum['streak'] = df_sum.apply(lambda x: calc_streak(df_schedule, x.get('team_id'), week), axis=1)
    # Add aggregate wins to the season summary
    agg_wins = calc_agg_wins(df_schedule, week)
    df_sum = pd.merge(df_sum, agg_wins, on='team_id')
    return df_sum


def calc_agg_wins(df_schedule, week):
    """Calculate aggregate wins and games played

    :param df_schedule: schedule table with all matchup data
    :param week: matchup id of current week
    :return: data frame with aggregate wins, games played, and wpct
    """
    # Make a row for each team for each week
    away_games = (
        df_schedule
        .query(f'matchupPeriodId <= {week} & winner!="UNDECIDED"')
        [['matchupPeriodId', 'away_id', 'away_total_points']]
        .rename({'away_id': 'team_id', 'away_total_points': 'points'}, axis=1)
    )
    home_games = (
        df_schedule
        .query(f'matchupPeriodId <= {week} & winner!="UNDECIDED"')
        [['matchupPeriodId', 'home_id', 'home_total_points']]
        .rename({'home_id': 'team_id', 'home_total_points': 'points'}, axis=1)
    )
    # Combine all rows
    all_games = pd.concat([away_games, home_games], axis=0)
    # Rank each team by points scored each week to calculate 'aggregate' wins
    all_games['agg_wins'] = all_games.groupby('matchupPeriodId').points.rank(ascending=True) - 1
    # Summarise wins over the season
    agg_wins = (
        all_games
        .sort_values(['matchupPeriodId', 'points'])
        .groupby('team_id')
        .agg(agg_wins=('agg_wins', 'sum'))
        .reset_index()
    )
    # Count total games
    agg_wins['agg_games'] = all_games.matchupPeriodId.size - all_games.matchupPeriodId.unique().size
    # Calculate winning percentage
    agg_wins['agg_wpct'] = agg_wins['agg_wins'] / agg_wins['agg_games']
    return agg_wins


def calc_streak(df_schedule, team, week):
    """Calculate current winning/losing streak

    :param df_schedule: data frame with scores and team id for each game
    :param team: team id
    :param week: current week
    :return: returns current streak for team
    """
    l_mov = (
        df_schedule
        .query(f'(home_id=={team} | away_id=={team}) & (matchupPeriodId <= {week} & winner != "UNDECIDED")')
        .sort_values('matchupPeriodId')
        .apply(lambda x:
               x.home_total_points - x.away_total_points if x.home_id == team else
               x.away_total_points - x.home_total_points, axis=1).values
    )
    # Break up MOV list into consecutive streaks (i.e. same sign)
    l_streaks = get_streaks(l_mov=l_mov)
    # Grab most recent streak, return length (and sign)
    current_streak = l_streaks[-1]
    return len(current_streak)*np.sign(current_streak[0])


def get_streaks(l_mov):
    """Break up list of MOV into streaks

    Algorithm from: https://stackoverflow.com/questions/38708692/identify-if-list-has-consecutive-elements-that-are-equal-in-python
    :param l_mov: list of margin of victory
    :return: list of streaks
    """
    return [list(map(itemgetter(1), g))
            for k, g
            in groupby(enumerate(l_mov), lambda x: np.sign(x[1]))]


