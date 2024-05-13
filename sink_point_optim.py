"""
Sink points are the games currency. Optimizing profit IRL is equal to maximize
sink point generation. 

Value concept of items:
- Standard recipes: value(items_out) = 2 * value(items_in)
- Packaging recipes: value(items_out) = value(items_in)
- Solutions: value(items_out) = value(items_in)
- Exceptions: Alumina Solution, others?
- Alternative recipes: Not clear

"""

from ortools.linear_solver import pywraplp

import game
import parse_items_from_csv


def define_game_constraints(solver: pywraplp.Solver, recipes: dict, resources_available: dict):
    var_recipes_used = {
        recipe_name: solver.NumVar(0, solver.infinity(), recipe_name)
        for recipe_name in game.RECIPES
    }

    # define helper terms
    consumed_in_all_recipes = dict()
    produced_in_all_recipes = dict()
    for item_name in game.ITEMS:
        consumed_in_all_recipes[item_name] = sum(
            game.RECIPES[recipe_name][0][item_name] * var_recipes_used[recipe_name]
            for recipe_name in recipes
            if recipe_name in game.consumed_by[item_name]
        )
        produced_in_all_recipes[item_name] = sum(
            game.RECIPES[recipe_name][1][item_name] * var_recipes_used[recipe_name]
            for recipe_name in recipes
            if recipe_name in game.produced_by[item_name]
        )
    
    # disable other recipes
    for recipe_name in game.RECIPES:
        if not recipe_name in recipes:
            solver.Add(var_recipes_used[recipe_name] == 0)
    
    # flow contraints
    for item_name in game.ITEMS:
        available = resources_available.get(item_name, 0)
        solver.Add(
            available + produced_in_all_recipes[item_name] >= consumed_in_all_recipes[item_name]
        )

    return var_recipes_used, consumed_in_all_recipes, produced_in_all_recipes


def define_objective(solver: pywraplp.Solver, var_recipes_used: dict,
                     consumed_in_all_recipes: dict, produced_in_all_recipes: dict):
    sum_points = 0
    for item_name, item_data in game.ITEMS.items():
        amount_consumed = consumed_in_all_recipes[item_name]
        amount_produced = produced_in_all_recipes[item_name]
        amount_available = resources_available.get(item_name, 0)
        amount_sold = amount_available + amount_produced - amount_consumed
        sum_points += amount_sold * item_data["sinkPoints"]

    solver.Maximize(sum_points)

    return var_recipes_used


def report(solver, status, var_recipes_used, 
           consumed_in_all_recipes, produced_in_all_recipes):
    if status != pywraplp.Solver.OPTIMAL:
        print("The problem does not have an optimal solution.")
        # return

    print("Solution:")

    print("\nRecipes used:")
    for recipe_name in game.RECIPES:
        recipes_used = var_recipes_used[recipe_name].solution_value()
        if round(recipes_used, 3) != 0:
            print(recipe_name, "=", round(recipes_used, 3))

    print("\nSold items:")
    for item_name in game.ITEMS:
        amount_consumed = consumed_in_all_recipes[item_name]
        amount_produced = produced_in_all_recipes[item_name]
        amount_available = resources_available.get(item_name, 0)
        amount_sold = amount_available + amount_produced - amount_consumed
        
        # is the case for all except from empty lists in consumed/produced in all recipes
        # because sum([]) = 0
        if not type(amount_sold) == int:
            amount_sold = amount_sold.solution_value()
        if round(amount_sold, 3) != 0:
            print(item_name, "=", round(amount_sold, 3))

    print("\nObjective value =", solver.Objective().Value())

    print("\nAdvanced usage:")
    print(f"Problem solved in {solver.wall_time():d} milliseconds")


def check_parameters(resources_available: dict) -> bool:
    result = True
    if 'Desc_Water_C' in resources_available:
        print('Water is available unlimited and therefore not in any recipe')
        result = False
    for item_name in resources_available:
        if not item_name in game.ITEMS:
            print('Unknown item:', item_name)
            result = False
    return result


def main(resources_available: dict, recipes: dict=game.RECIPES):
    if not check_parameters(resources_available):
        exit(1)

    # Create the linear solver with the GLOP backend.
    solver = pywraplp.Solver.CreateSolver("GLOP")
    if not solver:
        raise RuntimeError("Could not create GLOB solver")

    var_recipes_used, consumed_in_all_recipes, produced_in_all_recipes = define_game_constraints(
        solver, recipes, resources_available)
    define_objective(solver, var_recipes_used, consumed_in_all_recipes, produced_in_all_recipes)

    print("Number of variables =", solver.NumVariables())
    print("Number of constraints =", solver.NumConstraints())
    print(f"Solving with {solver.SolverVersion()}")
    status = solver.Solve()

    report(solver, status, var_recipes_used, consumed_in_all_recipes, produced_in_all_recipes)

    return solver


if __name__ == '__main__':
    resources_available = dict()

    # custom
    # resources_available['Desc_OreIron_C'] = 120
    # resources_available['Desc_OreCopper_C'] = 120
    
    # # current overhead
    # resources_available = parse_items_from_csv.parse_items('../Autonation4.0.csv')

    # full ressource occupancy
    resources_available['Desc_Stone_C'] = 480*27 + 240*47 + 120*12
    resources_available['Desc_OreIron_C'] = 480*46 + 240*41 + 120*33
    resources_available['Desc_OreCopper_C'] = 480*12 + 240*28 + 120*9
    resources_available['Desc_OreGold_C'] = 480*8 + 240*8
    resources_available['Desc_Coal_C'] = 480*14 + 240*29 + 120*6
    resources_available['Desc_LiquidOil_C'] = 240*8 + 120*12 + 60*10
    resources_available['Desc_Sulfur_C'] = 480*3 + 240*7 + 120*1
    resources_available['Desc_OreBauxite_C'] = 480*6 + 240*6 + 120*5
    resources_available['Desc_RawQuartz_C'] = 480*5 + 240*11
    resources_available['Desc_OreUranium_C'] = 240*3 + 120*1

    # recipes=dict()
    recipes=game.RECIPES
    main(resources_available, recipes)
