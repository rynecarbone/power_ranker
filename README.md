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

# Command line
First you need to download the configuration file locally with the -dc option (--download-config)
```bash
power_ranker -dc
```
Adjust the league name, league id, year, and week in the file, then pass the configuration file as an argument with the -c (--config-file) option
```bash
power_ranker -c MY_LOCAL_CONFIG.cfg
```
Alternatively, pass the league name, league id, year, and week as command line arguments (-n --name, -l --leagueid, -y --year, -w --week) and all other default power ranking settings will be used
```bash
power_ranker -n 'My League Name' -l '123456' -y 2017 -w 3
```

# Manipulate League objects in python interpreter
-Update instructions here


# Credit
The code to extract league info from hidden ESPN API is largely thanks to
Rich Barton's espnff package (used v 1.0.0 2016-10-04):
https://github.com/rbarton65/espnff
League class and team class templates also inspired from that code. 
