# Cleaning up code
### Team sorting
- Replace the sorted team lambda functions, with the member function of the league class.
- pass the sort key as a string
- optionally specify if in reverse order

### Website generation
- Maybe run rankings for previous week if not already saved somewhere ... ? Might be tricky if it rewrites over something you didn't want it to.
- What if multiple players wiht same name (drop down menu, folders, etc...)
- Should the code be a class or something?
- Add flavicon
- See if FAAB league or not -> change FAAB bar to waiver order
- Make sure team names are capitalized

### Command line arguments
- Make argparse -> refine a bit

# Algorithms
- Look at normalization funcitons -- standardize?
- LSQ -- verify it is doing what I think it is

# Further Things to Develop

### Summary plot of rankings vs week
- read the txt files
- do both for power rankings and espn rankings
- maybe add to team page?

### Make Documentation for Publishing Website
- Move /output folder somewhere better? 
- How to make it easier to upload to github pages?
- Make sure paths in code still work

### Testing
- Implement some unit tests

### Error Handling
- Something breaks with number of teams changing (see Physics League...)
- Have more than zero error handling

# Misc.
- power_ranker/power_ranker.py doesn't run as a script from directory with setup.py --> figure out how to fix the relative import thingy ... maybe just remove it...
