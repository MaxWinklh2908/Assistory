from enum import Enum
from typing import Optional

from ortools.linear_solver import pywraplp

from assistory import game
from assistory.game import ItemValues, RecipeValues
from assistory.optim.static_flow_problem_config import StaticFlowLPConfig


class ReturnCode(Enum):
    OPTIMAL = 0
    FEASIBLE = 1
    INFEASIBLE_OR_UNBOUNDED = 2
    UNBOUNDED = 3
    ABNORMAL = 4
    MODEL_INVALID = 5
    NOT_SOLVED = 6

DEBUG = False


# sum of variable might be integer 0 if no summands in sum
def get_solution_value(x):
    return x.solution_value() if hasattr(x, 'solution_value') else x


class StaticFlowLP:
    """
    Linear problem of the item flow between automated recipes.
    """

    def __init__(self, configuration: StaticFlowLPConfig):
        configuration.check()

        self.objective_value: Optional[float] = None

        self.solver = pywraplp.Solver.CreateSolver("GLOP")
        if not self.solver:
            raise RuntimeError("Could not create GLOB solver")
        pywraplp.Solver.SetSolverSpecificParametersAsString(self.solver, "use_dual_simplex:1")
        
        # variable to optimize are the utilization of each recipe
        self.var_recipes_used = RecipeValues(
            {
                recipe_name: self.solver.NumVar(0, self.solver.infinity(), recipe_name)
                for recipe_name in game.RECIPE_NAMES_AUTOMATED
            },
            omega=game.RECIPE_NAMES_AUTOMATED
        )

        # define helper terms
        self.item_balance = (
            self.var_recipes_used.get_item_rate_balance() + configuration.base_item_rate
        )

        # constraint: limits for item balance
        for item_name, limit in configuration.item_rate_balance_upper_limits.items():
            if limit == float('inf'):
                continue
            self.solver.Add(
                self.item_balance[item_name] <= limit,
                f'Upper_item_rate_balance_limit_{item_name}'
            )
        for item_name, limit in configuration.item_rate_balance_lower_limits.items():
            self.solver.Add(
                self.item_balance[item_name] >= limit,
                f'Lower_item_rate_balance_limit_{item_name}'
            )

        # constraint: item rate balance ratio
        ratio_factor = self.solver.NumVar(0, self.solver.infinity(), 'Ratio_factor')
        for item_name, ratio in configuration.item_rate_balance_ratio.items():
            if ratio == 0:
                continue
            self.solver.Add(
                self.item_balance[item_name] == ratio * ratio_factor,
                f'Item_rate_balance_ratio_{item_name}'
            )

        # constraint: limits for recipe count
        for recipe_name, limit in configuration.recipe_count_upper_limits.items():
            if limit == float('inf'):
                continue
            self.solver.Add(
                self.var_recipes_used[recipe_name] <= limit,
                f'Upper_recipe_count_limit_{recipe_name}'
            )
        for recipe_name, limit in configuration.recipe_count_lower_limits.items():
            if limit == 0:
                continue
            self.solver.Add(
                self.var_recipes_used[recipe_name] >= limit,
                f'Lower_recipe_count_limit_{recipe_name}'
            )

        # constraint: limits for recipe count
        for recipe_group, limit in configuration.recipe_group_count_upper_limits.items():
            recipe_group_count = sum(
                self.var_recipes_used[recipe_name]
                for recipe_name in recipe_group
            )
            self.solver.Add(
                recipe_group_count <= limit,
                f'Upper_recipe_group_count_limit_{recipe_group}'
            )
        for recipe_group, limit in configuration.recipe_group_count_lower_limits.items():
            recipe_group_count = sum(
                self.var_recipes_used[recipe_name]
                for recipe_name in recipe_group
            )
            self.solver.Add(
                recipe_group_count >= limit,
                f'Lower_recipe_group_count_limit_{recipe_group}'
            )

        # objective: recipe count
        if configuration.minimize_recipe_count or configuration.maximize_recipe_count:
            objective = sum(
                weight * self.var_recipes_used[recipe_name]
                for recipe_name, weight in configuration.recipe_weights.items()
                if weight > 0 # speed up by excluding; formula unchanged
            )
            if configuration.minimize_recipe_count:
                self.solver.Minimize(objective)
            elif configuration.maximize_recipe_count:
                self.solver.Maximize(objective)
        
        # objective: item rate balance
        elif configuration.minimize_item_rate_balance or configuration.maximize_item_rate_balance:
            objective = sum(
                weight * self.item_balance[item_name]
                for item_name, weight in configuration.item_weights.items()
                if weight > 0 # speed up by excluding; formula unchanged
            )
            if configuration.minimize_item_rate_balance:
                self.solver.Minimize(objective)
            elif configuration.maximize_item_rate_balance:
                self.solver.Maximize(objective)
        
    def optimize(self) -> ReturnCode:
        """Find the optimal solution for the problem.

        Returns:
            ReturnCode: Solver return code
        """
        if self.objective_value != None:
            raise RuntimeError('Problem already optimized')
        if DEBUG:
            print("Number of variables =", self.solver.NumVariables())
            print("Number of constraints =", self.solver.NumConstraints())
        code = ReturnCode(self.solver.Solve())
        if code == ReturnCode.OPTIMAL:
            self.objective_value = self.solver.Objective().Value()
        return code
    
    def get_recipes_used(self) -> RecipeValues:
        """
        Get the count of automatedrecipes used for each recipe

        Returns:
            RecipeAmounts: Recipe count by automated recipe name
        """
        return RecipeValues(
            {
                recipe_name: variable.solution_value()
                for recipe_name, variable in self.var_recipes_used.items()
            },
            omega=game.RECIPE_NAMES_AUTOMATED
        )
    
    def get_item_rate_balance(self) -> ItemValues:
        """
        Get the item rate balance for each item

        Returns:
            ItemAmounts: Item rate balance by item name
        """
        return ItemValues({
            item_name: get_solution_value(self.item_balance[item_name])
            for item_name in game.ITEMS
        })

    def report_solution_value(self):
        print('\nSolution value:')
        for variable in self.solver.variables():
            print(variable.name(), variable.solution_value())

    def report_shadow_prices(self):
        print('\nShadow prices of items available')
        activities = self.solver.ComputeConstraintActivities()
        o = [
            {
                'Name': c.name(),
                'shadow price': c.dual_value(),
                'slack': c.ub() - activities[i]
            } 
            for i, c in enumerate(self.solver.constraints())
        ]
        import pandas as pd
        print(pd.DataFrame(o).to_string())

    def report(self):
        print(f"\nObjective value = {round(self.solver.Objective().Value(), 3)}")
        print(f"\nProblem solved in {self.solver.wall_time():d} milliseconds")
