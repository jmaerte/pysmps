import re
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

COL_TYPES = {1: "Integer", 0: "Continuous"}
BND_TYPES = ["LO", "UP"]
BND_TYPE = {"LO": "bnd_lower", "UP": "bnd_upper"}
BND_FUNC = {"LO": max, "UP": min}


# public
def load_mps(path):
    mode = ""
    objective = dict(name = "", coefficients=[])
    constraints = dict()
    variable = {}
    rhs_names = []
    
    integral_marker = False
    
    with open(path, "r") as reader:
        
        line_idx = 0
        bars = 0
        
        for line in reader:
            if line.startswith("*"):
                continue

            line = re.split(" |\t", line)
            line = [x.strip() for x in line]
            line = list(filter(None, line))
            
            if len(line) == 0:
                continue
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
                    for key, c in constraints.items():
                        c["bounds"][line[1]] = 0
                    mode = CORE_FILE_RHS_MODE_NAME_GIVEN
                else:
                    mode = CORE_FILE_RHS_MODE_NO_NAME
            elif line[0] == CORE_FILE_BOUNDS_MODE and len(line) <= 2:
                if len(line) > 1:
                    mode = CORE_FILE_BOUNDS_MODE_NAME_GIVEN
                else:
                    mode = CORE_FILE_BOUNDS_MODE_NO_NAME
                    
            elif mode == CORE_FILE_ROW_MODE:
                if line[0] == ROW_MODE_OBJ:
                    objective["name"] = line[1]
                else:
                    constraints[line[1]] = {"type": line[0], "name": line[1], "coefficients": [], "bounds": dict()}
            elif mode == CORE_FILE_COL_MODE:
                if len(line) > 1 and line[1] == "'MARKER'":
                    if line[2] == "'INTORG'":
                        integral_marker = True
                    elif line[2] == "'INTEND'":
                        integral_marker = False
                    continue
                variable_name = line[0]
                if variable_name not in variable:
                    variable[variable_name] = {"type": COL_TYPES[integral_marker], "name": variable_name, "bnd_lower": -math.inf, "bnd_upper": math.inf}
                j = 1
                while j < len(line) - 1:
                    if line[j] == objective["name"]:
                        objective["coefficients"].append(
                            dict(name = variable_name, value = float(line[j + 1]))
                        )
                    else:
                        constraints[line[j]]["coefficients"].append(
                            dict(name=variable_name, value = float(line[j + 1]))
                        )
                    j = j + 2
            elif mode == CORE_FILE_RHS_MODE_NAME_GIVEN:
                if line[0] != rhs_names[-1]:
                    raise Exception("Other RHS name was given even though name was set after RHS tag.")
                for kk in range((len(line) - 1) // 2):
                  idx = kk * 2
                  constraints[line[idx + 1]]["bounds"][line[0]] = float(line[idx + 2])
            elif mode == CORE_FILE_RHS_MODE_NO_NAME:
                rhs_name = line[0]
                if rhs_name not in rhs_names:
                    rhs_names.append(rhs_name)
                    for key, c in constraints.items():
                        c["bounds"][rhs_name] = 0
                for kk in range((len(line) - 1) // 2):
                  idx = kk * 2
                  constraints[line[idx + 1]]["bounds"][line[0]] = float(line[idx+2])
            elif mode in [CORE_FILE_BOUNDS_MODE_NAME_GIVEN, CORE_FILE_BOUNDS_MODE_NO_NAME]:
                if line[0] in BND_TYPES:
                    variable[line[2]][BND_TYPE[line[0]]] = BND_FUNC[line[0]](float(line[3]), variable[line[2]][BND_TYPE[line[0]]])
                elif line[0] == "BV":
                    variable[line[2]]["bnd_lower"] = 0
                    variable[line[2]]["bnd_upper"] = 1
                    variable[line[2]]["type"] = "Integer"
                elif line[0] == "FX":
                    variable[line[2]]["bnd_lower"] = BND_FUNC["LO"](float(line[3]), variable[line[2]]["bnd_lower"])
                    variable[line[2]]["bnd_upper"] = BND_FUNC["UP"](float(line[3]), variable[line[2]]["bnd_upper"])
                elif line[0] == "FR":
                    variable[line[2]]["bnd_lower"] = -math.inf
    
    if len(rhs_names) == 1:
        for key, c in constraints.items():
            c["bounds"] = c["bounds"][rhs_names[0]]
    
    return dict(objective = objective, variables = variable, constraints = constraints, rhs_names = rhs_names)