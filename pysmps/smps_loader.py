# -*- coding: utf-8 -*-
"""
Created on Sun Sep  8 13:28:53 2019

@author: Julian Märte
"""

import re
import math
import copy
import warnings
from mps_loader import MPS, read_mps

TIME_FILE_PERIODS_MODE = "PERIODS"
TIME_FILE_PERIODS_MODE_EXPLICIT = "PERIODS_EXPLICIT"
TIME_FILE_PERIODS_MODE_IMPLICIT = "PERIODS_IMPLICIT"
TIME_FILE_ROWS_MODE = "ROWS"
TIME_FILE_COLS_MODE = "COLUMNS"

TIME_MODE = {TIME_FILE_PERIODS_MODE: 0, TIME_FILE_PERIODS_MODE_EXPLICIT: 1,
              TIME_FILE_PERIODS_MODE_IMPLICIT: 2, TIME_FILE_ROWS_MODE: 3,
              TIME_FILE_COLS_MODE: 4}


STOCH_FILE_INDEP_MODE = "INDEP"
STOCH_FILE_INDEP_DISCRETE_MODE = "INDEP_DISCRETE"
STOCH_FILE_INDEP_DISTRIB_MODE = "INDEP_DISTRIB"
STOCH_FILE_INDEP_SUB_MODE = "SUB"
STOCH_FILE_BLOCKS_MODE = "BLOCKS"
STOCH_FILE_BLOCKS_DISCRETE_MODE = "BLOCKS_DISCRETE"
STOCH_FILE_BLOCKS_SUB_MODE = "BLOCKS_SUB"
STOCH_FILE_BLOCKS_LINTR_MODE = "BLOCKS_LINTR"
STOCH_FILE_BLOCKS_BL_MODE = "BL"
STOCH_FILE_SCENARIOS_MODE = "SCENARIOS"


STOCH_MODE = {STOCH_FILE_INDEP_MODE: 0, STOCH_FILE_INDEP_DISCRETE_MODE: 1,
              STOCH_FILE_INDEP_DISTRIB_MODE: 2, STOCH_FILE_INDEP_SUB_MODE: 3,
              STOCH_FILE_BLOCKS_MODE: 4, STOCH_FILE_BLOCKS_BL_MODE: 5,
              STOCH_FILE_BLOCKS_DISCRETE_MODE: 6, STOCH_FILE_BLOCKS_SUB_MODE: 7,
              STOCH_FILE_BLOCKS_LINTR_MODE: 8, STOCH_FILE_BLOCKS_BL_MODE: 9}



class SMPS:
    
    def __init__(self, mps):
        self.mps = mps
        
        
        self.rows = self.mps.constraint_names()
        self.cols = self.mps.variable_names()
        
        self.row_periods = {}
        self.col_periods = {}
        
        self.distributions = {}
        self.blocks = {}
        
        self.curr_block = None
        self.curr_block_period = None
        
        self.curr_lintr_period = None
        self.curr_lintr_block = None
        self.curr_lintr = None
        self.curr_lintr_name = None
        
    
    
    
    # TIME RELATED FUNCTIONS
    def start_implicit(self):
        self.last_row_period = None
        self.last_row = -1
        self.last_col_period = None
        self.last_col = -1
        self.implicit = True

    def finalize_implicit(self):
        if self.implicit:
            self._add_col_period_implicit(None, len(self.cols))
            self._add_row_period_implicit(None, len(self.rows))

    def get_periods(self):
        return list(self.periods.keys())
    
    def _add_row_period_implicit(self, period, r):
        if self.last_row_period:
            if self.last_row_period in self.row_periods:
                self.row_periods[self.last_row_period].extend(self.rows[(self.last_row):r])
            else:
                self.row_periods[self.last_row_period] = copy.deepcopy(self.rows[(self.last_row):r])
        self.last_row_period = period
        self.last_row = r
        
    def _add_col_period_implicit(self, period, c):
        if self.last_col_period:
            if self.last_col_period in self.col_periods:
                self.col_periods[self.last_col_period].extend(self.cols[(self.last_col):c])
            else:
                self.col_periods[self.last_col_period] = copy.deepcopy(self.cols[(self.last_col):c])
        self.last_col_period = period
        self.last_col = c
    
    def _add_row_period_explicit(self, period, row):
        if period in self.row_periods:
            self.row_periods[period].append(row)
        else:
            self.row_periods[period] = [row]
        
    def _add_col_period_explicit(self, period, col):
        if period in self.col_periods:
            self.col_periods[period].append(col)
        else:
            self.col_periods[period] = [col]
    
    # STOCH RELATED FUNCTIONS
    def _add_discrete_distrib(self, period, col, row, value, probability):
        key = tuple([col, row])
        if period in self.distributions:
            if key in self.distributions[period]:
                self.distributions[period][key]["probabilities"][value] = probability
            else:
                self.distributions[period][key] = {"type": "DISCRETE", "probabilities": {value: probability}}
        else:
            self.distributions[period] = {key: {"type": "DISCRETE", "probabilities": {value: probability}}}
    
    def _add_distrib(self, period, col, row, distrib, params):
        key = tuple([col, row])
        if period in self.distributions:
            if key in self.distributions[period]:
                raise ValueError("There were two different distributions given for the same element in one period!")
            else:
                self.distributions[period][key] = {"type": distrib}
                self.distributions[period][key].update(params)
        else:
            self.distributions[period] = {key: {"type": distrib}}
            self.distributions[period][key].update(params)
    
    def attach_block(self, period, block, _type, probability):
        if period not in self.blocks:
            self.blocks[period] = {}
        self.detach_block()
        
        self.curr_block_period = period
        self.curr_block = block
        if block not in self.blocks[period]:
            if _type == "DISCRETE":
                self.blocks[period][block] = {"type": _type, "probabilities": {}}
            else:
                self.blocks[period][block] = {"type": _type}
            self.new_block = True
            self.curr_elements = []
            self.curr_basecase = []
        else:
            self.new_block = False
            self.curr_elements = self.blocks[period][block]["elements"]
            self.curr_basecase = copy.copy(self.blocks[period][block]["basecase"])
        self.curr_probability = probability
        
    
    def add_discrete_block_distrib(self, col, row, value):
        if self.new_block:
            self.curr_elements.append(tuple([col, row]))
            self.curr_basecase.append(value)
        else:
            self.curr_basecase[self.curr_elements.index(tuple([col, row]))] = value
            
    def add_sub_block_distrib(self, col, row):
        if self.curr_block:
            self.curr_elements.append(tuple([col, row]))
    
    def detach_block(self):
        if not self.curr_block:
            return
        if self.new_block:
            self.blocks[self.curr_block_period][self.curr_block]["elements"] = self.curr_elements
            for t in self.curr_elements:
                self.distributions[self.curr_block_period][t] = {"type": "BLOCK", "block": self.curr_block}
        if self.blocks[self.curr_block_period][self.curr_block]["type"] == "DISCRETE":
            if self.new_block:
                self.blocks[self.curr_block_period][self.curr_block]["basecase"] = self.curr_basecase
            self.blocks[self.curr_block_period][self.curr_block]["probabilities"][tuple(self.curr_basecase)] = self.curr_probability
        
        self.curr_block = None
        self.curr_block_period = None
        self.curr_basecase = None
        self.curr_probability = None
        self.curr_elements = None
        self.curr_basecase = None

    def attach_lintr(self, period, block, lintr, distrib, parameters):
        self.curr_lintr_name = lintr
        self.curr_lintr_period = period
        self.curr_lintr_block = block
        self.curr_lintr = {"type": distrib, "coefficients": {}}
        self.curr_lintr.update(parameters)
        
    def add_to_lintr(self, col, row, coeff):
        if self.curr_lintr_block:
            self.curr_lintr["coefficients"][tuple([col, row])] = coeff
        
    def detach_lintr(self):
        if not self.curr_lintr_name:
            return
        self.blocks[self.curr_lintr_period][self.curr_lintr_block][self.curr_lintr_name] = self.curr_lintr
        
        self.curr_lintr_period = None
        self.curr_lintr_block = None
        self.curr_lintr_name = None
        self.curr_lintr = None
        
    # used to produce dict
    def __iter__(self):
        for field in self.mps:
            yield field
        
        yield ("row_periods", self.row_periods)
        yield ("col_periods", self.col_periods)
        yield ("distributions", self.distributions)
        yield ("blocks", self.blocks)

def _read_tim(smps, path):
    mps = smps.mps
    
    mode = -1
    
    explicit = False
    rows = smps.rows
    cols = smps.cols
    
    with open(path, "r") as reader:
        for line in reader:
            if line.startswith("*"):
                continue

            line = re.split(" |\t", line)
            line = [x.strip() for x in line]
            line = list(filter(None, line))
            
            if len(line) == 0:
                continue
            if line[0] == "*":
                continue
            if line[0] == "ENDATA":
                break
            if line[0] == "TIME":
                assert line[1] == mps.name
                
                
            elif line[0] == TIME_FILE_PERIODS_MODE:
                if len(line) > 1 and line[1] == "EXPLICIT":
                    mode = TIME_MODE[TIME_FILE_PERIODS_MODE_EXPLICIT]
                    explicit = True
                else: # in case it is blank, IMPLICIT or anything else set it to implicit.
                    mode = TIME_MODE[TIME_FILE_PERIODS_MODE_IMPLICIT]
                    smps.start_implicit()
                    
                    
            elif line[0] == TIME_FILE_ROWS_MODE:
                mode = TIME_MODE[TIME_FILE_ROWS_MODE]
                
                
            elif line[0] == TIME_FILE_COLS_MODE:
                mode = TIME_MODE[TIME_FILE_COLS_MODE]
                
                
            elif mode == TIME_MODE[TIME_FILE_PERIODS_MODE_IMPLICIT]:
                smps._add_col_period_implicit(line[2], cols.index(line[0]))
                smps._add_row_period_implicit(line[2], rows.index(line[1]))
                
                
            elif mode == TIME_MODE[TIME_FILE_ROWS_MODE]:
                smps._add_row_period_explicit(line[1], line[0])
                
                
            elif mode == TIME_FILE_COLS_MODE:
                smps._add_col_period_explicit(line[1], line[0])
                
                
    smps.finalize_implicit()


def _read_sto(smps, path):
    mps = smps.mps
    
    mode = -1
    distribution = None
    
    with open(path, "r") as reader:
        for line in reader:
            if line.startswith("*"):
                continue

            line = re.split(" |\t", line)
            line = [x.strip() for x in line]
            line = list(filter(None, line))
            
            if len(line) == 0:
                continue
            if line[0] == "*":
                continue
            if line[0] == "ENDATA":
                break
            if line[0] == "STOCH":
                assert line[1] == mps.name
                
                
            elif line[0] == STOCH_FILE_INDEP_MODE:
                if line[1] == "DISCRETE":
                    mode = STOCH_MODE[STOCH_FILE_INDEP_DISCRETE_MODE]
                elif line[1] in ["UNIFORM", "NORMAL", "BETA", "GAMMA", "LOGNORMAL"]:
                    mode = STOCH_MODE[STOCH_FILE_INDEP_DISTRIB_MODE]
                elif line[1] == "SUB":
                    mode = STOCH_MODE[STOCH_FILE_INDEP_SUB_MODE]
                    warnings.warn(".sto file contains SUB section - this indicates that the user has to have a subroutine to generate distributions for a given row/col combination!")
                distribution = line[1]
                
                smps.detach_lintr()
                smps.detach_block()
                
            elif line[0] == STOCH_FILE_BLOCKS_MODE:
                if line[1] == "DISCRETE":
                    mode = STOCH_MODE[STOCH_FILE_BLOCKS_DISCRETE_MODE]
                elif line[1] == "SUB":
                    mode = STOCH_MODE[STOCH_FILE_BLOCKS_SUB_MODE]
                elif line[1] == "LINTR":
                    mode = STOCH_MODE[STOCH_FILE_BLOCKS_LINTR_MODE]
                
                smps.detach_lintr()
                smps.detach_block()
            
            elif line[0] == STOCH_FILE_SCENARIOS_MODE:
                raise ValueError("SCENARIOS are currently not implemented!")
                
                
            elif mode == STOCH_MODE[STOCH_FILE_INDEP_DISCRETE_MODE]:
                smps._add_discrete_distrib(line[3], line[0], line[1], float(line[2]), float(line[4]))
                
                
            elif mode == STOCH_MODE[STOCH_FILE_INDEP_DISTRIB_MODE]:
                smps._add_distrib(line[3], line[0], line[1], distribution, {"parameters": [float(line[2]), float(line[4])]})
            
            
            elif mode == STOCH_MODE[STOCH_FILE_INDEP_SUB_MODE]:
                smps._add_distrib(line[3], line[0], line[1], distribution, {})
                
            
            elif mode == STOCH_MODE[STOCH_FILE_BLOCKS_DISCRETE_MODE]:
                if line[0] == "BL":
                    smps.attach_block(line[2], line[1], "DISCRETE", float(line[3]))
                else:
                    smps.add_discrete_block_distrib(line[0], line[1], float(line[2]))
            
            
            elif mode == STOCH_MODE[STOCH_FILE_BLOCKS_SUB_MODE]:
                if line[0] == "BL":
                    smps.attach_block(line[2], line[1], "SUB", 0)
                else:
                    smps.add_sub_block_distrib(line[0], line[1])
            
            
            elif mode == STOCH_MODE[STOCH_FILE_BLOCKS_LINTR_MODE]:
                if line[0] == "BL":
                    smps.detach_lintr()
                    smps.attach_block(line[2], line[1], "LINTR", 0)
                elif line[0] == "RV":
                    if smps.curr_block:
                        period = smps.curr_block_period
                        block = smps.curr_block
                    else:
                        period = smps.curr_lintr_period
                        block = smps.curr_lintr_block
                    smps.detach_block()
                    smps.detach_lintr()
                    if line[2] in ["UNIFORM", "NORMAL", "BETA", "GAMMA", "LOGNORMAL"]:
                        smps.attach_lintr(period, block, line[1], line[2], {"parameters": [float(line[3]), float(line[5])]})
                    elif line[2] == "CONSTANT":
                        smps.attach_lintr(period, block, line[1], line[2], {})
                else:
                    if smps.curr_block:
                        smps.add_sub_block_distrib(line[0], line[1])
                    elif smps.curr_lintr_block:
                        smps.add_to_lintr(line[0], line[1], float(line[2]))
            
        smps.detach_block()
        smps.detach_lintr()
            

def read_smps(path):
    smps = SMPS(read_mps(path + ".cor"))
    _read_tim(smps, path + ".tim")
    _read_sto(smps, path + ".sto")
    return smps
    