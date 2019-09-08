# -*- coding: utf-8 -*-
"""
Created on Sun Sep  8 13:28:53 2019

@author: Julian Märte
"""

import re
import numpy as np
import math

CORE_FILE_ROW_MODE = "ROWS"
CORE_FILE_COL_MODE = "COLUMNS"
CORE_FILE_RHS_MODE = "RHS"
CORE_FILE_BOUNDS_MODE = "BOUNDS"

CORE_FILE_BOUNDS_MODE_NAME_GIVEN = "BOUNDS_NAME"
CORE_FILE_BOUNDS_MODE_NO_NAME = "BOUNDS_NO_NAME"
CORE_FILE_RHS_MODE_NAME_GIVEN = "RHS_NAME"
CORE_FILE_RHS_MODE_NO_NAME = "RHS_NO_NAME"

ROW_MODE_OBJ = "N"


TIME_FILE_PERIODS_MODE = "PERIODS"
TIME_FILE_PERIODS_MODE_EXPLICIT = "PERIODS_EXPLICIT"
TIME_FILE_PERIODS_MODE_IMPLICIT = "PERIODS_IMPLICIT"
TIME_FILE_ROWS_MODE = "ROWS"
TIME_FILE_COLS_MODE = "COLUMNS"


STOCH_FILE_SIMPLE_MODE = "SIMPLE"
STOCH_FILE_CHANCE_MODE = "CHANCE"
STOCH_FILE_SCENARIOS_MODE = "SCENARIOS"
STOCH_FILE_NODES_MODE = "NODES"
STOCH_FILE_INDEP_MODE = "INDEP"
STOCH_FILE_BLOCKS_MODE = "BLOCKS"
STOCH_FILE_DISTRIB_MODE = "DISTRIB"

# private
                    
def _load_time_file(path, name, row_names, col_names):
    mode = ""
    rows = False
    cols = False
    explicit = False
    periods = []
    row_periods = [""] * len(row_names)
    col_periods = [""] * len(col_names)
    
    with open(path + ".tim", "r") as reader:
        for line in reader:
            line = re.split(" |\t", line)
            line = [x.strip() for x in line]
            line = list(filter(None, line))
            
            if line[0] == "*":
                continue
            if line[0] == "ENDATA":
                break
            if line[0] == "TIME":
                assert line[1] == name
            elif line[0] == TIME_FILE_PERIODS_MODE:
                if len(line) > 1 and line[1] == "EXPLICIT":
                    mode = TIME_FILE_PERIODS_MODE_EXPLICIT
                    explicit = True
                else: # in case it is blank, IMPLICIT or anything else set it to implicit.
                    mode = TIME_FILE_PERIODS_MODE_IMPLICIT
            elif line[0] == TIME_FILE_ROWS_MODE:
                rows = True
                mode = TIME_FILE_ROWS_MODE
            elif line[0] == TIME_FILE_COLS_MODE:
                cols = True
                mode = TIME_FILE_COLS_MODE
            elif mode == TIME_FILE_PERIODS_MODE_IMPLICIT:
                try:
                    k = periods.index(line[2])
                except:
                    periods.append(line[2])
                j = col_names.index(line[0])
                i = row_names.index(line[1])
                col_periods[j:] = [line[2]] * (len(col_periods) - j)
                row_periods[i:] = [line[2]] * (len(row_periods) - i)
            elif mode == TIME_FILE_ROWS_MODE:
                try:
                    i = periods.index(line[1])
                except:
                    periods.append(line[1])
                row_periods[row_names.index(line[0])] = line[1]
            elif mode == TIME_FILE_COLS_MODE:
                try:
                    i = periods.index(line[1])
                except:
                    periods.append(line[1])
                col_periods[col_names.index(line[0])] = line[1]
    if explicit and not (rows and cols):
        raise Exception("Time format was explicit but some rows/cols don't have temporal information!")
    return periods, row_periods, col_periods
            
def _load_stoch_file(path, name, row_names, col_names):
    simple_names = []
    
    
    with open(path + ".sto", "r") as reader:
        for line in reader:
            line = re.split(" |\t", line)
            line = [x.strip() for x in line]
            line = list(filter(None, line))
            
            if line[0] == "STOCH":
                assert line[1] == name
            if line[0] == 

# public
def load_lp(path):
    mode = ""
    name = None
    objective_name = None
    row_names = []
    types = []
    col_names = []
    A = np.matrix([[]])
    c = np.array([])
    rhs_names = []
    rhs = {}
    bnd_names = []
    bnd = {}
    
    with open(path + ".cor", "r") as reader:
        for line in reader:
            line = re.split(" |\t", line)
            line = [x.strip() for x in line]
            line = list(filter(None, line))
            
            if line[0] == "ENDATA":
                break
            if line[0] == "*":
                continue
            if line[0] == "NAME":
                name = line[1]
            elif line[0] in [CORE_FILE_ROW_MODE, CORE_FILE_COL_MODE]:
                mode = line[0]
            elif line[0] == CORE_FILE_RHS_MODE and len(line) <= 2:
                if len(line) > 1:
                    rhs_names.append(line[1])
                    rhs[line[1]] = np.zeros(len(row_names))
                    mode = CORE_FILE_RHS_MODE_NAME_GIVEN
                else:
                    mode = CORE_FILE_RHS_MODE_NO_NAME
            elif line[0] == CORE_FILE_BOUNDS_MODE and len(line) <= 2:
                if len(line) > 1:
                    bnd_names.append(line[1])
                    bnd[line[1]] = {"LO": np.zeros(len(col_names)), "UP": np.repeat(math.inf, len(col_names))}
                    mode = CORE_FILE_BOUNDS_MODE_NAME_GIVEN
                else:
                    mode = CORE_FILE_BOUNDS_MODE_NO_NAME
            elif mode == CORE_FILE_ROW_MODE:
                if line[0] == ROW_MODE_OBJ:
                    objective_name = line[1]
                else:
                    types.append(line[0])
                    row_names.append(line[1])
            elif mode == CORE_FILE_COL_MODE:
                try:
                    i = col_names.index(line[0])
                except:
                    if A.shape[1] == 0:
                        A = np.zeros((len(row_names), 1))
                    else:
                        A = np.concatenate((A, np.zeros((len(row_names), 1))), axis = 1)
                    col_names.append(line[0])
                    c = np.append(c, 0)
                    i = -1
                j = 1
                while j < len(line) - 1:
                    if line[j] == objective_name:
                        c[i] = float(line[j + 1])
                    else:
                        A[row_names.index(line[j]), i] = float(line[j + 1])
                    j = j + 2
            elif mode == CORE_FILE_RHS_MODE_NAME_GIVEN:
                if line[0] != rhs_names[-1]:
                    raise Exception("Other RHS name was given even though name was set after RHS tag.")
                rhs[line[0]][row_names.index(line[1])] = float(line[2])
            elif mode == CORE_FILE_RHS_MODE_NO_NAME:
                try:
                    i = rhs_names.index(line[0])
                except:
                    rhs_names.append(line[0])
                    rhs[line[0]] = np.zeros(len(row_names))
                    i = -1
                rhs[line[0]][row_names.index(line[1])] = float(line[2])
            elif mode == CORE_FILE_BOUNDS_MODE_NAME_GIVEN:
                if line[1] != bnd_names[-1]:
                    raise Exception("Other BOUNDS name was given even though name was set after BOUNDS tag.")
                if line[0] in ["LO", "UP"]:
                    bnd[line[1]][line[0]][col_names.index(line[2])] = float(line[3])
                elif line[0] == "FX":
                    bnd[line[1]]["LO"][col_names.index(line[2])] = float(line[3])
                    bnd[line[1]]["UP"][col_names.index(line[2])] = float(line[3])
                elif line[0] == "FR":
                    bnd[line[1]]["LO"][col_names.index(line[2])] = -math.inf
            elif mode == CORE_FILE_BOUNDS_MODE_NO_NAME:
                try:
                    i = bnd_names.index(line[1])
                except:
                    bnd_names.append(line[1])
                    bnd[line[1]] = {"LO": np.zeros(len(col_names)), "UP": np.repeat(math.inf, len(col_names))}
                    i = -1
                if line[0] in ["LO", "UP"]:
                    bnd[line[1]][line[0]][col_names.index(line[2])] = float(line[3])
                elif line[0] == "FX":
                    bnd[line[1]]["LO"][col_names.index(line[2])] = float(line[3])
                    bnd[line[1]]["UP"][col_names.index(line[2])] = float(line[3])
                elif line[0] == "FR":
                    bnd[line[1]]["LO"][col_names.index(line[2])] = -math.inf
    return name, objective_name, row_names, col_names, types, c, A, rhs_names, rhs, bnd_names, bnd

def load_smps(path):
    name, objective_name, row_names, col_names, types, c, A, rhs_names, rhs, bnd_names, bnd = _load_core_file(path)
    periods, row_periods, col_periods = _load_time_file(path, name, row_names, col_names)
    
    
    
    
    
    