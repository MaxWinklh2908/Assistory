"""
While sink_point_optim.py calculates a facotry as a build blueprint, this
script calculates the fastest way create a set of items. The basic network flow is shared in the modeling
"""
import itertools

import numpy as np
from ortools.linear_solver import pywraplp
import pandas as pd

import game
import utils


RETURN_CODES = {
 2: 'INFEASIBLE',
 5: 'MODEL_INVALID',
 6: 'NOT_SOLVED',
 0: 'OPTIMAL',
 3: 'UNBOUNDED',
}

STEP_DURATION = 1.0 # minutes


def define_facility_recipes():
    facility_recipes = {
        recipe['products'][0]['item']: recipe
        for recipe in game.data['recipes'].values()
        if len(recipe['products'])  == 1
            and recipe['products'][0]['item'] in game.PRODUCTION_FACILITIES
    }
    facility_recipes['Desc_GeneratorCoal_C'] = {'ingredients': []}
    facility_recipes['Desc_GeneratorFuel_C'] = {'ingredients': []}
    facility_recipes['Desc_GeneratorNuclear_C'] = {'ingredients': []}
    facility_recipes['Desc_MinerMk1_C'] = {'ingredients': []}
    facility_recipes['Desc_MinerMk2_C'] = {'ingredients': []}
    facility_recipes['Desc_MinerMk3_C'] = {'ingredients': []}
    facility_recipes['Desc_WaterPump_C'] = {'ingredients': []}
    facility_recipes['Desc_OilPump_C'] = {'ingredients': []}
    facility_recipes['Desc_FrackingExtractor_C'] = {'ingredients': []}
    return facility_recipes
FACILITY_NAME2RECIPE = define_facility_recipes()



class DataConfiguration:
    pass


class GameDataConfiguration(DataConfiguration):

    def __init__(self):
        self.K = len(game.RECIPES) # number of recipes
        self.R = list(range(self.K))
        self.M = len(game.ITEMS) # number of items
        self.I = list(range(self.M))

        # production matrix A_i,r: production rate of item i by recipe r
        self.A = np.zeros((self.M, self.K))
        # cost matrix A_i,r: costs of item i for recipe j
        self.B = np.zeros((self.M, self.K))

        for r, recipe_name in enumerate(sorted(game.RECIPES)):
            recipe = game.RECIPES[recipe_name]

            ingredients = recipe['ingredients']
            products = recipe['products']
            self.A[:, r] = ((- np.array(utils.vectorize(ingredients, game.ITEMS))
                            + np.array(utils.vectorize(products, game.ITEMS))) 
                            / (recipe['time'] / 60))

            facility_name = recipe['producedIn']
            facility_recipe = FACILITY_NAME2RECIPE[facility_name]
            build_costs = utils.transform_to_dict(facility_recipe['ingredients'])
            self.B[:, r] = np.array(utils.vectorize(build_costs, game.ITEMS))


class CustomDataConfiguration(DataConfiguration):

    def __init__(self) -> None:
        self.K = 3 # number of recipes
        self.R = list(range(self.K))
        self.M = 4 # number of items
        self.I = list(range(self.M))

        # production matrix A_i,r: production rate of item i by recipe r
        # p_t = A * z_t
        self.A = np.array([
            [-30,   0,   0], # iron ore
            [ 30, -30, -15], # iron ingot
            [  0,  20,   0], # iron plate
            [  0,   0,  15], # iron rod
        ])

        # cost matrix A_i,r: costs of item i for recipe j
        # v_t = B * z_t
        self.B = np.array([
            [  0,    0,    0], # iron ore
            [  0,    0,    0], # iron ingot
            [  0,  12,   12], # iron plate
            [   5,   0,    0], # iron rod
        ])


class StartConfiguration:

    def __init__(self, data_conf: DataConfiguration,
                 S: np.ndarray, G: np.ndarray, E: np.ndarray):
        """Create a start configuration for the problem

        Args:
            data_conf (DataConfiguration): configuration of the game data
            S (np.ndarray): start amount of items
            G (np.ndarray): goal amount of items
            E (np.ndarray): existing recipes/production
        """
        if S.shape != (data_conf.M,):
            raise ValueError(f'Expect start amount of shape {(data_conf.M,)}. Got {S.shape}')
        if G.shape != (data_conf.M,):
            raise ValueError(f'Expect goal amount of shape {(data_conf.M,)}. Got {G.shape}')
        if E.shape != (data_conf.K,):
            raise ValueError(f'Expect existing recipes of shape {(data_conf.K,)}. Got {E.shape}')
        # TODO: Check feasibility of E
        self.S = S
        self.G = G
        self.E = E

class OptimizationConfiguration:

    def __init__(self, n: int):
        if n < 0:
            raise ValueError('Number of steps must be at least 1')
        self.N = n
        self.T = set(range(n + 1))


N_MAX = 40 # steps

def define_problem(data_conf: DataConfiguration,
                   start_conf: StartConfiguration,
                   optim_conf: OptimizationConfiguration):
    solver = pywraplp.Solver.CreateSolver("CBC")
    if not solver:
        raise RuntimeError("Could not create CBC solver")

    # variable: item i in stock at time t
    x = np.zeros((data_conf.M, len(optim_conf.T)), dtype=object)
    for i, t in itertools.product(data_conf.I, optim_conf.T):
        x[i,t] = solver.NumVar(0, solver.infinity(), f'x_{i}_{t}')
    
    # variable: add recipe r at t TODO: to enable dismantling allow reducing revenue
    z = np.zeros((data_conf.K, len(optim_conf.T)), dtype=object)
    for r, t in itertools.product(data_conf.R, optim_conf.T):
        z[r,t] = solver.IntVar(0, solver.infinity(), f'z_{r}_{t}')
    
    # variable: production active indicator
    # y = np.zeros(len(optim_conf.T), dtype=object)
    # for t in optim_conf.T:
    #     y[t] = solver.BoolVar(f'y_{t}')

    # helper term: investment
    v = data_conf.B @ z
    
    # helper term: investment TODO: consider ingredients and products(=revenue) of the recipes
    p = np.zeros((data_conf.M, len(optim_conf.T)), dtype=object)
    p[:,0] = data_conf.A @ (start_conf.E + z[:,0])
    for t in optim_conf.T - {0}:
        p[:,t] = p[:,t-1] + data_conf.A @ (z[:,t])

    # objective: minimize steps to reach goal
    # solver.Minimize(y.sum())
    # objective: minimize invested recipes
    solver.Minimize(z.sum())

    # constraint: produce until stop. No restart
    # for t in optim_conf.T - {0}:
    #     solver.Add(y[t] >= y[t-1])

    # constraint: time step
    for i in data_conf.I:
        solver.Add(x[i,0] == start_conf.S[i])
        for t in optim_conf.T - {0}:
            solver.Add(x[i,t] == x[i,t-1] + (-v[i,t-1] + STEP_DURATION * p[i,t-1]))
            # solver.Add(x[i,t] == x[i,t-1] + y[t] * (-v[i,t] + p[i,t])) # TODO: reformulate

    # constraint: target capital
    for i in data_conf.I:
        solver.Add(x[i, optim_conf.N] >= start_conf.G[i])

    # constraint: investment
    for i, t in itertools.product(data_conf.I, optim_conf.T):
        solver.Add(x[i,t] - v[i,t] >= 0)

    return solver, [x, z, None, v, p]


def solve(data_conf: DataConfiguration, start_conf: StartConfiguration, n_max: int=N_MAX):
    for n in range(0, n_max):
        print('Iteration: ', n)
        optim_conf = OptimizationConfiguration(n)
        solver, values = define_problem(data_conf, start_conf, optim_conf)
        print("Number of variables =", solver.NumVariables())
        print("Number of constraints =", solver.NumConstraints())
        status = solver.Solve()
        print(f"Problem processed in {solver.wall_time():d} milliseconds")
        if status == pywraplp.Solver.OPTIMAL:
            minimal_steps = n
            return solver, values, minimal_steps
        if status != pywraplp.Solver.INFEASIBLE:
            raise RuntimeError('Unexpected status: ' + RETURN_CODES[status])
    raise RuntimeError('Could not reach target in time. Status=' + RETURN_CODES[status])


def print_solution(N, x, z, y, v, p):
    # N is number of steps + 1
    if x.shape[1] != N + 1:
        raise ValueError(f'Expect {N+1} columns in state values. Got {x.shape}')
    if z.shape[1] != N + 1:
        raise ValueError(f'Expect {N+1} columns in recipe values. Got {z.shape}')
    if v.shape[1] != N + 1:
        raise ValueError(f'Expect {N+1} columns in investment values. Got {v.shape}')
    if p.shape[1] != N + 1:
        raise ValueError(f'Expect {N+1} columns in revenue values. Got {p.shape}')
    data = dict()
    data.update({ f'State_{i}': x[i] for i in range(x.shape[0])})
    data.update({ f'Invest_Recipes_{i}': z[i] for i in range(z.shape[0])})
    data.update({ f'Invest_Costs_{i}': v[i] for i in range(v.shape[0])})
    data.update({ f'Revenue_{i}': p[i] for i in range(p.shape[0])})
    data = {
        name: [round(val.solution_value(), 2) for val in vals]
        for name, vals in data.items()
    }
    print(pd.DataFrame(data))


def print_solution_dict(N, x, z, y, v, p):
    # N is number of steps + 1
    if x.shape[1] != N + 1:
        raise ValueError(f'Expect {N+1} columns in state values. Got {x.shape}')
    if z.shape[1] != N + 1:
        raise ValueError(f'Expect {N+1} columns in recipe values. Got {z.shape}')
    if v.shape[1] != N + 1:
        raise ValueError(f'Expect {N+1} columns in investment values. Got {v.shape}')
    if p.shape[1] != N + 1:
        raise ValueError(f'Expect {N+1} columns in revenue values. Got {p.shape}')
    data = {
        'State': [
            str(utils.unvectorize([round(val.solution_value(), 2) for val in x[:,t]], game.ITEMS))
            for t in range(N+1)],
        'Recipes': [
            str(utils.unvectorize([round(val.solution_value(), 2) for val in z[:,t]], game.RECIPES))
            for t in range(N+1)],
        'Investment Cost': [
            str(utils.unvectorize([round(val.solution_value(), 2) for val in v[:,t]], game.ITEMS))
            for t in range(N+1)],
        'Revenue': [
            str(utils.unvectorize([round(val.solution_value(), 2) for val in p[:,t]], game.ITEMS))
            for t in range(N+1)],
    }
    print(pd.DataFrame(data))
    print('\nState')
    for i, val in enumerate(data['State']):
        print(i, val)
    print('\nRecipe Plan')
    for i, val in enumerate(data['Recipes']):
        print(i, val)


def main():
    data_conf = GameDataConfiguration()
    start_conf = StartConfiguration(data_conf,
                                    S = np.array(utils.vectorize({
                                        'Desc_OreIron_C': 1000,
                                        'Desc_IronRod_C': 10,
                                        'Desc_Wire_C': 16,
                                        }, game.ITEMS)),
                                    G = np.array(utils.vectorize({
                                        'Desc_IronIngot_C': 100,
                                        }, game.ITEMS)),
                                    E = np.array(utils.vectorize({
                                        # 'Recipe_IngotIron_C': 1,
                                        }, game.RECIPES)))
    solver, values, minimal_steps = solve(data_conf, start_conf)
    print(f'Minimal number of steps: {minimal_steps}')
    print_solution_dict(minimal_steps, *values)


if __name__ == '__main__':
    pd.set_option('display.max_colwidth', None)
    main()
