# Change Log
All notable changes to this project will be documented in this file.

## [Unreleased]
- Updating website generation code
- Now will copy bootrap css/js files to make raw html pretty
- Creating command line scripts for downloading configuration file locally, and running rankings
- Creating package to install with pip
- Fixed bug where teamId can skip numbers, and be larger than size of league if some teams have left your league from previous seasons

## 0.0.2 - 2017-09-13
### Changed
- Multiple instances of application for separate league settings 
are now handled in one application with the help of the configuration file

### Fixed
- Reorganized power ranking code into a neater package

### Added
- Configuration file to modify power ranking settings

