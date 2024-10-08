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

DEFAULT_STEP_DURATION = 1.0 # minutes
DEFAULT_MAX_STEPS = 20 # steps
DEBUG = False

class DataConfiguration:
    # TODO: Use methods to access variables to enforce interface
    pass


class GameDataConfiguration(DataConfiguration):

    def __init__(self):
        self.RECIPES = sorted(game.RECIPES)
        self.K = len(self.RECIPES) # number of recipes
        self.R = list(range(self.K))

        self.RECIPES_HANDCRAFT = sorted(game.RECIPES_HANDCRAFT)
        self.L = len(self.RECIPES_HANDCRAFT) # number of handcraft recipes
        self.R_handcraft = list(range(self.L))

        self.ITEMS = sorted(game.ITEMS)
        self.M = len(self.ITEMS) # number of items
        self.I = list(range(self.M))

        # production matrix A_i,r: production rate of item i by recipe r
        self.A = np.zeros((self.M, self.K), dtype=float)
        # cost matrix A_i,r: costs of item i for recipe j
        self.B = np.zeros((self.M, self.K), dtype=float)
        # handcrafting production matrix A^H_i,r: production rate of item i by recipe r
        self.A_handcraft = np.zeros((self.M, self.L), dtype=float)

        for r, recipe_name in enumerate(self.RECIPES):
            recipe = game.RECIPES[recipe_name]

            ingredients = recipe['ingredients']
            products = recipe['products']
            self.A[:, r] = (
                (- np.array(utils.vectorize(ingredients, self.ITEMS))
                 + np.array(utils.vectorize(products, self.ITEMS))) 
                / (recipe['time'] / 60))

            facility_name = recipe['producedIn']
            build_costs = game.PRODUCTION_FACILITIES[facility_name]['costs']
            self.B[:, r] = np.array(utils.vectorize(build_costs, self.ITEMS))

        for r, recipe_name in enumerate(self.RECIPES_HANDCRAFT):
            recipe = game.RECIPES_HANDCRAFT[recipe_name]

            ingredients = recipe['ingredients']
            products = recipe['products']
            self.A_handcraft[:, r] = (
                (- np.array(utils.vectorize(ingredients, self.ITEMS))
                 + np.array(utils.vectorize(products, self.ITEMS)))
                / (recipe['time'] / 60))


class CustomDataConfiguration(DataConfiguration):

    def __init__(self) -> None:
        self.RECIPES = [
            'Recipe_IronIngot_C',
            'Recipe_IronPlate_C',
            'Recipe_IronRod_C',
        ]
        self.K = len(self.RECIPES) # number of recipes
        self.R = list(range(self.K))

        self.RECIPES_HANDCRAFT = [
            'Recipe_IronOre_C',
            'Recipe_IronIngot_C',
            'Recipe_IronRod_C',
        ]
        self.L = len(self.RECIPES_HANDCRAFT) # number of handcrafting recipes
        self.R_handcraft = list(range(self.L))
        
        self.ITEMS = [
            'Desc_OreIron_C',
            'Desc_IronIngot_C',
            'Desc_IronPlate_C',
            'Desc_IronRod_C',
        ]
        self.M = len(self.ITEMS) # number of items
        self.I = list(range(self.M))

        # production matrix A_i,r: production rate of item i by recipe r
        # p_t = A * z_t
        self.A = np.array([
            [-30,   0,   0], # iron ore
            [ 30, -30, -15], # iron ingot
            [  0,  20,   0], # iron plate
            [  0,   0,  15], # iron rod
        ], dtype=float)

        # cost matrix A_i,r: costs of item i for recipe j
        # v_t = B * z_t
        self.B = np.array([
            [  0,    0,    0], # iron ore
            [  0,    0,    0], # iron ingot
            [  0,  12,   12], # iron plate
            [   5,   0,    0], # iron rod
        ], dtype=float)

        # production matrix A_i,r: production rate of item i by recipe r
        # h_t = A^H * z_t
        self.A_handcraft = np.array([
            [  30, -30,   0], # iron ore
            [   0,  30, -1], # iron ingot
            [   0,   0,   1], # iron plate
            [   0,   0,  0], # iron rod
        ], dtype=float)


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
        self.S = S
        self.G = G
        self.E = E
        self.data_conf = data_conf


    def validate(self):
        """Test whether the current configuration of recipes is valid, by
        checking manual item supply needed for existing recipes configuration.
        """
        existing_recipes = utils.unvectorize(self.E, self.data_conf.RECIPES)
        existing_items = utils.unvectorize(self.S, self.data_conf.ITEMS)
        if DEBUG:
            print('\nExisting recipes:')
            for recipe_name, amount in existing_recipes.items():
                print(recipe_name, amount)
            print('\nExisting items:')
            for item_name, amount in existing_items.items():
                print(item_name, amount)
        item_balance = dict()
        for recipe_name, recipe_amount in existing_recipes.items():
            recipe = game.RECIPES[recipe_name]
            for item_name, item_amount in recipe['ingredients'].items():
                flow = recipe_amount * item_amount / (recipe['time'] / 60)
                item_balance[item_name] = item_balance.get(item_name, 0) - flow
            for item_name, item_amount in recipe['products'].items():
                flow = recipe_amount * item_amount / (recipe['time'] / 60)
                item_balance[item_name] = item_balance.get(item_name, 0) + flow
        if DEBUG:
            print('\nItem balance:')
        for item_name, balance in item_balance.items():
            if DEBUG:
                print(item_name, ':', balance)
            if balance < 0:
                print(f'WARNING: Negative balance of item {item_name}: {balance}.'
                      ' This might cause optimization failure if it can not'
                      ' build up production fast enough. Put a sufficient amount'
                      ' of the item into the inventory.')

class OptimizationConfiguration:

    def __init__(self, n: int=DEFAULT_MAX_STEPS,
                 step_duration: float=DEFAULT_STEP_DURATION):
        """
        Configuration for the optimization

        Args:
            n (int, optional): Maximal number of iterations. Must be al least 0.
                Defaults to DEFAULT_MAX_STEPS.
            step_duration (float, optional): Amount of minutes an iteration takes.
                Defaults to DEFAULT_STEP_DURATION.
        """
        if n < 0:
            raise ValueError('Number of steps must be at least 1')
        self.N = n
        self.T = set(range(n + 1))
        self.step_duration = step_duration


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

    
    # variable: add handcraft recipe r at t
    z_H = np.zeros((data_conf.L, len(optim_conf.T)), dtype=object)
    for r, t in itertools.product(data_conf.R_handcraft, optim_conf.T):
        z_H[r,t] = solver.IntVar(0, 1, f'z^H_{r}_{t}')
    
    # variable: production active indicator
    # y = np.zeros(len(optim_conf.T), dtype=object)
    # for t in optim_conf.T:
    #     y[t] = solver.BoolVar(f'y_{t}')

    # helper term investment
    v = data_conf.B @ z
    
    # helper term production: ingredients and products(=revenue) of the recipes
    p = np.zeros((data_conf.M, len(optim_conf.T)), dtype=object)
    p[:,0] = data_conf.A @ (start_conf.E + z[:,0])
    for t in optim_conf.T - {0}:
        p[:,t] = p[:,t-1] + data_conf.A @ (z[:,t])

    # helper term handcrafted production
    h = np.zeros((data_conf.M, len(optim_conf.T)), dtype=object)
    for t in optim_conf.T:
        h[:,t] = data_conf.A_handcraft @ (z_H[:,t])

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
            solver.Add(x[i,t] == x[i,t-1] + (-v[i,t-1] + optim_conf.step_duration * (p[i,t-1] + h[i,t-1])))

    # constraint: target capital
    for i in data_conf.I:
        solver.Add(x[i, optim_conf.N] >= start_conf.G[i])

    # constraint: investment
    for i, t in itertools.product(data_conf.I, optim_conf.T):
        solver.Add(x[i,t] - v[i,t] >= 0)

    # constraint: one handcrafted recipe at a time
    for t in optim_conf.T:
        solver.Add(sum(z_H[:,t]) <= 1)

    return solver, [x, z, z_H, None, v, p]


def solve_with_increasing_steps(data_conf: DataConfiguration,
                                start_conf: StartConfiguration,
                                optim_conf: OptimizationConfiguration):
    for n in range(0, optim_conf.N+1):
        print('Iteration: ', n)
        _optim_conf = OptimizationConfiguration(n, optim_conf.step_duration)
        solver, values = define_problem(data_conf, start_conf, _optim_conf)
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


def solve_with_binary_search(data_conf: DataConfiguration,
                             start_conf: StartConfiguration,
                             optim_conf: OptimizationConfiguration):
    
    left = 0
    right = optim_conf.N
    minimal_steps = None

    # test feasibility first
    print('Test most relaxed conditions first...')
    _optim_conf = OptimizationConfiguration(right, optim_conf.step_duration)
    best_solver, best_values = define_problem(
        data_conf, start_conf, _optim_conf)
    print("Number of variables =", best_solver.NumVariables())
    print("Number of constraints =", best_solver.NumConstraints())
    status = best_solver.Solve()
    print(f"Problem processed in {best_solver.wall_time():d} milliseconds")
    if status == pywraplp.Solver.INFEASIBLE:
        # If no feasible solution was found
        raise RuntimeError('Could not reach target in time. Status=' + RETURN_CODES[status])
    elif status != pywraplp.Solver.OPTIMAL:
        raise RuntimeError('Unexpected status: ' + RETURN_CODES[status])

    while left <= right:

        mid = (left + right) // 2
        print('Search value: ', mid)
        _optim_conf = OptimizationConfiguration(mid, optim_conf.step_duration)
        solver, values = define_problem(data_conf, start_conf, _optim_conf)
        status = solver.Solve()
        print(f"Problem processed in {solver.wall_time():d} milliseconds")

        if status == pywraplp.Solver.OPTIMAL:
            # If an optimal solution is found, store the current mid as the best solution
            minimal_steps = mid
            # Try to find a smaller solution, search the lower half
            right = mid - 1
            best_solver = solver
            best_values = values
        elif status == pywraplp.Solver.INFEASIBLE:
            # If the problem is infeasible, search the upper half
            left = mid + 1
        else:
            raise RuntimeError('Unexpected status: ' + RETURN_CODES[status])

    # Return the solver, values, and the minimal steps found
    return best_solver, best_values, minimal_steps


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


def print_solution_dict(N, x, z, z_H, y, v, p, data_conf: DataConfiguration):
    # N is number of steps + 1
    if x.shape[1] != N + 1:
        raise ValueError(f'Expect {N+1} columns in state values. Got {x.shape}')
    if z.shape[1] != N + 1:
        raise ValueError(f'Expect {N+1} columns in recipe values. Got {z.shape}')
    if z_H.shape[1] != N + 1:
        raise ValueError(f'Expect {N+1} columns in handcraft recipe values. Got {z_H.shape}')
    if v.shape[1] != N + 1:
        raise ValueError(f'Expect {N+1} columns in investment values. Got {v.shape}')
    if p.shape[1] != N + 1:
        raise ValueError(f'Expect {N+1} columns in revenue values. Got {p.shape}')
    data = {
        'State': [
            str(utils.unvectorize([round(val.solution_value(), 2) for val in x[:,t]],
                                  data_conf.ITEMS))
            for t in range(N+1)],
        'Recipes': [
            str(utils.unvectorize([round(val.solution_value(), 2) for val in z[:,t]],
                                  data_conf.RECIPES))
            for t in range(N+1)],
        'Handcraft recipes': [
            str(utils.unvectorize([round(val.solution_value(), 2) for val in z_H[:,t]],
                                  data_conf.RECIPES_HANDCRAFT))
            for t in range(N+1)],
        'Investment Cost': [
            str(utils.unvectorize([round(val.solution_value(), 2) for val in v[:,t]],
                                  data_conf.ITEMS))
            for t in range(N+1)],
        'Revenue': [
            str(utils.unvectorize([round(val.solution_value(), 2) for val in p[:,t]],
                                  data_conf.ITEMS))
            for t in range(N+1)],
    }
    if DEBUG:
        print(pd.DataFrame(data))
    print('\nState')
    for i, val in enumerate(data['State']):
        print(i, val)
    print('\nRecipe Plan (step, recipes, handcrafted)')
    for i, vals in enumerate(zip(data['Recipes'], data['Handcraft recipes'])):
        val, val_H = vals
        print(i, val, val_H)


def main():
    data_conf = GameDataConfiguration()
    start_conf = StartConfiguration(data_conf,
                                    S = np.array(utils.vectorize({
                                        'Desc_OreIron_C': 1000,
                                        'Desc_IronRod_C': 10,
                                        'Desc_Wire_C': 16,
                                        }, data_conf.ITEMS)),
                                    G = np.array(utils.vectorize({
                                        'Desc_IronIngot_C': 100,
                                        }, data_conf.ITEMS)),
                                    E = np.array(utils.vectorize({
                                        # 'Recipe_IngotIron_C': 1,
                                        }, data_conf.RECIPES)))
    start_conf.validate()
    optim_conf = OptimizationConfiguration()
    solver, values, minimal_steps = solve_with_binary_search(
        data_conf, start_conf, optim_conf)
    print(f'Minimal number of steps: {minimal_steps}')
    print_solution_dict(minimal_steps, *values, data_conf)


if __name__ == '__main__':
    pd.set_option('display.max_colwidth', None)
    main()
