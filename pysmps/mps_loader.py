import re
import math
import copy
import warnings

CORE_FILE_ROW_MODE = "ROWS"
CORE_FILE_COL_MODE = "COLUMNS"
CORE_FILE_RHS_MODE = "RHS"
CORE_FILE_BOUNDS_MODE = "BOUNDS"
CORE_FILE_RANGES_MODE = "RANGES"
CORE_FILE_SOS_MODE = "SOS"

# SMPS special tags
CORE_FILE_ARCS_MODE = "ARCS"

CORE_FILE_BOUNDS_MODE_NAME_GIVEN = "BOUNDS_NAME"
CORE_FILE_BOUNDS_MODE_NO_NAME = "BOUNDS_NO_NAME"
CORE_FILE_RHS_MODE_NAME_GIVEN = "RHS_NAME"
CORE_FILE_RHS_MODE_NO_NAME = "RHS_NO_NAME"
CORE_FILE_RANGES_MODE_NAME_GIVEN = "RANGES_NAME"
CORE_FILE_RANGES_MODE_NO_NAME = "RANGES_NO_NAME"
CORE_FILE_SOS_MODE_FIRST_LINE = "SOS_FIRST_LINE"


ROW_MODE_OBJ = "N"

MODE = {CORE_FILE_ROW_MODE: 0, CORE_FILE_COL_MODE: 1, CORE_FILE_RHS_MODE: 3,
         CORE_FILE_BOUNDS_MODE: 4, CORE_FILE_BOUNDS_MODE_NAME_GIVEN: 5,
         CORE_FILE_BOUNDS_MODE_NO_NAME: 6, CORE_FILE_RHS_MODE_NAME_GIVEN: 7,
         CORE_FILE_RHS_MODE_NO_NAME: 8, CORE_FILE_RANGES_MODE_NAME_GIVEN: 9,
         CORE_FILE_RANGES_MODE_NO_NAME: 10, CORE_FILE_SOS_MODE: 11,
         CORE_FILE_SOS_MODE_FIRST_LINE: 12}

COL_TYPES = {1: "Integer", 0: "Continuous"}
BND_TYPES = ["LO", "UP"]
BND_TYPE = {"LO": "lower", "UP": "upper"}
BND_FUNC = {"LO": lambda a, b : a if b == 0 else max(a,b), "UP": min}





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


warnings.simplefilter("always", ImportWarning)
warnings.warn("""pysmps: Backwards compatibility to pre-2.0 versions has been abolished. Install older versions for code adjusted to the old interface, e.g. via \r\n
              pip install 'pysmps<2.0'\r\n""", category=ImportWarning, stacklevel=2)
warnings.simplefilter("default", ImportWarning)

# public
class MPS:
    
    def __init__(self, defaults):
        self.defaults = {"Integer": {"type": "Integer", "lower": defaults["i_lower"], "upper": defaults["i_upper"]}, "Continuous": {"type": "Continuous", "lower": defaults["c_lower"], "upper": defaults["c_upper"]}}
        self.name = "No Name"
        self.objectives = {}
        self.variables = {}
        self._variables = {}
        self.constraints = {}
        self.rhs = {}
        self.offsets = {}
        self.ranges = {}
        #self.sos = {}
        
        self.curr_rhs = -1
        self.curr_bnd = -1
        self.curr_range = -1
        
        
    def finalize(self):
        if len(self.bnd_names()) > 0: self.curr_bnd = self.bnd_names()[0]
        if len(self.rhs_names()) > 0: self.curr_rhs = self.rhs_names()[0]
        if len(self.range_names()) > 0: self.curr_range = self.range_names()[0]
        #if len(self.sos_names()) > 0: self.curr_sos = self.sos_names()[0]
        
    def _set_name(self, name):
        self.name = name
    
    def add_objective(self, name):
        self.objectives[name] = {"coefficients": {}}
    
        
    # returns the list of names of possible boundary configurations
    def objective_names(self):
        return list(self.objectives.keys())
    def bnd_names(self):
        return list(self.variables.keys())
    def rhs_names(self):
        return list(self.rhs.keys())
    def variable_names(self):
        return list(self._variables.keys())
    def constraint_names(self):
        return list(self.constraints.keys())
    def range_names(self):
        return list(self.ranges.keys())
    #def sos_names(self):
    #    return list(self.sos.keys())
    
    
    
    def get_variables(self):
        return self.variables[self.curr_bnd]
    def get_rhs(self):
        return self.rhs[self.curr_rhs]
    def get_constraints(self):
        return self.constraints
    def get_objectives(self):
        return self.objectives
    def get_offsets(self):
        return self.offsets[self.curr_rhs]
    def get_ranges(self):
        return self.ranges[self.curr_range]
    
    
    def _add_constraint(self, name, constr):
        self.constraints[name] = constr
        
    def _set_coefficient(self, row, variable, value):
        if row in self.objectives:
            self.objectives[row]["coefficients"][variable] = value
        else:
            self.constraints[row]["coefficients"][variable] = value
    
    
    #def add_sos(self, name, degree):
    #    if name in self.sos:
    #        raise ValueError('The SOS ' + name + ' does already exist!')
    #    self.sos[name] = {"degree": degree, "priority": priority, "variables": {}}
    
    #def attach_sos(self, name):
    #    self.curr_sos = name
        
    #def add_variable_to_sos(self, var, value):
    #    self.sos[self.curr_sos]["variables"][var] = value
    
    # sets the boundary group active for modification
    def attach_bnd(self, name):
        if name not in self.variables:
            raise ValueError('The boundary group ' + name + ' does not exist!')
        self.curr_bnd = name
    
    def _add_variable(self, name, _type):
        self._variables[name] = {"type": _type, "lower": self.defaults[_type]["lower"], "upper": self.defaults[_type]["upper"]}
    def _update_variable(self, variable, mod):
        self.variables[self.curr_bnd][variable].update(mod)
        
    def _add_bnd_group(self, name):
        if name in self.variables:
            raise ValueError('The boundary group ' + name + ' already exists!')
        self.variables[name] = copy.deepcopy(self._variables)
        if len(self.variables) == 2:
            warnings.warn("There are multiple boundary groups for the linear program " + self.name + ". Switch boundary group using the MPS.set_bounds_group function.", stacklevel=2)
    
    def attach_range(self, name):
        if name not in self.ranges:
            raise ValueError('The range group ' + name + ' does not exist!')
        self.curr_range = name
    
    def _add_range_group(self, name):
        if name in self.ranges:
            raise ValueError('The range group ' + name + ' already exists!')
        self.ranges[name] = {}
        if len(self.ranges) == 2:
            warnings.warn("There are multiple range groups for the linear program " + self.name + ". Switch range group using the MPS.attach_range function.", stacklevel=2)
    
    def add_range(self, constr, value):
        if self.constraints[constr]["type"] == "G":
            self.ranges[self.curr_range][constr] = {"lower": 0, "upper": abs(value)}
        elif self.constraints[constr]["type"] == "L":
            self.ranges[self.curr_range][constr] = {"lower": -abs(value), "upper": 0}
        elif self.constraint[constr]["type"] == "E":
            if constr not in self.ranges[self.curr_range]:
                self.ranges[self.curr_range] = {"lower": 0, "upper": 0}
            if value < 0:
                self.ranges[self.curr_range][constr]["lower"] = value
            else:
                self.ranges[self.curr_range][constr]["upper"] = value
        else:
            raise ValueError('Range given for free row!')
    
    def _add_rhs_group(self, name):
        if name in self.rhs:
            raise ValueError('The RHS group ' + name + ' already exists!')
        self.rhs[name] = dict((constr,0) for constr in self.constraints)
        self.offsets[name] = dict((obj,0) for obj in self.objectives)
        if len(self.rhs) == 2:
            warnings.warn("There are multiple rhs groups for the linear program " + self.name + ". Switch rhs group using the MPS.attach_rhs function.", stacklevel=2)
    
    def attach_rhs(self, name):
        if name not in self.rhs:
            raise ValueError('The RHS group ' + name + ' does not exist!')
        self.curr_rhs = name
    
    def set_rhs(self, constr, value):
        if constr in self.constraints:
            self.rhs[self.curr_rhs][constr] = value
        elif constr in self.objectives:
            self.offsets[self.curr_rhs][constr] = value
        else:
            raise ValueError('The row ' + constr + ' does not exist!')
        
    def get_curr_rhs(self):
        return self.curr_rhs
    def get_curr_bnd(self):
        return self.curr_bnd
    def get_curr_range(self):
        return self.curr_range
    
    # used to produce dict
    def __iter__(self):
        yield ("name", self.name)
        yield ("objective_names", self.objective_names())
        yield ("bnd_names", self.bnd_names())
        yield ("rhs_names", self.rhs_names())
        yield ("range_names", self.range_names())
        yield ("constraint_names", self.constraint_names())
        yield ("variable_names", list(self._variables.keys()))
        #yield ("sos_names", self.sos_names())
        yield ("objectives", self.objectives)
        yield ("variables", self.variables)
        yield ("constraints", self.constraints)
        yield ("rhs", self.rhs)
        yield ("offsets", self.offsets)
        yield ("ranges", self.ranges)
        #yield ("sos", self.sos)


def read_mps(path, **kwargs):
    mode = -1
    
    default_bounds = {"c_lower": 0.0, "c_upper": math.inf, "i_lower": 0.0, "i_upper": math.inf}
    given_bounds = dict((k, kwargs[k]) for k in ['c_lower', 'c_upper', 'i_lower', 'i_upper'] if k in kwargs)
    default_bounds.update(given_bounds)
   
    mps = MPS(default_bounds)
    
    defaults = {"MI_upper": 0.0, "SC_lower": 1.0}
    given_defaults = dict((k, kwargs[k]) for k in ['MI_upper', 'SC_lower'] if k in kwargs)
    defaults.update(given_defaults)
    
    integral_marker = False
    
    with open(path, "r") as reader:
        
        for line in reader:
            if line.startswith("*"):
                continue

            line = re.split(" |\t", line)
            line = [x.strip() for x in line]
            line = list(filter(None, line))
            
            if len(line) == 0:
                continue
            if line[0] == "ENDATA":
                mps.finalize()
                break
            if line[0] == "*":
                continue
            if line[0] == "NAME":
                mps._set_name(line[1])
                #name = line[1]
                
            # ROW INSTRUCTION
            elif line[0] in [CORE_FILE_ROW_MODE, CORE_FILE_COL_MODE]:
                mode = MODE[line[0]]
                
            # RHS INSTRUCTION
            elif line[0] == CORE_FILE_RHS_MODE and len(line) <= 2:
                if len(line) > 1:
                    if line[1] not in mps.rhs:
                        mps._add_rhs_group(line[1])
                    mps.attach_rhs(line[1])
                    
                    mode = MODE[CORE_FILE_RHS_MODE_NAME_GIVEN]
                else:
                    mode = MODE[CORE_FILE_RHS_MODE_NO_NAME]
                    
            # BOUNDS INSTRUCTION  
            elif line[0] == CORE_FILE_BOUNDS_MODE and len(line) <= 2:
                if len(line) > 1:
                    if line[1] not in mps.variables:
                        mps._add_bnd_group(line[1])
                    mps.attach_bnd(line[1])
                    
                    mode = MODE[CORE_FILE_BOUNDS_MODE_NAME_GIVEN]
                else:
                    mode = MODE[CORE_FILE_BOUNDS_MODE_NO_NAME]
                    
            # RANGES INSTRUCTION
            elif line[0] == CORE_FILE_RANGES_MODE and len(line) <= 2:
                if len(line) > 1:
                    if line[1] not in mps.ranges:
                        mps._add_range_group(line[1])
                    mps.attach_range(line[1])
                    
                    mode = MODE[CORE_FILE_RANGES_MODE_NAME_GIVEN]
                else:
                    mode = MODE[CORE_FILE_RANGES_MODE_NO_NAME]
                    
            # SOS INSTRUCTION
            elif line[0] == CORE_FILE_SOS_MODE:
                mode = MODE[CORE_FILE_SOS_MODE_FIRST_LINE]
                
            
            elif line[0] == CORE_FILE_ARCS_MODE:
                raise ValueError("NETWORK is currently not implemented!")
                
                
            elif mode == MODE[CORE_FILE_ROW_MODE]:
                if line[0] == ROW_MODE_OBJ:
                    mps.add_objective(line[1])
                else:
                    mps._add_constraint(line[1], {"type": line[0], "coefficients": {}})
                    
            # COL MODE
            elif mode == MODE[CORE_FILE_COL_MODE]:
                if len(line) > 1 and line[1] == "'MARKER'":
                    if line[2] == "'INTORG'":
                        integral_marker = True
                    elif line[2] == "'INTEND'":
                        integral_marker = False
                    continue
                if line[0] not in mps._variables:
                    mps._add_variable(line[0], COL_TYPES[integral_marker])
                j = 1
                while j < len(line) - 1:
                    mps._set_coefficient(line[j], line[0], float(line[j+1]))
                    j = j + 2
                    
            # RHS MODE
            elif mode in [MODE[CORE_FILE_RHS_MODE_NAME_GIVEN], MODE[CORE_FILE_RHS_MODE_NO_NAME]]:
                if mode == MODE[CORE_FILE_RHS_MODE_NAME_GIVEN]:
                    if line[0] != mps.get_curr_rhs():
                        raise Exception("Other RHS name was given even though name was set after RHS tag.")
                elif line[0] not in mps.rhs:
                    mps._add_rhs_group(line[0])
                    mps.attach_rhs(line[0])
                for kk in range((len(line) - 1) // 2):
                    idx = kk * 2
                    mps.set_rhs(line[idx + 1], float(line[idx + 2]))
                    
            # SOS MODE
            elif mode == MODE[CORE_FILE_SOS_MODE_FIRST_LINE]:
                warnings.warn("SOS functionality is currently not supported. If your program relies on Special Ordered Set functionality the output might not be true to the file input!", stacklevel=2)
            #    degree = int(line[0][1:])
            #    mps.add_sos(line[2], degree, int(line[3]))
            #    mps.attach_sos(line[2])
                mode = MODE[CORE_FILE_SOS_MODE]
                
                
            elif mode == MODE[CORE_FILE_SOS_MODE]:
                pass
                #mps.add_variable_to_sos(line[1], float(line[2]))
                
            # BOUNDS MODE
            elif mode in [MODE[CORE_FILE_BOUNDS_MODE_NAME_GIVEN], MODE[CORE_FILE_BOUNDS_MODE_NO_NAME]]:
                if mode == MODE[CORE_FILE_BOUNDS_MODE_NAME_GIVEN]:
                    if line[1] != mps.get_curr_bnd():
                        raise Exception("Other BND name was given even though name was set after BND tag.")
                elif line[1] not in mps.variables:
                    mps._add_bnd_group(line[1])
                    mps.attach_bnd(line[1])
                
                if line[0] == "UP":
                    mps._update_variable(line[2], {"upper": float(line[3])})
                elif line[0] == "UI":
                    mps._update_variable(line[2], {"type": "Integer", "upper": float(line[3])})
                elif line[0] == "LO":
                    mps._update_variable(line[2], {"lower": float(line[3])})
                elif line[0] == "LI":
                    mps._update_variable(line[2], {"type": "Integer", "lower": float(line[3])})
                elif line[0] == "FX":
                    mps._update_variable(line[2], {"lower": float(line[3]), "upper": float(line[3])})
                elif line[0] == "FR":
                    mps._update_variable(line[2], {"lower": -math.inf, "upper": math.inf})
                elif line[0] == "MI":
                    mps._update_variable(line[2], {"lower": -math.inf, "upper": defaults["MI_upper"]})
                elif line[0] == "PL":
                    mps._update_variable(line[2], {"lower": 0.0, "upper": math.inf})
                elif line[0] == "BV":
                    mps._update_variable(line[2], {"type": "Integer", "lower": 0.0, "upper": 1.0})
                elif line[0] == "SC":
                    val = defaults["SC_lower"]
                    if len(line) > 3:
                        val = float(line[3])
                    mps._update_variable(line[2], {"type": "Semi-Continuous", "lower": val})
                
            # RANGES MODE
            elif mode in [MODE[CORE_FILE_RANGES_MODE_NAME_GIVEN], MODE[CORE_FILE_RANGES_MODE_NO_NAME]]:
                if mode == MODE[CORE_FILE_RANGES_MODE_NAME_GIVEN]:
                    if line[0] != mps.get_curr_range():
                        raise Exception("Other RANGES group tag was given even though group was set after RANGES tag.")
                elif line[0] not in mps.ranges:
                    mps._add_range_group(line[0])
                    mps.attach_range(line[0])
                
                mps.add_range(line[1], float(line[2]))
    
    
    return mps
    
    
    
    
    
    
