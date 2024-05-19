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


class SatisfactoryLP:

    def __init__(self, recipes: dict,
                 items_available: dict=game.RESOURCES_AVAILABLE,
                 free_power: float=game.FREE_POWER):
        if not self.check_parameters(items_available):
            exit(1)

        self._objective_specific_report = lambda: None

        self.items_available = items_available

        self.solver = pywraplp.Solver.CreateSolver("GLOP")
        if not self.solver:
            raise RuntimeError("Could not create GLOB solver")

        # variable to optimize are the utilization of each recipe
        self.var_recipes_used = {
            recipe_name: self.solver.NumVar(0, self.solver.infinity(), recipe_name)
            for recipe_name in game.RECIPES
        }
        self.var_item_sold = {
            item_name: self.solver.NumVar(0, self.solver.infinity(), item_name)
            for item_name in game.ITEMS
        }

        # define helper terms
        self.consumed_in_all_recipes = dict()
        for item_name in game.ITEMS:
            self.consumed_in_all_recipes[item_name] = sum(
                game.RECIPES[recipe_name]['ingredients'][item_name] * self.var_recipes_used[recipe_name]
                for recipe_name in recipes
                if recipe_name in game.consumed_by[item_name]
            )
        self.produced_in_all_recipes = dict()
        for item_name in game.ITEMS:
            self.produced_in_all_recipes[item_name] = sum(
                game.RECIPES[recipe_name]['products'][item_name] * self.var_recipes_used[recipe_name]
                for recipe_name in recipes
                if recipe_name in game.produced_by[item_name]
            )
        
        # disable other recipes
        for recipe_name in game.RECIPES:
            if not recipe_name in recipes:
                self.solver.Add(self.var_recipes_used[recipe_name] == 0,
                        f'Disable_{recipe_name}')
                
        self._define_flow_constraints()
        self._define_power_contraints(free_power)

    ################################ constraints ##############################

    def _define_flow_constraints(self):
        for item_name in game.ITEMS:
            required_items = (
                self.consumed_in_all_recipes[item_name]
                 + self.var_item_sold[item_name]
                 - self.produced_in_all_recipes[item_name]
            )
            available = self.items_available.get(item_name, 0)
            self.solver.Add(required_items == available, f'Flow_{item_name}')

    def define_production_rates(self, production_rate: dict):
        """
        Achieve a certain minimum production rate of items

        Args:
            production_rates (dict): Set constraints to achieve at least these production rates of items
        """
        for item_name in game.ITEMS:
            available = self.items_available.get(item_name, 0)
            goal_rate = production_rate.get(item_name, 0)
            self.solver.Add(
                available + self.produced_in_all_recipes[item_name]
                - self.consumed_in_all_recipes[item_name]
                >= goal_rate,
                f'Goal_{item_name}'
            )

    def _define_power_contraints(self, free_power: float):
        amount_facility = {
            facility_name: sum(
                var_recipe
                for recipe_name, var_recipe in self.var_recipes_used.items()
                if game.RECIPES[recipe_name]['producedIn'] == facility_name
            )
            for facility_name in game.PRODUCTION_FACILITIES
        }
        
        power_balance = sum(
            amount_facility[facility_name] * power_consumption
            for facility_name, power_consumption in game.PRODUCTION_FACILITIES.items()
        )
        self.solver.Add(
            power_balance + free_power >= 0,
            'Power balance'
        )

    ################################ objective ##############################

    def set_objective_max_sink_points(self):
        sum_points = 0
        for item_name, item_data in game.ITEMS.items():
            sum_points += self.var_item_sold[item_name] * item_data["sinkPoints"]
        self.solver.Maximize(sum_points)
        self._objective_specific_report = self._report_sold_items

    def set_objective_min_resources_spent(self):
        """Minimize the (mining) resources needed to achieve the given production rates
        """
        if not any('Goal_' in c.name() for c in self.solver.constraints()):
            print('WARNING: No goal production rate has been set.'
                  'Recipes will be all 0')
        
        sum_resources_spent = 0
        for item_name in game.RESOURCES_AVAILABLE:
            sum_resources_spent += self.consumed_in_all_recipes[item_name]
        self.solver.Minimize(sum_resources_spent)
        self._objective_specific_report = self._report_items_required

    ################################### report ###############################

    def _report_sold_items(self):
        print("\nSold items:")
        sum_sink_points = 0
        for item_name in game.ITEMS:
            amount_sold = self.var_item_sold[item_name].solution_value()
            if round(amount_sold, 3) != 0:
                print(item_name, "=", round(amount_sold, 3))
            sum_sink_points += amount_sold * game.ITEMS[item_name]["sinkPoints"]
        print('Total sink points:', round(sum_sink_points,1))

    def _report_items_required(self):
        print("\nRequired items (without goal rates):")
        for item_name in game.RESOURCES_AVAILABLE:
            amount_consumed = self.consumed_in_all_recipes[item_name]
            
            if not type(amount_consumed) == int: # because only sum([]) = 0
                amount_consumed = amount_consumed.solution_value()
            if round(amount_consumed, 3) != 0:
                print(item_name, "=", round(amount_consumed, 3))

    def _report_power(self):
        print("\nPower consumption")
        amount_facility = {
            facility_name: sum(
                var_recipe.solution_value()
                for recipe_name, var_recipe in self.var_recipes_used.items()
                if game.RECIPES[recipe_name]['producedIn'] == facility_name
            )
            for facility_name in game.PRODUCTION_FACILITIES
        }
        
        power_sum = game.FREE_POWER
        print(f'Free power: {power_sum} MW')
        for facility_name, power_consumption in game.PRODUCTION_FACILITIES.items():
            sum_power_of_type = amount_facility[facility_name] * power_consumption
            if round(sum_power_of_type, 3) != 0:
                print(f'{facility_name}({round(amount_facility[facility_name], 1)}):'
                      f' {round(sum_power_of_type, 3)} MW')
            power_sum += sum_power_of_type
        print(f'Total: {round(power_sum, 3)} MW')

    def _report_debug(self):
        for variable in self.solver.variables():
            print(variable.name(), variable.solution_value())

    def report(self):
        print("\nObjective value =", self.solver.Objective().Value())
        print(f"\nProblem solved in {self.solver.wall_time():d} milliseconds")

        print("\nRecipes used:")
        for recipe_name in game.RECIPES:
            recipes_used = self.var_recipes_used[recipe_name].solution_value()
            if round(recipes_used, 3) != 0:
                print(recipe_name, "=", round(recipes_used, 3))

        self._objective_specific_report()


    def check_parameters(self, resources_available: dict) -> bool:
        result = True
        if 'Desc_Water_C' in resources_available:
            print('Water is available unlimited and therefore not in any recipe')
            result = False
        for item_name in resources_available:
            if not item_name in game.ITEMS:
                print('Unknown item:', item_name)
                result = False
        return result
    
    def optimize(self):
        status = self.solver.Solve()
        if status != pywraplp.Solver.OPTIMAL:
            raise RuntimeError("The problem does not have an optimal solution")
        return status


if __name__ == '__main__':
    resources_available = dict()

    # custom
    # resources_available['Desc_OreIron_C'] = 4*480
    # resources_available['Desc_OreCopper_C'] = 2*480
    # resources_available['Desc_Coal_C'] = 4*240
    # resources_available['Desc_Stone_C'] = 2*480
    
    # # current overhead
    # resources_available = {
    #     item_name: amount
    #     for item_name, amount in 
    #     parse_items_from_csv.parse_items('Autonation4.0.csv').items()
    #     if not 'Packaged' in item_name and not 'Water' in item_name
    # }


    # full ressource occupancy
    resources_available = game.RESOURCES_AVAILABLE

    # recipes=dict()
    recipes=game.RECIPES
    problem = SatisfactoryLP(recipes, resources_available)
    problem.define_production_rates({'Desc_PlutoniumFuelRod_C': 6})
    # problem.set_objective_max_sink_points()
    problem.set_objective_min_resources_spent()
    print("Number of variables =", problem.solver.NumVariables())
    print("Number of constraints =", problem.solver.NumConstraints())
    status = problem.optimize()
    problem.report()
    problem._report_power()
    # problem._report_debug()
    