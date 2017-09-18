# README
Finish instructions on how to run

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
Download a local copy of the default configuration file. Once you have the file, file in your league name, league id, year, and week (that you want to make rankings for). You can also adjust any of the settings that control the algorithms in the power rankings, or use the default values. To download a local copy of the configuration file, use the -dc (--download-config) option:
```bash
power_ranker -dc
```
Use your favorite editor to open the local "MY_LOCAL_CONFIG.cfg" file and edit it.

# Command line
After you have added your league information, pass the configuration file as an argument with the -c (--config-file) option
```bash
power_ranker -c MY_LOCAL_CONFIG.cfg
```
Alternatively, pass the league name, league id, year, and week as command line arguments (-n --name, -l --leagueid, -y --year, -w --week) and all other default power ranking settings will be used
```bash
power_ranker -n 'My League Name' -l 123456 -y 2017 -w 3
```

# Manipulate League objects in python interpreter
After you have added your league information to the local configuration file, you can open python3 interpreter:
```python3
python3
from power_ranker.league import League
my_config = 'MY_LOCAL_CONFIG.cfg'
my_league = League(my_config)
my_league.get_power_rankings()
```


# Credit
The code to extract league info from hidden ESPN API is largely thanks to
Rich Barton's espnff package (used v 1.0.0 2016-10-04):
https://github.com/rbarton65/espnff
League class and team class templates also inspired from that code. 
