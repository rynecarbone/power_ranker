#!/usr/bin/env python

"""Create Radar plots to summarize team statistics

TODO: Update with plotnine if they ever implement coord_polar
"""

import logging
from pathlib import Path
import numpy as np
import pandas as pd
from matplotlib import pylab as pl

__author__ = 'Ryne Carbone'

logger = logging.getLogger(__name__)


class Radar:
    """Creates a radar plot for each team """
    def __init__(self, fig, titles, labels, rect=None):
        if rect is None:
            rect = [0.05, 0.05, 0.85, 0.85]
        self.n = len(titles)
        self.angles = [a if a <= 360.
                       else a - 360.
                       for a in np.arange(90, 90+360, 360.0/self.n)]
        self.axes = [fig.add_axes(rect, projection="polar", label='axes{:d}'.format(i))
                     for i in range(self.n)]
        self.ax = self.axes[0]
        self.ax.set_thetagrids(self.angles, labels=titles, fontsize=12, weight='bold')
        for ax in self.axes[1:]:
            ax.patch.set_visible(False)
            ax.grid(False)
            ax.xaxis.set_visible(False)
        for ax, angle, label in zip(self.axes, self.angles, labels):
            ax.set_rgrids(range(1, 6), angle=angle, labels=['{:.1f}'.format(l) for l in label])
            ax.spines["polar"].set_visible(False)
            ax.set_ylim(0, 5)

    def plot(self, values, *args, **kw):
        """plots the data"""
        angle = np.deg2rad(np.r_[self.angles, self.angles[0]])
        values = np.r_[values, values[0]]
        self.ax.plot(angle, values, *args, **kw)
        self.ax.fill(angle, values, *args, **kw)


def make_radar(team, year, week, Y_LOW=None, Y_HIGH=None):
    """
    Makes radar plots and saves them to folder

    y_low is list of minimum y values (win pct, awp, sos, ppg, mov, streak)
    y_high is list of maximum y values (win pct, awp, sos, ppg, mov, streak)

    :param team: object with rankings for team
    :param year: current year
    :param week: current week
    :param Y_LOW: lower axis limits
    :param Y_HIGH: upper axis limits
    :return: None
    """
    if not Y_LOW:
        Y_LOW = [0, 0, .4, 50, -60, -5]
    if not Y_HIGH:
        Y_HIGH = [1, 1, 1.4, 150, 40, 5]
    fig = pl.figure(figsize=(6, 6))
    titles = ['Win Pct', 'AWP', 'SOS', 'PPG', 'MOV', 'Streak']
    # Recalculate low y-values at second tick
    Y_LOW2 = [0.2*(h-l)+l for (l, h) in zip(Y_LOW, Y_HIGH)]
    labels = [
        np.linspace(Y_LOW2[0], Y_HIGH[0], num=5),
        np.linspace(Y_LOW2[1], Y_HIGH[1], num=5),
        np.linspace(Y_LOW2[2], Y_HIGH[2], num=5),
        np.linspace(Y_LOW2[3], Y_HIGH[3], num=5),
        np.linspace(Y_LOW2[4], Y_HIGH[4], num=5),
        np.linspace(Y_LOW2[5], Y_HIGH[5], num=5)
    ]
    scale = [5./(Y_HIGH[x]-Y_LOW[x]) for x in range(6)]
    offset = [(0 - Y_LOW[x]) for x in range(6)]
    # Calculate stats to plot for team
    t_ranks = [
        team.get('wpct'),
        team.get('agg_wpct'),
        team.get('sos'),
        team.get('ppg'),
        team.get('mov'),
        team.get('streak')
    ]
    # Normalize to the axes scales
    t_ranks_norm = [(t_ranks[x]+offset[x])*scale[x] for x in range(6)]
    # Create the plot
    radar = Radar(fig, titles, labels)
    radar.plot(t_ranks_norm, "-", lw=2, color="g", alpha=0.4) #, label=team.teamName)
    # Save the output
    fig.set_size_inches(6, 6, forward=True)
    out_dir = Path(f'output/{year}/week{week}/radar_plots')
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f'radar_{int(team.get("team_id"))}.png'
    fig.savefig(out_file)
    logger.debug(f'Saved radar plot for team {team.get("team_id")} to local destination {out_file.resolve()}')


def save_team_radar_plots(df_rank, df_season_summary, year, week, Y_LOW, Y_HIGH):
    """Save radar plots for each team

    :param df_rank: data frame wit calculated rankings
    :param df_season_summary: data frame with summary stats
    :param year: current year
    :param week: current week
    :param Y_LOW: lower limits for plots
    :param Y_HIGH: upper limits for plots
    :return: None
    """
    # Select relevant summary stats
    df_radar = (
        df_season_summary
        [['team_id', 'wins', 'games', 'points_for', 'points_against', 'agg_wpct', 'streak']]
        .reset_index(drop=True))
    # Calculate wpct, mov, ppg
    df_radar['wpct'] = df_radar.apply(lambda x: x.get('wins')/x.get('games'), axis=1)
    df_radar['mov'] = df_radar.apply(lambda x: (x.get('points_for') - x.get('points_against'))/x.get('games'), axis=1)
    df_radar['ppg'] = df_radar.apply(lambda x: x.get('points_for')/x.get('games'), axis=1)
    # Add in sos
    df_radar = pd.merge(df_radar, df_rank[['team_id', 'sos']].reset_index(drop=True), on='team_id')
    # Make sure team id is int -- used in plot name
    df_radar['team_id'] = df_radar.get('team_id').astype(int)
    # Save plot for each team
    _ = df_radar.apply(lambda x: make_radar(team=x, year=year, week=week, Y_LOW=Y_LOW, Y_HIGH=Y_HIGH), axis=1)






