# coding=utf-8
import numpy as np
from scipy.linalg import solve

class Colley(object):
  '''Calculates rating using Colley matrix'''
	
  def __init__(self, week, N_teams, printM=False):	
    self.week    = week
    self.N_teams = N_teams
    self.printM  = printM
    self.C       = np.zeros(shape=(self.N_teams, self.N_teams)) # array N_teams x N_teams
    self.b       = np.zeros(self.N_teams) # vector with weighted record
	
  def _calc_matrix(self, teams):		
    ''' C_ij = -n_ij              (number of games team i played team j)
  	 		C_ii = 2 + n_i            (total games team i played)
  	 		b_i  = 1 + 0.5(w_i - l_i) (can introduce weights as well) '''
    for i,team in enumerate(teams):
	    # Calculate entries in row for team i
      for j in range(self.N_teams):
	      # how many total games team i played
	      if j == int(team.teamId)-1:
	        self.C[i][j] = 2 + self.week
	      # how many games team i played team j
	      else:
	        n_ij = 0
	        for opponent in team.stats.schedule[:self.week]:
	          if int(opponent.teamId)-1 == j:
	            n_ij += 1
	        self.C[i][j] = -n_ij
      self.b[i] = 1 + 0.5*( int(team.stats.wins) - int(team.stats.losses) ) # add weight? 

  def _solve_matrix(self, teams):
    '''Solve the matrix equation'''
    res = solve(self.C,self.b)
    if self.printM:
	    self._print_colley(self.C, self.b, res)
    for i,team in enumerate(teams):
	    team.rank.col = res[i]
  
  def _print_colley(self,C,b,res):
    '''Print the Colley matrix'''
    print('\nColley matrix: \nC r = b') 
    for i,r in enumerate(C):
	    s = ''
	    for x in r:
	      s += '%s  '%x
	    s += '\t%s\t'%res[i]
	    if i == 5:
	      s += '='
	    print("%s\t%s"%(s,b[i]))
  
  def get_ranks(self, teams):
    '''Create the colley matrix and save ranks to teams'''
    self._calc_matrix(teams)
    self._solve_matrix(teams)
