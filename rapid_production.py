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
import sink_point_optim


RETURN_CODES = {
 2: 'INFEASIBLE',
 5: 'MODEL_INVALID',
 6: 'NOT_SOLVED',
 0: 'OPTIMAL',
 3: 'UNBOUNDED',
}

DEFAULT_STEP_DURATION = 1.0 # minutes
DEFAULT_MAX_STEPS = 40 # steps


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
        self.A = np.zeros((self.M, self.K), dtype=float)
        # cost matrix A_i,r: costs of item i for recipe j
        self.B = np.zeros((self.M, self.K), dtype=float)

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
        ], dtype=float)

        # cost matrix A_i,r: costs of item i for recipe j
        # v_t = B * z_t
        self.B = np.array([
            [  0,    0,    0], # iron ore
            [  0,    0,    0], # iron ingot
            [  0,  12,   12], # iron plate
            [   5,   0,    0], # iron rod
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


    def validate(self):
        """Test whether the current configuration of recipes is valid, by checking
        - absence of handcrafted items in goal items and recipe ingredients
        - consistency of existing recipes (no manual item supply needed)
        """
        # TODO: Instead of excluding handcrafted items, add handcrafting recipes
        # with overall maximum rate per minute. This enables production
        # of everything!
        all_recipes = {recipe_name: 1 for recipe_name in game.RECIPES}
        all_resource_node_levels = {
            recipe_name: 1
            for recipe_name in game.NODES_AVAILABLE
        }
        producable_items = sink_point_optim.get_producable_items(all_recipes,
                                                                 dict(),
                                                                 all_resource_node_levels)
        existing_recipes = utils.unvectorize(self.E, game.RECIPES)
        for recipe_name, amount in existing_recipes.items():
            if amount == 0:
                continue
            required_items = set(game.RECIPES[recipe_name]['ingredients'])
            unprod_items = required_items - producable_items
            if unprod_items:
                raise RuntimeError(f'Recipe {recipe_name} relies on '
                                   f'unproducable items: {unprod_items}')
        goal_items = utils.unvectorize(self.G, game.ITEMS)
        for item_name, amount in goal_items.items():
            if amount == 0:
                continue
            if not item_name in producable_items:
                raise RuntimeError(f'Goal item {item_name} is not producable')
        
        item_balance = dict()
        for recipe_name, recipe_amount in existing_recipes.items():
            recipe = game.RECIPES[recipe_name]
            for item_name, item_amount in recipe['ingredients'].items():
                flow = recipe_amount * item_amount / (recipe['time'] / 60)
                item_balance[item_name] = item_balance.get(item_name, 0) - flow
            for item_name, item_amount in recipe['products'].items():
                flow = recipe_amount * item_amount / (recipe['time'] / 60)
                item_balance[item_name] = item_balance.get(item_name, 0) + flow
        existing_items = utils.unvectorize(self.S, game.ITEMS)
        for item_name, balance in item_balance.items():
            if balance < 0 and existing_items.get(item_name, 0) <= 0:
                # TODO: Why?
                print(f'WARNING: Negative balance of item not in stock: {item_name}.'
                      ' This might cause optimization failure. Put at least one'
                      ' item into the inventory.')

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
            solver.Add(x[i,t] == x[i,t-1] + (-v[i,t-1] + optim_conf.step_duration * p[i,t-1]))
            # solver.Add(x[i,t] == x[i,t-1] + y[t] * (-v[i,t] + p[i,t])) # TODO: reformulate

    # constraint: target capital
    for i in data_conf.I:
        solver.Add(x[i, optim_conf.N] >= start_conf.G[i])

    # constraint: investment
    for i, t in itertools.product(data_conf.I, optim_conf.T):
        solver.Add(x[i,t] - v[i,t] >= 0)

    return solver, [x, z, None, v, p]


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
    start_conf.validate()
    optim_conf = OptimizationConfiguration()
    solver, values, minimal_steps = solve_with_increasing_steps(
        data_conf, start_conf, optim_conf)
    print(f'Minimal number of steps: {minimal_steps}')
    print_solution_dict(minimal_steps, *values)


if __name__ == '__main__':
    pd.set_option('display.max_colwidth', None)
    main()
