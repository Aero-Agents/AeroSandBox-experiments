# Opti Class Documentation

This document provides a comprehensive explanation of the `Opti` class and its methods, based on the docstrings in the source code.

## Overview

The `Opti` class is the base class for mathematical optimization, extending `casadi.Opti`. It provides a user-friendly interface for defining variables, constraints, parameters, and solving optimization problems, with additional features for engineering design workflows such as variable freezing and solution caching.

### Example Usage
```python
opti = asb.Opti() # Initializes an optimization environment
x = opti.variable(init_guess=5) # Initializes a new variable
f = x ** 2 # Nonlinear function of variable
opti.subject_to(x > 3) # Adds a constraint
opti.minimize(f) # Sets the objective function
sol = opti.solve() # Solves the problem
print(sol(x)) # Prints the optimal value of x
```

---

## Methods

### `__init__`
Initializes the optimization environment and sets up variable freezing, caching, and tracking mechanisms. See source for advanced options.

---

### `variable(...)`
Initializes a new decision variable (or vector of variables).
- **init_guess**: Initial guess for the variable (float or ndarray).
- **n_vars**: Optional, manually set dimensionality.
- **scale**: Optional, recommended for nonconvex problems.
- **freeze**: If True, variable is fixed at initial guess or cache value.
- **log_transform**: If True, variable is log-transformed (for positive quantities).
- **category**: Optional, for grouping variables (useful for freezing by category).
- **lower_bound/upper_bound**: Optional, bounds for the variable.

**Returns:** Symbolic CasADi variable (MX type).

#### Usage Notes
- Vector variables can be indexed and summed.
- Freezing is useful for engineering design stages and off-design analysis.
- Log-transform helps maintain convexity for positive quantities.

---

### `subject_to(constraint, ...)`
Adds equality or inequality constraints to the optimization problem.
- **constraint**: Can be symbolic, boolean, or a list of constraints.
- **_stacklevel**: Advanced, for debugging declaration locations.

**Returns:** Dual variable(s) associated with the constraint(s).

#### Usage Notes
- Supports vectorized and list constraints.
- Skips always-true constraints; raises error for always-false constraints.

---

### `minimize(f)`
Sets the objective function to be minimized.
- **f**: Symbolic CasADi expression.

---

### `maximize(f)`
Sets the objective function to be maximized (by minimizing `-f`).
- **f**: Symbolic CasADi expression.

---

### `parameter(value, n_params=None)`
Initializes a new parameter (or vector of parameters).
- **value**: Initial value (float or ndarray).
- **n_params**: Optional, manually set dimensionality.

**Returns:** Symbolic CasADi parameter (MX type).

---

### `solve(...)`
Solves the optimization problem using CasADi with IPOPT backend.
- **parameter_mapping**: Optional, dictionary of parameters to set before solving.
- **max_iter**: Maximum iterations.
- **max_runtime**: Maximum runtime.
- **callback**: Function called at each iteration.
- **verbose**: Controls solver output.
- **jit**: Experimental, enables JIT compilation.
- **options**: Dictionary of IPOPT options.
- **behavior_on_failure**: "raise" (default) or "return_last" (returns last solution).

**Returns:** `OptiSol` object containing the solution.

#### Usage Notes
- Use `sol(variable)` to extract optimal values.
- Supports solution caching and variable freezing from cache.

---

### `solve_sweep(parameter_mapping, ...)`
Runs a sweep over multiple parameter values, solving the optimization problem for each set.
- **parameter_mapping**: Dictionary of parameters to sweep over (values as arrays).
- **update_initial_guesses_between_solves**: If True, updates initial guesses between runs.
- **verbose**: Controls output.
- **solve_kwargs**: Additional arguments for `solve()`.
- **return_callable**: If True, returns a callable for the sweep.
- **garbage_collect_between_runs**: If True, runs garbage collection between solves.

**Returns:** Array of solutions or a callable.

---

## Additional Features
- **Variable Freezing**: Freeze variables or categories for design iteration and off-design analysis.
- **Solution Caching**: Save and load solutions for reproducibility and workflow efficiency.
- **Debugging Tools**: Tracks declaration locations for variables and constraints.

---

For further details, see the source code and method docstrings.
