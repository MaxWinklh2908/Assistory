"""
While sink_point_optim.py calculates a facotry as a build blueprint, this
script calculates the fastest way create a set of items. The basic network flow is shared in the modeling
"""
import numpy as np
from ortools.linear_solver import pywraplp
import pandas as pd


RETURN_CODES = {
 2: 'INFEASIBLE',
 5: 'MODEL_INVALID',
 6: 'NOT_SOLVED',
 0: 'OPTIMAL',
 3: 'UNBOUNDED',
}


class StartConfiguration:

    def __init__(self, S: int, G: int, E: int):
        """Create a start configuration for the problem

        Args:
            S (int): start amount of items
            G (int): goal amount of items
            E (int): existing recipes/production
        """
        self.S = S
        self.G = G
        self.E = E

class OptimizationConfiguration:

    def __init__(self, n: int):
        if n < 1:
            raise ValueError('Number of steps must be at least 1')
        self.N = n
        self.T = set(range(n + 1))


# production matrix A_i,r: production rate of item i by recipe j
# p_t = A * z_t
A = 0.25

# cost matrix A_i,r: costs of item i for recipe j
# v_t = B * z_t
B = 1

N_MAX = 25 # steps
BIG_M = 1000

def define_problem_min_investment(start_conf: StartConfiguration,
                                  optim_conf: OptimizationConfiguration):
    solver = pywraplp.Solver.CreateSolver("CBC")
    if not solver:
        raise RuntimeError("Could not create CBC solver")

    # variable: item i in stock at time t
    x = np.zeros(len(optim_conf.T), dtype=object)
    for t in optim_conf.T:
        x[t] = solver.NumVar(0, solver.infinity(), f'x_{t}')
    
    # varialbe: add recipe r at t TODO: to enable dismantling allow reducing revenue
    z = np.zeros(len(optim_conf.T), dtype=object)
    for t in optim_conf.T:
        z[t] = solver.NumVar(0, solver.infinity(), f'z_{t}')
    
    # variable: production active indicator
    y = np.zeros(len(optim_conf.T), dtype=object)
    for t in optim_conf.T:
        y[t] = solver.BoolVar(f'y_{t}')

    # helper term: investment
    v = B * z
    
    # helper term: investment TODO: consider ingredients and products(=revenue) of the recipes
    p = np.zeros(len(optim_conf.T), dtype=object)
    p[0] = A * (start_conf.E + z[0])
    for t in optim_conf.T - {0}:
        p[t] = p[t-1] + A * (z[t])

    # objective: minimize steps to reach goal
    solver.Minimize(sum(y))
    # solver.Minimize(sum(v))

    # constraint: produce until stop. No restart
    for t in optim_conf.T - {0}:
        solver.Add(y[t] <= y[t-1])

    # constraint: time step
    solver.Add(x[0] == start_conf.S - v[0])
    w_helper = np.zeros(len(optim_conf.T), dtype=object)
    for t in optim_conf.T - {0}:
        w = -v[t] + p[t]
        w_helper[t] = solver.NumVar(-solver.infinity(), solver.infinity(), f'w_{t}')
        solver.Add(w_helper[t] <= BIG_M * y[t]) # w == 0 if not y[t]
        solver.Add(-BIG_M * y[t] <= w_helper[t]) # w == 0 if not y[t]
        solver.Add(w_helper[t] <= w + BIG_M * (1 - y[t]) ) # w == 0 if not y[t]
        solver.Add(w - BIG_M * (1 - y[t]) <= w_helper[t])
        solver.Add(x[t] == x[t-1] + w_helper[t]) # 
        # solver.Add(x[t] == x[t-1] + (-v[t] + p[t])) # TODO: reformulate
   

    # constraint: target capital
    solver.Add(x[optim_conf.N] >= start_conf.G)

    # constraint: investment
    for t in optim_conf.T:
        solver.Add(x[t] - v[t] >= 0)

    return solver, [x, z, y, v, p]


def define_problem_min_steps(start_conf: StartConfiguration,
                             optim_conf: OptimizationConfiguration):
    solver = pywraplp.Solver.CreateSolver("CBC")
    if not solver:
        raise RuntimeError("Could not create CBC solver")

    # variable: item i in stock at time t
    x = np.zeros(len(optim_conf.T), dtype=object)
    for t in optim_conf.T:
        x[t] = solver.NumVar(0, solver.infinity(), f'x_{t}')
    
    # varialbe: add recipe r at t TODO: to enable dismantling allow reducing revenue
    z = np.zeros(len(optim_conf.T), dtype=object)
    for t in optim_conf.T:
        z[t] = solver.NumVar(0, solver.infinity(), f'z_{t}')
    
    # variable: production active indicator
    y = np.zeros(len(optim_conf.T), dtype=object)
    for t in optim_conf.T:
        y[t] = solver.BoolVar(f'y_{t}')

    # helper term: investment
    v = B * z
    
    # helper term: investment TODO: consider ingredients and products(=revenue) of the recipes
    p = np.zeros(len(optim_conf.T), dtype=object)
    p[0] = A * (start_conf.E + z[0])
    for t in optim_conf.T - {0}:
        p[t] = p[t-1] + A * (z[t])

    # objective: minimize steps to reach goal
    solver.Minimize(sum(y))

    # constraint: produce until stop. No restart
    for t in optim_conf.T - {0}:
        solver.Add(y[t] <= y[t-1])

    # constraint: time step
    solver.Add(x[0] == start_conf.S - v[0])
    w_helper = np.zeros(len(optim_conf.T), dtype=object)
    for t in optim_conf.T - {0}:
        w = -v[t] + p[t]
        w_helper[t] = solver.NumVar(-solver.infinity(), solver.infinity(), f'w_{t}')
        solver.Add(w_helper[t] <= BIG_M * y[t]) # w == 0 if not y[t]
        solver.Add(-BIG_M * y[t] <= w_helper[t]) # w == 0 if not y[t]
        solver.Add(w_helper[t] <= w + BIG_M * (1 - y[t]) ) # w == 0 if not y[t]
        solver.Add(w - BIG_M * (1 - y[t]) <= w_helper[t])
        solver.Add(x[t] == x[t-1] + w_helper[t]) # 
   

    # constraint: target capital
    solver.Add(x[optim_conf.N] >= start_conf.G)

    # constraint: investment
    for t in optim_conf.T:
        solver.Add(x[t] - v[t] >= 0)

    return solver, [x, z, y, v, p]


def solve(start_conf: StartConfiguration):
    print('Test', N_MAX)
    optim_conf = OptimizationConfiguration(N_MAX)
    solver, values = define_problem_min_steps(start_conf, optim_conf)
    status = solver.Solve()
    print(f"Problem processed in {solver.wall_time():d} milliseconds")
    if status != pywraplp.Solver.OPTIMAL:
        raise RuntimeError('Could not reach target in time')
    return solver, values
    

def extract_required_steps(y):
    for i, y_t in enumerate(y):
        if y_t.solution_value() == 0:
            return i
    raise RuntimeError('Did not find final step')


def print_solution(x, z, y, v, p):
    N = len(x)
    if len(v) != N:
        raise ValueError(f'Expect {N} investment values. Got {len(v)}')
    if len(p) != N:
        raise ValueError(f'Expect {N} revenue values. Got {len(p)}')
    df = pd.DataFrame({
        'State': [round(val.solution_value(), 2) for val in x],
        'Indicator': [val.solution_value() for val in y],
        'Investment': [round(val.solution_value(), 2) for val in v],
        'Revenue': [round(val.solution_value(), 2) for val in p],
    })
    print(df)


def main():
    start_conf = StartConfiguration(S = 10,
                                    G = 200,
                                    E = 0)
    solver, values = solve(start_conf)
    minimal_steps = extract_required_steps(values[2])
    # values = [vals[:minimal_steps] for vals in values]
    print("Number of variables =", solver.NumVariables())
    print("Number of constraints =", solver.NumConstraints())
    print(f'Minimal number of steps: {minimal_steps}')
    print_solution(*values)


if __name__ == '__main__':
    main()
