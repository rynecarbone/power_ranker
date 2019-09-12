[![version](https://img.shields.io/badge/version-2.0.1-blue.svg)](https://github.com/rynecarbone/power_ranker/blob/master/CHANGELOG.md) [![PyPI version](https://badge.fury.io/py/power-ranker.svg)](https://badge.fury.io/py/power-ranker)

# Power Ranker
A tool for scraping fantasy football stats from ESPN leagues, creating power rankings, collecting previous season standings, and publishing to a website.

*Update 2019-09-12*: version 2.0.1 is now working with the newest v3 of ESPN api

# Check out package

```python3
pip3 install power_ranker
```

OR

```bash
git clone https://github.com/rynecarbone/power_ranker
cd power_ranker
python3 setup.py install
```

# Generate a Configuration File
Download a local copy of the default configuration file. Once you have the file, fill in your league name, league id, year, and week (that you want to make rankings for). You can also adjust any of the settings that control the algorithms in the power rankings, or use the default values. For detailed instructions, see the [Configuration File Documentation](https://github.com/rynecarbone/power_ranker/blob/master/power_ranker/docs/ConfigurationDocumentation.md)

To download a local copy of the configuration file, use the -dc (--download-config) option. If you are in a private league, use the -p (--private-league) option to log into your ESPN account and retreive cookie information:
```bash
power_ranker -dc 
Creating copy of: /Path/To/power_ranker/docs/default_config.cfg
To local destination: /Path/To/Current/Dir/MY_LOCAL_CONFIG.cfg
```
or 
```bash
power_ranker -dc -p
Creating copy of: /Path/To/power_ranker/docs/default_config.cfg
To local destination: /Path/To/Current/Dir/MY_LOCAL_CONFIG.cfg
Username: <Enter ESPN Login>
Password: <Enter ESPN Password>
```

Use your favorite editor to open the local "MY_LOCAL_CONFIG.cfg" file and edit it.

# Command line
After you have added your league information, pass the configuration file as an argument with the -c (--config-file) option. If you haven't already, you can add the -p (--private-league) option to log into your ESPN account and retreive cookie information.
```bash
power_ranker -c MY_LOCAL_CONFIG.cfg 
Using MY_LOCAL_CONFIG.cfg to generate power rankings

Week 3 Power Rankings
...
```
Alternatively, pass the league id, year, and week as command line arguments (-l --leagueid, -y --year, -w --week) and all other default power ranking settings will be used. Pass the -p option if in a private league.
```bash
power_ranker -l 123456 -y 2019 -w 1 
Using user input:
League ID: 123456
Year: 2019
Week: 1
Creating copy of: /Path/To/power_ranker/docs/default_config.cfg
To local destination: /Path/To/Current/Dir/MY_LOCAL_CONFIG.cfg

Week 1 Power Rankings 
...
```
After you run the rankings, a template website will be generated in a directory titled "output/". Follow the instructions on how to [Publish Power Rankings to a Website](https://github.com/rynecarbone/power_ranker/blob/master/power_ranker/docs/PublishingWebsite.md) if you want to share the output with your league. To add your own summary to the week's power rankings, edit the file "output/2017/power.html". Find the commented out section:
```html
<!--- <p>FIXME! FIXME!
         Add your own commentary here! New write-up here!
         Or just leave the rankings</p> -->
```
Remove the `<!--` and `-->` comment delimeters, and edit the text inside the paragraph markers (`<p>`, `</p>`).

# Playoff Odds
See [Configuration File Documentation](https://github.com/rynecarbone/power_ranker/blob/master/power_ranker/docs/ConfigurationDocumentation.md) for detailed instructins on how to alter the configuration file to run simulated playoff odds. You can control the number of simulations to run, where each simulation uses this season's scores to predict the outcomes of the remaining games. The fraction of simulations in which a team makes the playoffs determines that team's estimated odds of making the playoffs.

# League History
The first time you run power_ranker, make sure 'do_Setup' option is set to True. It will search for and scrape stats for
all previous seasons. A League history page will be created displaying the standings and stats from each of these past seasons. 

# Example Output
After successfully running the code, the generated website files should appear like the examples below:
- Power rankings [welcome page](https://rynecarbone.github.io/ff/2017/example/)
- Power rankings [table](https://rynecarbone.github.io/ff/2017/example/power.html) with metric breakdown
- [About page](https://rynecarbone.github.io/ff/2017/example/about/), explaining briefly the algorithms
- [Team summary pages](https://rynecarbone.github.io/ff/2017/example/Marie_Curie/) showing stats for each team, with a game log
- [History page](https://rynecarbone.github.io/ff/2017/example/history/index.html) showing the final season standings for all previous seasons

# Credit
The code to extract league info from hidden ESPN API, including retreiving league settings and accessing private league data, is largely thanks to
Rich Barton's espnff package: https://github.com/rbarton65/espnff.
