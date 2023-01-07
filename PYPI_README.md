# pysmps

This is a utility script for parsing MPS and SMPS file formats. It offers two main functions `load_mps` for loading mps files and `load_smps` for loading smps file directory.

**DISCLAIMER** This parser assumes a certain order of instructions in the MPS file and so a latter instruction colliding with an earlier one counts. In case you find a unnatural behavior in this parser let me know via github.

### `read_mps`

The `read_mps(path)` method takes a `path` variable as input. The contents of the file under `path` are assumed to be in MPS format.
It opens the file and parses the described linear program into an instance of the class `MPS`. Note that `MPS` has always attached a group of the `RHS`, `BOUNDS` and `RANGES` sections. If there are no multiple groups in the file this is irrelevant to the user; in case there are multiple groups in the mps file given you can see the list of groups via the following methods:

* `MPS.bnd_names()` for a list of the boundary group names
* `MPS.rhs_names()` for a list of the RHS group names
* `MPS.range_names()` for a list of range names.

In order to obtain the values for different choices of group names you can attach a group via

* `MPS.attach_bnd(group)` to attach the boundary group with name `group`
* `MPS.attach_rhs(group)` to attach the rhs group with name `group`
* `MPS.attach_range(group)` to attach the range group with name `group`

After attachment you can modify the linear program for this particular group choice via the methods for modification or obtain the linear program parameters for the choice via the getter functions:

* `MPS.get_variables()` returns a `dict` mapping a variable name to a `dict` containing the `type` and bounds (`lower`, `upper`) w.r.t. the attached BOUNDS group
* `MPS.get_rhs()` returns a `dict` mapping a **constraint** row name to the RHS value of the row w.r.t. the attached RHS group
* `MPS.get_offsets()` returns a `dict` mapping an **objective** row name to the RHS value (i.e. offset) of the row w.r.t. the attached RHS group
* `MPS.get_ranges()` returns a `dict` mapping a contraint row name to a `dict` containing the `upper` and `lower` deviation of the interval in which the row has to be from its respective RHS value w.r.t. the attached RANGES group

In order to see the entire linear program (without having to attach groups) it is useful to convert the class instance into a `dict` via the pre-implemented functionality

```python
M = read_mps("some/path")
dict(M)
```

This function returns a `dict` with all the information of `M`. This `dict` is a mapping of the following kind:

```python
name -> str: Name of program
objective_names -> list of str: Names of the objective rows
bnd_names -> list of str: Names of the different boundary configurations given
rhs_names -> list of str: Names of the different RHS configurations given
range_names -> list of str: Names of range configurations
constraint_names -> list of str: Names of constraint rows
variable_names -> list of str: Names of variables
objectives -> dict: Maps each of objective_names to a dict mapping each of variable_names with non-zero
    			coefficient for this objective to its respective coefficient
variables -> dict: Maps each of bnd_names to a dict mapping each of variable_names to a dict describing 				the variable for this particular boundary setting. The dict has keys "type", "lower" and 
    			"upper".
constraints -> dict: Maps each of constraint_names to a dict containing the type of the constraint
    			("E", "L", "G") and a dict mapping each of variable_names having non-zero coefficient for
        		this constraint to its coefficient
rhs -> dict: Maps each of rhs_names to a dict mapping each of of constraint_names to its respective rhs
    			value
offsets -> dict: Maps each of rhs_names to a dict mapping each of objective_names to their offset in this
    			particular rhs configuration
ranges -> dict: Maps each of range_names to a dict containing the ranges for this particular range
    			configuration. This dict maps one of constraint_names to a dict containing "lower" and
        		"upper" if ranges are given for it
```



**NOTE** Currently this code does not support `SOS` tags. However the reader will skip over this section with no errors. The default behavior of this parser is as follows:

* The default bounds for continuous aswell as integer values are `{lower: 0, upper: math.inf}`. You can change this by calling the `read_mps` function with the additional arguments `c_lower, c_upper, i_lower, i_upper` and the respective values for continuous and integer default bounds. Note that the `i_lower` and `i_upper` bounds are only applied to variables declared in an `INTORG`, `INTEND` block. They are not applied to continuously declared variables which become integral by `LI` or `UI` BOUNDS tags.
* If conflicting BOUNDS, RHS or RANGE values are given the one given last counts.
* The BOUNDS tags have following default bound values:
  * The default bounds if none are given are `i_lower, c_lower: 0` and `i_upper, c_upper: math.inf`
  * `MI` has a default upper bound of `0`; can be set by the `MI_upper` argument
  * `SC` has a default lower bound of `1` if no argument is given; can be set by the `SC_lower` argument
* The general behaviour of BOUNDS tags is that the relevant portions of previous BOUNDS is overwritten; `MI` for example overwrites the previous `lower` bound to `-math.inf` but also the previous `upper` bound to the given upper bound or `MI_default`. Thus the file should set explicit upper bounds either in the `MI` line or after it but never before (similar behavior for `SC`).
* As mentioned above the `LI` and `UI` commands do not apply the integer default bounds `i_lower`, `i_upper`, `LI` and `UI` only change the variable to `Integer` and set the respective bound; the other bound stays as is.
* Variable types can be `Integer`, `Continuous` or `Semi-Continuous`

`load_smps`

This function makes use of the `load_mps` function for parsing the .cor file. The SMPS file format consists of three files, a .cor, .tim and .sto file. The .cor file is in MPS format. Further the function expects a parameter `path` to be such that `path + ".cor"` is the core file, `path + ".tim"` the time file and `path + ".sto"` is the stochastic file.

**NOTE** It *does not* support scenarios or nodes!

Similar to the `MPS` object the `SMPS` object can be converted into a `dict` containing all information of the object. This `dict` has the same fields as its underlying `MPS` class from the .cor file. The remaining fields are:

```python
row_periods -> dict: Maps every period name to a list of str containing the rows belonging to this period
col_periods -> dict: Maps every period name to a list of str containing the cols belonging to this period
distributions -> dict: Maps every period for which distributions are given to a dict mapping every pair
    			(i.e. tuple) of row and col names to a dict describing the distribution. This dict either 
        		declares the distribution directly if one is given or refers to a block distribution
blocks -> dict: Maps every period to a dict of blocks describing the distribution for each block
```

The same default behavior as in the `read_mps` function hold.