# pysmps

This is a utility script for parsing MPS and SMPS file formats. It offers two main functions `load_lp` for loading mps files and `load_smps` for loading smps file directory.

### `load_lp`

The `load_lp(path)` method takes a `path` variable as input. It should be a .cor or .mps file.
It opens the file with read-permissions and parses the described linear program into the following format:

- `name`: The name given to the linear program (can't be blank)
- `objective_name`: The name of the objective function value
- `row_names`: list of row names
- `col_names`: list of column names
- `types`: list of constraint type indicators, i.e. either "E", "L" or "G" for equality, lower/equal or greater/equal constraint respectively.
- `c`: the objective function coefficients
- `A`: the constraint matrix
- `rhs_names`: list of names of right hand sides (there can be multiple right hand side components be defined, seldom more than one though)
- `rhs`: dictionary `(rhs_name) => b`, where `b` is the vector of constraint values for that given right hand side name.
- `bnd_names`: list of names of box-bounds (seldom more than one)
- `bnd`: dictionary `(bnd_name) => {"LO": v_l, "UP": v_u}` where `v_l` is the vector of lower bounds and `v_u` is the vector of upper bound values (defaults to `v_l = 0` and `v_u = +inf`).

Finally this corresponds to the linear program

```python
min 	c * x

w.r.t.	for each rhs_name with corresponding b:

			A[types == "E",:] * x  = b[types == "E"]
			A[types == "L",:] * x <= b[types == "L"]
			A[types == "G",:] * x >= b[types == "G"]

		for each bnd_name with corresponding v_l and v_u:

			v_l <= x <= v_u

```

### `load_smps`

This function makes use of the `load_mps` function for parsing the .cor file. The SMPS file format consists of three files, a .cor, .tim and .sto file. The .cor file is in MPS format. Further the function expects a parameter `path` to be such that `path + ".cor"` is the core file, `path + ".tim"` the time file and `path + ".sto"` is the stochastic file.
It *does not* support scenarios yet!
It returns a stochastic multi-stage problem in the following format

- `name`: name of the program (must be the same in all 3 files)

- `objective_name`: name of the objective function value

- `constraints`: list of tuples `(name, period, type)` for each constraint. It gives a name, a period in which the constraints appears and a type, i.e. "E", "L" or "G" as in MPS.

- `variables`: list of tuples `(name, period)` for each variable. It defines a name and a period in which the variable joins the program.

- `c`: vector of objective function coefficients (of all periods)

- `A`: matrix of constraint coefficients (of all periods)

- `rhs_names`: list of rhs names as in MPS

- `rhs`: dictionary as in MPS

- `bounds`: dictionary as in MPS

- `periods`: list of all periods appearing. `len(periods)` is the number stages.

- `blocks`: dictionary of `Block`,`LinearTransform` or `SubRoutine` objects. Dependent on what the .sto file defined. `Blocks` are independent random variables (every case of a `Block` must be combined with each case of another `Block` to get all possible appearences; the probabilities multiply), `LinearTransform` are linear transformations of continuous random variables. The user needs to write the sample script on his own. `SubRoutine` is a left-out in the file; it presupposes the user to know what to do with these values.

- `independent_variables`: dictionary `((i,j)) => {position, period, distrib}`, where `(i,j)` is the tuple of row/column indices. If one of them is `-1` this means that it's either an objective value or a rhs-value respectively. `position` is a dictionary adapting to where the entry is (objective value, rhs value or matrix value), `period` defines the period in which this variable is stochastic, `distrib` is either a definition of a continuous random variables

  ```python
  distrib: {type: "N(mu, sigma**2)"/"U(a, b)"/"B(p, q)"/"G(p, b)"/"LN(mu, sigma**2)", parameters}
  ```

  where parameters is a dictionary defining the required parameters. In the discrete case it is a list of tuples `(v,p)`, where `v` is the value of this position and `p` is the probability of it appearing.

For an example on how to use this format i recommand looking at the code for `load_2stage_problem`.

### `load_2stage_problem`

Loads a SMPS directory and tries to bring it into a 2-staged L-shaped stochastic linear program with fixed recourse. Output is a dictionary containing the values

- `c`: first stage objective function value
- `A`: first stage (equality) constraint coefficient matrix
- `b`: first stage constraint values
- `q`: list of second stage objective function coefficients (each case one entry)
- `h`: list of second stage constraint values (each case one entry)
- `T`: list of second stage constraint values for deterministic variables (each case one entry)
- `W`: recourse matrix (since it's fixed recourse this is not a list)
- `p`: list of probabilities for each case

The constellations in which `(q,h,T,W)` appear are the realizations given by `(q[k], h[k], T[k], W)`.