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

from game import ITEMS, RECIPES, RESOURCES


def define_game_constraints(solver: pywraplp.Solver):
    # Create the variables containers
    var_items_consumed = { item_name: dict() for item_name in ITEMS.keys()}
    var_items_produced = { item_name: dict() for item_name in ITEMS.keys()}
    var_items_sold = dict()

    var_recipes_used = {
        recipe_name: solver.NumVar(0, solver.infinity(), recipe_name)
        for recipe_name, _, _ in RECIPES
    }

    # recipes
    for i, recipe in enumerate(RECIPES):
        var_recipe_in = dict()
        var_recipe_out = dict()
        recipe_name, items_in, items_out = recipe

        # create variables for recipe
        for item_name in items_in:
            var_name = f'{item_name}_in_{i}'
            var_item = solver.NumVar(0, solver.infinity(), var_name)
            var_recipe_in[item_name] = var_item
            var_items_consumed[item_name][i] = var_item
        
        for item_name in items_out:
            var_name = f'{item_name}_out_{i}'
            var_item = solver.NumVar(0, solver.infinity(), var_name)
            var_recipe_out[item_name] = var_item
            var_items_produced[item_name][i] = var_item

        # define recipe
        var_recipe = var_recipes_used[recipe_name]
        for item_name, number in items_in.items():
            solver.Add(var_recipe == var_recipe_in[item_name] / number)
        for item_name, number in items_out.items():
            solver.Add(var_recipe == var_recipe_out[item_name] / number)

    # sold items
    var_items_sold = {
        item_name: solver.NumVar(0, solver.infinity(), f'{item_name}_sold')
        for item_name in ITEMS.keys()
    }
    return var_items_produced, var_items_consumed, var_items_sold


def set_flow_constraints(solver, var_items_produced, var_items_consumed, var_items_sold, resources_available):
    # flow contraints
    for item_name in ITEMS.keys():
        produced_in_all_recipes = sum(var_out for var_out in var_items_produced[item_name].values())
        consumed_in_all_recipes = sum(var_in for var_in in var_items_consumed[item_name].values())
        available = resources_available.get(item_name, 0)
        solver.Add(available + produced_in_all_recipes 
                   == var_items_sold[item_name] + consumed_in_all_recipes)


def report(solver, status, var_items_produced, var_items_consumed, var_items_sold):
    if status != pywraplp.Solver.OPTIMAL:
        print("The problem does not have an optimal solution.")
        # return

    print("Solution:")

    print("\nSold items:")
    for item_name in ITEMS.keys():
        var_item = var_items_sold[item_name]
        if var_item.solution_value() != 0:
            print(item_name, "=", round(var_item.solution_value(), 2))

    print("\nProduced items:")
    for item_name in ITEMS.keys():
        var_item = var_items_sold[item_name]
        items_produced = sum(var_out.solution_value() for var_out in var_items_produced[item_name].values())
        if items_produced != 0:
            print(item_name, "=", round(items_produced, 2))

    print("\nConsumed items:")
    for item_name in ITEMS.keys():
        var_item = var_items_sold[item_name]
        items_consumed = sum(var_out.solution_value() for var_out in var_items_consumed[item_name].values())
        if items_consumed != 0:
            print(item_name, "=", round(items_consumed, 2))

    print("\nRecipes used:")
    for i, recipe in enumerate(RECIPES):
        item_name, number = list(recipe[2].items())[0]
        amount = var_items_produced[item_name][i].solution_value()
        if amount != 0:
            print(recipe[0], "=", round(amount / number, 2))

    print("\nObjective value =", solver.Objective().Value())

    print("\nAdvanced usage:")
    print(f"Problem solved in {solver.wall_time():d} milliseconds")
    print(f"Problem solved in {solver.iterations():d} iterations")


def main(resources_available: dict):
    # Create the linear solver with the GLOP backend.
    solver = pywraplp.Solver.CreateSolver("GLOP")
    if not solver:
        raise RuntimeError("Could not create GLOB solver")

    # Define constraints
    var_items_produced, var_items_consumed, var_items_sold = define_game_constraints(solver)
    set_flow_constraints(solver, var_items_produced, var_items_consumed, var_items_sold, resources_available)

    # Objective: Maximize points
    sum_points = 0
    for item_name, item_data in ITEMS.items():
        sum_points += var_items_sold[item_name] * item_data["sinkPoints"]

    solver.Maximize(sum_points)

    print("Number of variables =", solver.NumVariables())
    print("Number of constraints =", solver.NumConstraints())
    print(f"Solving with {solver.SolverVersion()}")
    status = solver.Solve()

    report(solver, status, var_items_produced, var_items_consumed, var_items_sold)

    return solver


if __name__ == '__main__':
    resources_available = {
        item_name: 0 for item_name in RESOURCES
    }
    resources_available['Desc_OreIron_C'] = 120
    resources_available['Desc_OreCopper_C'] = 120

    main(resources_available)
