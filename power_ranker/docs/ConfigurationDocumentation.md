# Configuration File Documentation
The default configuration values are able to give you accurate power rankings, however,
you may need to adjust some parameters to fit your specific league. The only specific
configuration required, is for the [League Info](#league-info) section. The [Tiers](#tiers) section is also 
useful for producing an appropriate amount of tiers.

## League Info
This basic information is needed to access the data for your ESPN league. To find the information,
log into your ESPN league and look at the url.
For example, if your url looks like:

`http://games.espn.com/ffl/clubhouse?leagueId=ZZZZZZ&teamId=X&seasonId=YYYY`

Enter the following information after the "=" in the configuration file

Parameter |What value to enter
--------- | -------------
`league_id` | Part of url after "leagueId=", i.e. ZZZZZZ
`year` | The year you want to retrieve data for, i.e. YYYY
`week` | Which week you want to calculate power rankings for. Must be less than the current week in the season


## Private League
If you are in a public league, leave this section as it is. If you are in a private league, the easiest way to retrieve this cookie information
is to use the `-p` option when using the tool via the command line. 

If you want to retrieve the information yourself, log into your private ESPN league, and look for the cookies for `espn_s2` and `SWID`. 
In Chrome, for example, select "View > Developer > Developer Tools". Then choose the "Application" tab, and navigate to "Cookies". If you
choose to enter the cookies manually, you have to also add `=` after the parameter.

Parameter |What value to enter
----------|-------------------
`s2` | Copy the value of the `espn_s2` cookie
`swid`| Copy the value of `SWID` cookie, including braces


## Tiers
Each week the distribution of power rankings may differ. The website is set up to expect around 5 tiers, so you may need to fine tune these 
settings to achieve the appropriate number of tiers. 

Parameter |What value to enter
----------|------------------
`getPrev`| Set to `False` for the first week of the rankings (no previous rankings to retreive). For all subsequent weeks, set to `True`. Be sure that you run the rankings in the same directory as previous weeks, the tool will search the previous output for the saved rankings. This setting is important to make the arrows on the website reflect accurate movement in the power rankings
`bw`| This is the bandwidth of the tier algorithm. A smaller value will create finer differentiation between power scores to define the tiers. If the value is too small, every team will be it's own tier. You can see the distribution and output of the tiers by locating the file `output/<year>/week<X>/tiers.png`.
`order`|This roughly determines the minimum separation between tiers. If you find lowering the bandwidth doesn't create enough tiers, try lowering the order, and vice versa
`show_plot`|This will display the tiers plot when running the power rankings via command line

## Web
The first time you run the rankings, make sure this is enabled. The code will copy the bootstrap html, css, and javascript template files. Without these 
files the website will look like it is from 1990, and many of the features will not be enabled.

Parameter|What value to enter
---------|------------------
`doSetup`|Set to `True` for the first time you run the rankings, and `False` for subsequent power ranings if you don't want to re-download all the supporting template files

## Playoffs
If you wish to simulate the rest of the season, you can enable this flag. It will fit each teams season score distribution to a gaussian, in order to predict scores in future games. The remaining games in the season are simulated for the specified number of simulations, and the fraction of simulated seasons each team makes the playoffs determines the odds of that team making the playoffs. This feature assumes, at the moment, that your league seeds playoffs by division winners, and then the remaining spots are wildcards. The tie breakers are assumed to be regular season records, and then total points for. After running the simulations, an output image is stored in `output/<year>/<week>/playoff_odds.png` where you can verify the odds have leveled out.

Parameter|What value to enter
---------|-------------------
`doPlayoffs`|Set to `True` if you wish to run the playoff odds simulation. Warning, it may take a very long time if you try early in the season
`num_simulations`|Set to the desired number of simulated seasons. A suggested starting point is between 100k-200k


## Power
If you find the power rankings don't reflect the actual state of your league, you can adjust the weights of the metrics used in the 
overall power ranking. For total rankings with a maximum score near 100, make sure the weights sum to 1.0

Parameter|What value to enter
---------|-------------------
`w_dom`|Weight of the dominance matrix ranking (default 0.18)
`w_lsq`|Weight of the predictive, iterative least squares metric (default 0.18)
`w_col`|Weight of the colley matrix ranking (default 0.18)
`w_awp`|Weight of the aggregate winning percentage (default 0.18)
`w_cons`|Weight of the consistency metric (default 0.10)
`w_sos`|Weight of the strength of schedule metric (default 0.06)
`w_luck`|Weight of the luck ranking boost (default 0.06)
`w_strk`|Weight of the winning streak boost (default 0.06)

## 2SD
You can alter the weights of the linear and square matrices in the two step dominance ranking, as well
as the decay penalty used to devalue games that happened early in the season.

Parameter|What value to enter
---------|-------------------
`sq_weight`|Weight of the square matrix (default 0.25). The linear matrix will be weighted by `1-sq_weight`. In general, the linear matrix should have a larger weight than the square matrix.
`decay_penalty`|A smaller value will weigh older games more closely to recent games (default 0.5)


## LSQ
The method of the iterative least squares ranking is discussed in the "about" section of the website. Refer to the documentaiton there for a more detailed
explanation ofthe algorithm. In general, the sum of `B_w`, `B_r`, and `dS_max` should be 100. To see the output of the rankings, navigate to `output/<year>/week<X>/lsq_iter_rankings.png`. If you alter the default parameters, or you find the LSQ rankings don't seem to make sense, check this output to make sure the rankings are converging.

Parameter|What value to enter
---------|-------------------
`B_w`|Bonus for winning (default 30.0)
`B_r`|Score ratio coefficient (default 35.0)
`dS_max`|Maximum value for the truncated score differential (default 35.0)
`show_plot`|Set to `True` to display the output of the iterative LSQ algorithm when rankings are run via command line

## Colley
The colley matrix algorithm doesn't have any configurable parameters, but you can print the output of the matrix if you want:

Parameter|What value to enter
---------|-------------------
`printMatrix`|Set to `True` if you want to see the raw output of the Colley matrix

## SOS
The strength of schedule uses a ratio of your opponent's ranking, to the average ranking, raised to a power. A higher power creates more separation in SOS, weighting games
against highly ranked opponents more.

Parameter|What value to enter
---------|-------------------
`rank_power`|A typical value is more than 2, but less than 3 (default 2.37)


## Luck
In the luck index, the aggregate winning percentage, and opponents performance metrics have weights.

Parameter|What value to enter
---------|-------------------
`awp_weight`|How much to weight the aggregate winning percentage in the luck metric (default 0.5). The opponents performance metric will be weighted by `1-awp_weight`

## Radar
On the team pages, the radar plots can be configured so that the ranges are more applicable for the scoring of your league. There are six metrics on the ranking plot, you can edit the minimum and maximum values. Separate values with a comma.

Parameter|What value to enter
---------|-------------------
`Y_LOW`|Minimum y-values. The order is win percentage, aggregate winning percentage, strength of schedule, points per game, margin of victory, and winning streak. (Default:0, 0, 0, 50, -60, -5 )
`Y_HIGH`|Maximum y-values. The order is the same as for `Y_LOW`. (Default: 1, 1, 1, 150, 40, 5)
