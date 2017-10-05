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
`bw`| This is the bandwidth of the tier algorithm. A smaller value will create finer differentiation between power scores to define the tiers. If the value is too small, every team will be it's own tier. You can see the distribution and output of the tiers by locating the file `output/<year>/weekX/tiers.png`.
`order`|This roughly determines the minimum separation between tiers. If you find lowering the bandwidth doesn't create enough tiers, try lowering the order, and vice versa
`show_plot`|This will display the tiers plot when running the power rankings via command line
