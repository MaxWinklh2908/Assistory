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


# Create the linear solver with the GLOP backend.
solver = pywraplp.Solver.CreateSolver("GLOP")
if not solver:
    exit(1)


def solve(item_names: list, recipes: list, resources_available: dict, sink_points):
    # Create the variables containers
    var_items_produced = { item_name: [] for item_name in item_names}
    var_items_consumed = { item_name: [] for item_name in item_names}
    var_items_sold = dict()

    # ressources available
    for item_name, amount in resources_available.items():
        var_name = f'{item_name}_out'
        var_item = solver.NumVar(0, solver.infinity(), var_name)
        var_items_produced[item_name].append(var_item)
        solver.Add(var_item == amount)

    # sold items
    for item_name in item_names:
        var_name = f'{item_name}_sold'
        var_item = solver.NumVar(0, solver.infinity(), var_name)
        var_items_sold[item_name] = var_item

    # recipes
    for i, recipe in enumerate(recipes):
        var_recipe_in = dict()
        var_recipe_out = dict()
        items_in, items_out = recipe

        # create variables for recipe
        for item_name in items_in:
            var_name = f'{item_name}_in_{i}'
            var_item = solver.NumVar(0, solver.infinity(), var_name)
            var_recipe_in[item_name] = var_item
            var_items_consumed[item_name].append(var_item)
        
        for item_name in items_out:
            var_name = f'{item_name}_out_{i}'
            var_item = solver.NumVar(0, solver.infinity(), var_name)
            var_recipe_out[item_name] = var_item
            var_items_produced[item_name].append(var_item)

        # define recipe
        sum_in = sum(var_recipe_in[item_name] / number
                     for item_name, number in items_in.items())
        sum_out = sum(var_recipe_out[item_name] / number
                      for item_name, number in items_out.items())
        solver.Add(sum_out == sum_in)

    # flow contraints
    for item_name in item_names:
        sum_out = sum(var_out for var_out in var_items_produced[item_name])
        sum_in = sum(var_in for var_in in var_items_consumed[item_name])
        solver.Add(sum_out - sum_in == var_items_sold[item_name])

    print("Number of variables =", solver.NumVariables())
    print("Number of constraints =", solver.NumConstraints())

    # Objective: Maximize points
    sum_points = sum(var_items_sold[item_name] * sink_points[item_name]
                     for item_name in item_names)
    solver.Maximize(sum_points)

    print(f"Solving with {solver.SolverVersion()}")
    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        print("Solution:")
        print("Objective value =", solver.Objective().Value())
        for item_name, var_item in var_items_sold.items():
            print(item_name, "=", var_item.solution_value())
    else:
        print("The problem does not have an optimal solution.")


item_names = [
    'iron_rod',
    'iron_plate',
    'iron_ingot',
    'iron_ore',
    'screw',
    'reinforced_iron_plate',
]

recipes = [
    ({'iron_ore': 1}, {'iron_ingot': 1}),
    ({'iron_ingot': 3}, {'iron_plate': 2}),
    ({'iron_ingot': 1}, {'iron_rod': 1}),
    ({'iron_rod': 1}, {'screw': 4}),
    ({'iron_plate': 6, 'screw': 12}, {'reinforced_iron_plate': 1})
]

resources_available = {
    'iron_ore': 120,
}

sink_points = {
    'iron_ore': 1,
    'iron_ingot': 2,
    'iron_rod': 4,
    'iron_plate': 6,
    'screw': 2,
    'reinforced_iron_plate': 120,
}

solve(item_names, recipes, resources_available, sink_points)
