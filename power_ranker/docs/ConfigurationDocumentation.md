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

Parameter | What value to enter
--------- | -------------
`league_id` | Part of url after "leagueId=", i.e. ZZZZZZ
`year` | The year you want to retrieve data for, i.e. YYYY
`week` | Which week you want to calculate power rankings for. Must be less than the current week in the season


## Tiers

Discuss tiers
