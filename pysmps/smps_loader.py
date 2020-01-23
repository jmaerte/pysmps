# -*- coding: utf-8 -*-
"""
Created on Sun Sep  8 13:28:53 2019

@author: Julian Märte
"""

import re
import numpy as np
import math
import copy

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
STOCH_FILE_BLOCKS_BL_MODE = "BL"

# BLOCKS modes
STOCH_FILE_BLOCKS_DISCRETE_MODE = "BLOCKS_DISCRETE"
STOCH_FILE_BLOCKS_SUB_MODE = "BLOCKS_SUB"
STOCH_FILE_BLOCKS_LINTR_MODE = "BLOCKS_LINTR"

#INDEP modes
STOCH_FILE_INDEP_DISCRETE_MODE = "INDEP_DISCRETE"
STOCH_FILE_INDEP_DISTRIB_MODE = "INDEP_DISTRIB"

class Block(object):
    
    period = ""
    probabilities = []
    cases = []
    
    def __init__(self, period):
        self.period = period

    def add(self, probability):
        self.probabilities.append(probability)
        if len(self.cases) > 0:
            self.cases.append(copy.deepcopy(self.cases[0]))
        else:
            self.cases.append({"c": {}, "A": {}, "b": {}})
    
    def add_case(self, probability, case):
        self.probabilities.append(probability)
        self.cases.append(case)
    
    def append_matrix(self, i, j, value):
        self.cases[-1]["A"][(i,j)] = value
    
    def append_obj(self, j, value):
        self.cases[-1]["c"][j] = value
    
    def append_rhs(self, i, rhs, value):
        try:
            self.cases[-1]["b"][rhs][i] = value
        except:
            self.cases[-1]["b"][rhs] = {i: value}

"""
Implements the random variables that are linear transforms of distributions.
places save the locations of the random variables in the LP
matrix has as i-th entry the coefficients of the random variables
variables holds the distributions that are linearly combined as dicts, e.g.
{"type": "normal", "parameters": {"mu": mu, "sigma**2": sigma**2}}
"""
class LinearTransform(object):
    _mapping = {}
    places = []
    variables = []
    matrix = np.matrix([[]])
    period = ""
    
    def __init__(self, period):
        self.period = period

    def add_location(self, i, j, description):
        self._mapping[(i,j)] = len(self.places)
        self.places.append(description)
        
    def add_distribution(self, type_of, name, parameters):
        self.variables.append({"type": type_of, "name": name, "parameters": parameters})
        if self.matrix.shape[1] == 0:
            matrix = np.zeros((len(self.places),1))
        else:
            matrix = np.append((matrix, np.zeros((len(self.places), 1))), axis = 1)
    def add_value(self, i, j, value):
        self.matrix[self._mapping[(i,j)],-1] = value

class SubRoutine(object):
    subroutine_locations = []
    period = ""
    
    def __init__(self, period):
        self.period = period
        
    def add(self, location):
        self.subroutine_locations.append(location)

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
            
def _load_stoch_file(path, name, objective_name, row_names, col_names, rhs_names):
    mode = ""
    last_block = ""
    blocks = {}
    independent_variables = {}
    
    is_rv = False
    indep_distribution = ""
    
    
    with open(path + ".sto", "r") as reader:
        for line in reader:
            line = re.split(" |\t", line)
            line = [x.strip() for x in line]
            line = list(filter(None, line))
            
            if line[0] == "STOCH":
                assert line[1] == name
            if line[0] == "ENDATA":
                break
            if line[0] == "*":
                continue
            if line[0] == STOCH_FILE_BLOCKS_MODE:
                if line[1] == "LINTR":
                    mode = STOCH_FILE_BLOCKS_LINTR_MODE
                elif line[1] == "SUB":
                    mode = STOCH_FILE_BLOCKS_SUB_MODE
                elif line[1] == "DISCRETE":
                    mode = STOCH_FILE_BLOCKS_DISCRETE_MODE
                else:
                    raise Exception("BLOCKS section was initiated without another tag (LINTR, SUB, DISCRETE).")
            elif line[0] == STOCH_FILE_INDEP_MODE:
                if line[1] == "DISCRETE":
                    mode = STOCH_FILE_INDEP_DISCRETE_MODE
                elif line[1] in ["UNIFORM", "NORMAL", "BETA", "GAMMA", "LOGNORMAL"]:
                    mode = STOCH_FILE_INDEP_DISTRIB_MODE
                    indep_distribution = line[1]
            # BLOCKS mode handler
            elif mode == STOCH_FILE_BLOCKS_DISCRETE_MODE:
                if line[0] == STOCH_FILE_BLOCKS_BL_MODE:
                    if line[1] not in blocks:
                        blocks[line[1]] = Block(line[2])
                    blocks[line[1]].add(float(line[3]))
                    last_block = line[1]
                elif last_block != "":
                    i, j = _get_indices(row_names, col_names, line)
                    if i < 0:
                        blocks[last_block].append_obj(j, float(line[2]))
                    elif j < 0:
                        blocks[last_block].append_rhs(i, line[0], float(line[2]))
                    else:
                        blocks[last_block].append_matrix(i, j, float(line[2]))
            elif mode == STOCH_FILE_BLOCKS_LINTR_MODE:
                if line[0] == STOCH_FILE_BLOCKS_BL_MODE:
                    is_rv = False
                    if line[1] not in blocks:
                        blocks[line[1]] = LinearTransform(line[2])
                    last_block = line[1]
                elif line[0] == "RV":
                    if line[2] == "NORMAL":
                        blocks[last_block].add_distribution("N(mu, sigma**2)", line[1], {"mu": float(line[3]), "sigma**2": float(line[5])})
                    elif line[2] == "UNIFORM":
                        blocks[last_block].add_distribution("U(a, b)", line[1], {"a": float(line[3]), "b": float(line[5])})
                    elif line[2] == "CONSTANT":
                        blocks[last_block].add_distribution("CONST. 1", line[1], {})
                    else:
                        raise Exception("Looks like you are using an unknown distribution to this script. For now we only support NORMAL, UNIFORM and CONSTANT distributions.")
                    is_rv = True
                elif not is_rv and last_block != "":
                    i, j = _get_indices(row_names, col_names, line)
                    if i < 0:
                        description = {"type": line[1], "VAR": j}
                    elif j < 0:
                        description = {"type": line[0], "ROW": i}
                    else:
                        description = {"type": "matrix", "ROW": i, "COL": j}
                    blocks[last_block].add_location(i, j, description)
                elif is_rv:
                    i, j = _get_indices(row_names, col_names, line)
                    blocks[last_block].add_value(i, j, float(line[2]))
            elif mode == STOCH_FILE_BLOCKS_SUB_MODE:
                if line[0] == STOCH_FILE_BLOCKS_BL_MODE:
                    if line[1] not in blocks:
                        blocks[line[1]] = SubRoutine(line[2])
                    last_block = line[1]
                elif last_block != "":
                    i, j = _get_indices(row_names, col_names, line)
                    if i < 0:
                        description = {"type": line[1], "VAR": j}
                    elif j < 0:
                        description = {"type": line[0], "ROW": i}
                    else:
                        description = {"type": "matrix", "ROW": i, "COL": j}
                    blocks[last_block].add(description)
            # INDEP mode handler
            elif mode == STOCH_FILE_INDEP_DISCRETE_MODE:
                i, j = _get_indices(row_names, col_names, line)
                if (i,j) in independent_variables:
                    independent_variables[(i,j)]["distrib"].append((float(line[2]), float(line[4])))
                else:
                    if i < 0:
                        description = {"type": line[1], "VAR": j}
                    elif j < 0:
                        description = {"type": line[0], "ROW": i}
                    else:
                        description = {"type": "matrix", "ROW": i, "COL": j}
                    independent_variables[(i,j)] = {"position": description, "period": line[3], "distrib": [(float(line[2]), float(line[4]))]}
            elif mode == STOCH_FILE_INDEP_DISTRIB_MODE:
                i, j = _get_indices(row_names, col_names, line)
                if (i,j) in independent_variables:
                    raise Exception("Tried to set independent distribution of an element twice.")
                else:
                    if i < 0:
                        description = {"type": line[1], "VAR": j}
                    elif j < 0:
                        description = {"type": line[0], "ROW": i}
                    else:
                        description = {"type": "matrix", "ROW": i, "COL": j}
                    if indep_distribution == "NORMAL":
                        independent_variables[(i,j)] = {"position": description, "period": line[3],
                                          "distrib": {"type": "N(mu, sigma**2)", "parameters": {"mu": float(line[2]), "sigma**2": float(line[4])}}}
                    elif indep_distribution == "UNIFORM":
                        independent_variables[(i,j)] = {"position": description, "period": line[3],
                                          "distrib": {"type": "U(a, b)", "parameters": {"a": float(line[2]), "b": float(line[4])}}}
                    elif indep_distribution == "BETA":
                        independent_variables[(i,j)] = {"position": description, "period": line[3],
                                          "distrib": {"type": "B(p, q)", "parameters": {"p": float(line[2]), "q": float(line[4])}}}
                    elif indep_distribution == "GAMMA":
                        independent_variables[(i,j)] = {"position": description, "period": line[3],
                                          "distrib": {"type": "G(p, b)", "parameters": {"p": float(line[2]), "b": float(line[4])}}}
                    elif indep_distribution == "LOGNORMAL":
                        independent_variables[(i,j)] = {"position": description, "period": line[3],
                                          "distrib": {"type": "LN(mu, sigma**2)", "parameters": {"mu": float(line[2]), "sigma**2": float(line[4])}}}
    return blocks, independent_variables
def _get_indices(row_names, col_names, line):
    i = -1
    j = -1
    try:
        j = col_names.index(line[0])
    except:
        pass
    try:
        i = row_names.index(line[1])
    except:
        pass
    return i, j
# public
def load_mps(path):
    mode = ""
    name = None
    objective_name = None
    row_names = []
    types = []
    col_names = []
    col_types = []
    A = np.matrix([[]])
    c = np.array([])
    rhs_names = []
    rhs = {}
    bnd_names = []
    bnd = {}
    integral_marker = False
    
    with open(path, "r") as reader:
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
                if len(line) > 1 and line[1] == "'MARKER'":
                    if line[2] == "'INTORG'":
                        integral_marker = True
                    elif line[2] == "'INTEND'":
                        integral_marker = False
                    continue
                try:
                    i = col_names.index(line[0])
                except:
                    if A.shape[1] == 0:
                        A = np.zeros((len(row_names), 1))
                    else:
                        A = np.concatenate((A, np.zeros((len(row_names), 1))), axis = 1)
                    col_names.append(line[0])
                    col_types.append(integral_marker * 'integral' + (not integral_marker) * 'continuous')
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
    return name, objective_name, row_names, col_names, col_types, types, c, A, rhs_names, rhs, bnd_names, bnd

def load_smps(path):
    name, objective_name, row_names, col_names, col_types, types, c, A, rhs_names, rhs, bnd_names, bnd = load_mps(path + ".cor")
    periods, row_periods, col_periods = _load_time_file(path, name, row_names, col_names)
    blocks, independent_variables = _load_stoch_file(path, name, objective_name, row_names, col_names, rhs_names)
    return {"name": name, "objective_name": objective_name, "constraints": [(row_names[i], row_periods[i], types[i]) for i in range(len(row_names))], "variables": [(col_names[i], col_periods[i], col_types[i]) for i in range(len(col_names))], "c": c, "A": A, "rhs_names": rhs_names, "rhs": rhs, "bounds": bnd, "periods": periods, "blocks": blocks, "independent_variables": independent_variables}
    


def load_2stage_problem(path):
    d = load_smps(path)
    print("Loaded problem", d["name"])
    print("Assuming", d["periods"][0], "to be the deterministic period and", d["periods"][1], "to be the stochastic one.")
    assert len(d["periods"]) == 2
    deterministic_rows = [i for i in range(len(d["constraints"])) if d["constraints"][i][1] == d["periods"][0]]
    stochastic_rows = [i for i in range(len(d["constraints"])) if d["constraints"][i][1] == d["periods"][1]]
    deterministic_cols = [i for i in range(len(d["variables"])) if d["variables"][i][1] == d["periods"][0]]
    stochastic_cols = [i for i in range(len(d["variables"])) if d["variables"][i][1] == d["periods"][1]]
    
    A = d["A"][deterministic_rows,:][:,deterministic_cols]
    assert np.count_nonzero(d["A"][deterministic_rows,:][:,stochastic_cols]) == 0
    W = d["A"][stochastic_rows,:][:,stochastic_cols]
    T_matrix = d["A"][stochastic_rows,:][:,deterministic_cols]
    
    c = d["c"][deterministic_cols]
    q_array = d["c"][stochastic_cols]
    
    assert len(d["rhs_names"]) == 1
    b = d["rhs"][d["rhs_names"][0]][deterministic_rows]
    h_array = d["rhs"][d["rhs_names"][0]][stochastic_rows]
    
    for key, bound in d["bounds"].items():
        assert np.count_nonzero(bound["LO"]) == 0
        assert np.sum(np.isinf(bound["UP"])) == bound["UP"].size
    
    # Assert A and W are not stochastic
    for key, block in d["blocks"].items():
        if isinstance(block, Block):
            for stochastic in block.cases:
                for entries in stochastic["A"]:
                    assert not (entries[0] in stochastic_rows and entries[1] in stochastic_cols)
                    assert not (entries[0] in deterministic_rows and entries[1] in deterministic_cols)
                    assert not (entries[0] in deterministic_rows and entries[1] in stochastic_cols)
    for indep in d["independent_variables"]:
        assert not (indep[0] in stochastic_rows and indep[1] in stochastic_cols)
        assert not (indep[0] in deterministic_rows and indep[1] in deterministic_cols)
        assert not (indep[0] in deterministic_rows and indep[1] in stochastic_cols)
    
    # Assert stochastic elements appear only in phase 2
    for key, block in d["blocks"].items():
        assert block.period == d["periods"][1]
    for key, indep in d["independent_variables"].items():
        assert indep["period"] == d["periods"][1]
    
    determ_cnstr = [row[2] for row in d["constraints"] if row[1] == d["periods"][0]]
    stochastic_cnstr = [row[2] for row in d["constraints"] if row[1] == d["periods"][1]]
    #deterministic
    determ_ineq = sum(x != "E" for x in determ_cnstr)
    c = np.concatenate((c, np.zeros(determ_ineq)))
    T_matrix = np.concatenate((T_matrix, np.zeros((T_matrix.shape[0], determ_ineq))), axis = 1)
    A_add = np.zeros((A.shape[0], determ_ineq))
    k = 0
    for i in range(A.shape[0]):
        if determ_cnstr[i] != "E":
            A_add[i, k] = 1 if determ_cnstr[i] == "L" else -1
            k = k + 1
    A = np.concatenate((A, A_add), axis = 1)
    
    stochastic_ineq = sum(x != "E" for x in stochastic_cnstr)
    q_array = np.concatenate((q_array, np.zeros(stochastic_ineq)))
    W_add = np.zeros((W.shape[0], stochastic_ineq))
    k = 0
    for i in range(W.shape[0]):
        if stochastic_cnstr[i] != "E":
            W_add[i, k] = 1 if stochastic_cnstr[i] == "L" else -1
            k = k + 1
    W = np.concatenate((W, W_add), axis = 1)
    
    T = [T_matrix]
    h = [h_array]
    q = [q_array]
    p = [1]
    
    for key, indep in d["independent_variables"].items():
        T_next = []
        h_next = []
        q_next = []
        p_next = []
        for vp in indep["distrib"]:
            for i in range(len(T)):
                if key[0] < 0:
                    j = stochastic_cols.index(key[1])
                    # objective
                    add = np.copy(q[i])
                    add[j] = vp[0]
                    q_next.append(add)
                    p_next.append(p[i] * vp[1])
                    T_next.append(T[i])
                    h_next.append(h[i])
                elif key[1] < 0:
                    k = stochastic_rows.index(key[0])
                    add = np.copy(h[i])
                    add[k] = vp[0]
                    h_next.append(add)
                    p_next.append(p[i] * vp[1])
                    T_next.append(T[i])
                    q_next.append(q[i])
                else:
                    k = stochastic_rows.index(key[0])
                    j = deterministic_cols.index(key[1])
                    add = np.copy(T[i])
                    add[k, j] = vp[0]
                    T_next.append(add)
                    p_next.append(p[i] * vp[1])
                    q_next.append(q[i])
                    h_next.append(h[i])
        T = T_next
        h = h_next
        q = q_next
        p = p_next

    for key, block in d["blocks"].items():
        T_next = []
        h_next = []
        q_next = []
        p_next = []
        if isinstance(block, Block):
            for i in range(len(block.probabilities)):
                for t in range(len(T)):
                    # handle T
                    T_add = np.copy(T[t])
                    h_add = np.copy(h[t])
                    q_add = np.copy(q[t])
                    for location, value in block.cases[i]["A"].items():
                        k = stochastic_rows.index(location[0])
                        j = deterministic_cols.index(location[1])
                        T_add[k, j] = value
                    for location, value in block.cases[i]["b"].items():
                        k = stochastic_rows.index(location)
                        h_add[k] = value
                    for location, value in block.cases[i]["c"].items():
                        j = deterministic_cols.index(location)
                        q_add[j] = value
                    T_next.append(T_add)
                    h_next.append(h_add)
                    q_next.append(q_add)
                    p_next.append(p[t] * block.probabilities[i])
        T = T_next
        h = h_next
        q = q_next
        p = p_next
    
    assert len(T) == len(h)
    assert len(T) == len(p)
    assert len(T) == len(q)
    
    return {"name": d["name"], "c": c, "A": A, "b": b, "q": q, "h": h, "T": T, "W": W, "p": p}
    