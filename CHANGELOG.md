# Change Log
All notable changes to this project will be documented in this file.

## [Unreleased]


## [2.0.0](https://github.com/rynecarbone/power_ranker/tree/2.0.0) - 2019-09-12
- Major changes related to updated v3 of API, old endpoints no longer valid
- Refactoring code to use pandas and vectorized calculations
- Added code to calculate league history and display on history page
- Updated text at bottom of each page, added links to league history
- Fixed bug in MOV calculation for radar plot

## [1.1.1](https://github.com/rynecarbone/power_ranker/tree/1.1.1) - 2018-09-19
### Fixed
- Merged matplotlib deprecation warning
- Fixed matplotlib bug on radar plot where rounding created weird decimal labels
### Added
- Added missing Manifest.in file for github repository clone

## [1.1.0](https://github.com/rynecarbone/power_ranker/tree/1.1.0) - 2017-11-08
### Added
- Playoff simulations: fit each teams weekly score distribution with a gaussian. Use the gaussian fit to predict the scores for that team for the rest of the regular season games. Simulate the rest of the season for many iterations
- Cleaned up some of the documentation

## [1.0.0](https://github.com/rynecarbone/power_ranker/tree/1.0.0) - 2017-10-05
### Changed
- Multiple instances of application for separate league settings 
are now handled in one application with the help of a configuration file
- Ranking normalizations are standardized
- Website generation will now copy bootrap css/js files to make raw html pretty

### Fixed
- Reorganized power ranking code into a neater package
- Fixed bug where teamId can skip numbers, and be larger than size of league if some teams have left your league from previous seasons
- Some metrics weighted a bit improperly in final power rankings

### Added
- Private league access via command line log-in or user-inputed cookies
- Retreival of league settings to handle FAAB/waiver leagues
- Configuration file to modify power ranking settings
- Created command line scripts for downloading configuration file locally, and running rankings
- Created package to install with pip
- Description of LSQ metric
- Added a favicon to website
