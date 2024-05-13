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


def define_game_constraints(solver: pywraplp.Solver, recipes: dict):
    var_recipes_used = {
        recipe_name: solver.NumVar(0, solver.infinity(), recipe_name)
        for recipe_name in recipes
    }
    var_items_sold = {
        item_name: solver.NumVar(0, solver.infinity(), f'{item_name}_sold')
        for item_name in game.ITEMS.keys()
    }
    return var_items_sold, var_recipes_used


def set_flow_constraints(solver, var_items_sold, var_recipes_used, resources_available):
    # map items to recipes
    consumed_by = { item_name: [] for item_name in game.ITEMS}
    produced_by = { item_name: [] for item_name in game.ITEMS}
    for recipe_name, data in recipes.items():
        items_in, items_out = data
        for item_name in items_in:
            consumed_by[item_name].append(recipe_name)
        for item_name in items_out:
            produced_by[item_name].append(recipe_name)
    
    # flow contraints
    for item_name in game.ITEMS:
        consumed_in_all_recipes = sum(
            game.RECIPES[recipe_name][0][item_name] * var_recipes_used[recipe_name]
            for recipe_name in consumed_by[item_name]
        )
        produced_in_all_recipes = sum(
            game.RECIPES[recipe_name][1][item_name] * var_recipes_used[recipe_name]
            for recipe_name in produced_by[item_name]
        )
        available = resources_available.get(item_name, 0)
        solver.Add(
            available + produced_in_all_recipes 
            == var_items_sold[item_name] + consumed_in_all_recipes
        )


def report(solver, status, var_items_sold, var_recipes_used):
    if status != pywraplp.Solver.OPTIMAL:
        print("The problem does not have an optimal solution.")
        # return

    print("Solution:")

    print("\nSold items:")
    for item_name in game.ITEMS:
        var_item = var_items_sold[item_name]
        if var_item.solution_value() != 0:
            print(item_name, "=", round(var_item.solution_value(), 2))

    # print("\nProduced items:")
    # for item_name in game.ITEMS.keys():
    #     var_item = var_items_sold[item_name]
    #     items_produced = sum(var_out.solution_value() for var_out in var_items_produced[item_name].values())
    #     if items_produced != 0:
    #         print(item_name, "=", round(items_produced, 2))

    # print("\nConsumed items:")
    # for item_name in game.ITEMS.keys():
    #     var_item = var_items_sold[item_name]
    #     items_consumed = sum(var_out.solution_value() for var_out in var_items_consumed[item_name].values())
    #     if items_consumed != 0:
    #         print(item_name, "=", round(items_consumed, 2))

    print("\nRecipes used:")
    # for i, recipe in enumerate(recipes):
    #     item_name, number = list(recipe[2].items())[0]
    #     amount = var_items_produced[item_name][i].solution_value()
    #     if amount != 0:
    #         print(recipe[0], "=", round(amount / number, 2))
    for recipe_name in game.RECIPES:
        var_item = var_recipes_used[recipe_name]
        if var_item.solution_value() != 0:
            print(recipe_name, "=", round(var_item.solution_value(), 2))

    print("\nObjective value =", solver.Objective().Value())

    print("\nAdvanced usage:")
    print(f"Problem solved in {solver.wall_time():d} milliseconds")
    print(f"Problem solved in {solver.iterations():d} iterations")


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

    # Define constraints
    var_items_sold, var_recipes_used = define_game_constraints(solver, recipes)
    set_flow_constraints(solver, var_items_sold, var_recipes_used, resources_available)

    # Objective: Maximize points
    sum_points = 0
    for item_name, item_data in game.ITEMS.items():
        sum_points += var_items_sold[item_name] * item_data["sinkPoints"]

    solver.Maximize(sum_points)

    print("Number of variables =", solver.NumVariables())
    print("Number of constraints =", solver.NumConstraints())
    print(f"Solving with {solver.SolverVersion()}")
    status = solver.Solve()

    report(solver, status, var_items_sold, var_recipes_used)

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
