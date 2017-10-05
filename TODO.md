# Cleaning up code
### Team sorting
- Replace the sorted team lambda functions, with the member function of the league class.
- pass the sort key as a string
- optionally specify if in reverse order

### Website generation
- Maybe run rankings for previous week if not already saved somewhere ... ? Might be tricky if it rewrites over something you didn't want it to.
- Add documentaiton for LSQ: http://www.phys.utk.edu/sorensen/ranking/Documentation/Sorensen_documentation_v1.pdf
- Revise documentaiton about normalizing funcitons
- Luck is bonus for bad luck

### Classes
- Make Web a class?

### Command line arguments
- Attribute code for settings/private league

# Algorithms
- Look at normalization funcitons -- standardize?
- Make most metrics max at 1 ... how to scale evenly, maybe stretch from 0 to 1?
- LSQ -- verify it is doing what I think it is


# Further Things to Develop

### Playoffs
- Figure out how to handle playoff weeks automatically
- If week input is too large, maybe stop at last game of regular season for now

### Summary plot of rankings vs week
- read the txt files
- do both for power rankings and espn rankings
- maybe add to team page?

### Testing
- Implement some unit tests

### Error Handling
- Something breaks with number of teams changing (see Physics League...)
- Have more than zero error handling

