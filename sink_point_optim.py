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
import utils


class SatisfactoryLP:

    def __init__(self, recipes: dict,
                 items_available: dict=dict(),
                 resource_nodes_available: dict=game.NODES_AVAILABLE,
                 free_power: float=game.FREE_POWER):
        """Create a Satisfactory Linear Program

        Args:
            recipes (dict): Available recipes
            items_available (dict, optional): Available existing item
                production (in items/minute). Defaults to dict().
            resource_nodes_available (dict, optional): Available resource nodes
                where mining recipes can be applied. Defaults to game.NODES_AVAILABLE.
            free_power (float, optional): Existing power capacity. Defaults to game.FREE_POWER.

        Raises:
            RuntimeError: Invalid parameters given
        """

        if not self.check_parameters(items_available, resource_nodes_available):
            exit(1)

        self._objective_specific_report = lambda: None

        self.items_available = items_available
        self.free_power = free_power

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
                game.RECIPES[recipe_name]['ingredients'][item_name]
                * self.var_recipes_used[recipe_name]
                / (game.RECIPES[recipe_name]['time'] / 60)
                for recipe_name in recipes
                if recipe_name in game.consumed_by[item_name]
            )
        self.produced_in_all_recipes = dict()
        for item_name in game.ITEMS:
            self.produced_in_all_recipes[item_name] = sum(
                game.RECIPES[recipe_name]['products'][item_name]
                * self.var_recipes_used[recipe_name]
                / (game.RECIPES[recipe_name]['time'] / 60)
                for recipe_name in recipes
                if recipe_name in game.produced_by[item_name]
            )
        
        # disable other recipes
        for recipe_name in game.RECIPES:
            if not recipe_name in recipes:
                self.solver.Add(self.var_recipes_used[recipe_name] == 0,
                                f'Disable_{recipe_name}')
                
        self._define_flow_constraints()
        self._define_power_contraints()
        self._define_non_sellable_items()
        self._define_resource_node_constraints(resource_nodes_available)

    ################################ constraints ##############################

    def _define_flow_constraints(self):
        for item_name in game.ITEMS:
            required_items = (
                self.consumed_in_all_recipes[item_name]
                 + self.var_item_sold[item_name]
                 - self.produced_in_all_recipes[item_name]
            )
            available = self.items_available.get(item_name, 0)
            self.solver.Add(required_items == available,
                            f'Flow_{item_name}')

    def _define_non_sellable_items(self):
        for item_name, item_data in game.ITEMS.items():
            if item_data['sinkPoints'] == 0:
                self.solver.Add(self.var_item_sold[item_name] == 0,
                                f'Non-sellable_{item_name}')

    def define_sell_rates(self, production_rate: dict):
        """
        Achieve a certain minimum production rate of items. The rates are
        defined in items/minute.

        Args:
            production_rates (dict): Set constraints to achieve at least these
            production rates of items
        """
        if any(item_name in game.NON_SELLABLE_ITEMS
               for item_name, rate in production_rate.items()
               if rate > 0):
            raise ValueError('Can not require selling of: ' + item_name)

        if any(item_name in game.NON_PRODUCABLE_ITEMS
               for item_name, rate in production_rate.items()
               if rate - self.items_available.get(item_name, 0) > 0):
            raise ValueError('Can not require production of: ' + item_name)

        for item_name in game.ITEMS:
            available = self.items_available.get(item_name, 0)
            goal_rate = production_rate.get(item_name, 0)
            self.solver.Add(
                available + self.produced_in_all_recipes[item_name]
                - self.consumed_in_all_recipes[item_name]
                >= goal_rate,
                f'Goal_{item_name}'
            )

    def _define_power_contraints(self):
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
            power_balance + self.free_power >= 0,
            'Power_balance'
        )

    def _define_resource_node_constraints(self, resource_nodes_available: dict):
        for resource_node_name in game.NODES_AVAILABLE:
            amount = resource_nodes_available.get(resource_node_name, 0)
            self.solver.Add(self.var_recipes_used[resource_node_name] <= amount,
                            'Nodes_' + resource_node_name)

    ################################ objective ##############################

    def set_objective_max_sink_points(self):
        sum_points = 0
        for item_name, item_data in game.ITEMS.items():
            sum_points += self.var_item_sold[item_name] * item_data["sinkPoints"]
        self.solver.Maximize(sum_points)

        self._objective_specific_report = self._report_sold_items

    def set_objective_min_resources_spent(self, weighted=False):
        """Minimize the required resource nodes (and wells) needed to achieve
        the given production rates

        Args:
            weighted (bool, optional): Whether rare resources should be spent
            less than common ones. Defaults to False.
        """
        if not any('Goal_' in c.name() for c in self.solver.constraints()):
            print('WARNING: No goal production rate has been set.'
                  'Recipes will be all 0')
            
        sum_resource_nodes = 0
        
        for node_name in game.NODES_AVAILABLE:
            weight = 1
            if weighted:
                weight = 1/game.NODES_AVAILABLE[node_name]
            sum_resource_nodes += weight * self.var_recipes_used[node_name] 

        self.solver.Minimize(sum_resource_nodes)
        self._objective_specific_report = self._report_resource_nodes_required

    def set_objective_min_recipes(self):
        """Minimize the required recipes to achieve
        the given production rates.
        """
        if not any('Goal_' in c.name() for c in self.solver.constraints()):
            print('WARNING: No goal production rate has been set.'
                  'Recipes will be all 0')
            
        cnt_recipes = 0
        for recipe_name in game.RECIPES:
            weight = 1
            cnt_recipes += weight * self.var_recipes_used[recipe_name] 

        self.solver.Minimize(cnt_recipes)
        self._objective_specific_report = self.report_items_produced_to_sell

    ################################### report ###############################

    def _report_sold_items(self):
        print("\nSold items:")
        sum_sink_points = 0
        for item_name in game.ITEMS:
            amount_sold = self.var_item_sold[item_name].solution_value()
            if round(amount_sold, 3) != 0:
                print(game.get_bare_item_name(item_name), "=",
                      round(amount_sold, 3))
            sum_sink_points += amount_sold * game.ITEMS[item_name]["sinkPoints"]
        print('Total sink points:', round(sum_sink_points,1))

    def _report_resource_nodes_required(self):
        print("\nRequired resource nodes:")
        for resource_node_name in game.NODES_AVAILABLE:
            amount_required = self.var_recipes_used[resource_node_name].solution_value()
            if round(amount_required, 3) != 0:
                print(game.get_bare_item_name(resource_node_name),
                      "=", round(amount_required, 3))

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
        
        sum_consumption = 0
        print(f'Free power: {self.free_power} MW')
        for facility_name, power_consumption in game.PRODUCTION_FACILITIES.items():
            sum_power_of_type = amount_facility[facility_name] * power_consumption
            if round(sum_power_of_type, 3) != 0:
                print(f'{game.get_bare_item_name(facility_name)}'
                      f'({round(amount_facility[facility_name], 1)}) = '
                      f' {round(sum_power_of_type, 3)} MW')
            if sum_power_of_type < 0:
                sum_consumption += abs(sum_power_of_type)
        print(f'Total consumption: {round(sum_consumption, 3)} MW')

    def _report_debug(self):
        for variable in self.solver.variables():
            print(variable.name(), variable.solution_value())

    def _report_recipes_used(self):
        print("\nRecipes used:")
        for recipe_name in game.RECIPES:
            recipes_used = self.var_recipes_used[recipe_name].solution_value()
            if round(recipes_used, 3) != 0:
                print(game.get_bare_item_name(recipe_name), "=", round(recipes_used, 3))

    def report_shadow_prices(self):
        print('Shadow prices of items available')
        activities = self.solver.ComputeConstraintActivities()
        o = [
            {
                'Name': c.name(),
                'shadow price': c.dual_value(),
                'slack': c.ub() - activities[i]
            } 
            for i, c in enumerate(self.solver.constraints())
            if (
                ('Flow_' in c.name() and c.name()[5:] in self.items_available)
                or ('Nodes_' in c.name())
            )
        ]
        import pandas as pd
        print(pd.DataFrame(o).to_string())

    def report_items_produced_to_sell(self):
        print("\nSold items (excluding items available):")
        for item_name in game.ITEMS:
            amount_sold = self.var_item_sold[item_name].solution_value()
            amount_available = self.items_available.get(item_name, 0)
            produced_to_sell = round(max(0, amount_sold - amount_available), 3)
            if produced_to_sell == 0:
                continue
            print(game.get_bare_item_name(item_name), "=", produced_to_sell)

    def report(self, debug=False):
        print("\nObjective value =", self.solver.Objective().Value())
        print(f"\nProblem solved in {self.solver.wall_time():d} milliseconds")

        self._report_recipes_used()
        self._report_power()
        
        if debug:
            self._report_debug()

        self._objective_specific_report()

    def get_recipes_used(self) -> dict:
        return {
            recipe_name: self.var_recipes_used[recipe_name].solution_value()
            for recipe_name in game.RECIPES
        }

    def check_parameters(self, resources_available: dict,
                         resource_nodes_available: dict) -> bool:
        result = True
        for item_name in resources_available:
            if not item_name in game.ITEMS:
                print('ERROR Unknown item:', item_name)
                result = False
            if resources_available[item_name] < 0:
                raise ValueError('Resource node availability can not be negative')
        for node_name in resource_nodes_available:
            if node_name not in game.NODES_AVAILABLE:
                print('ERROR Unknown resource node:', node_name)
                result = False
            if resource_nodes_available[node_name] < 0:
                raise ValueError('Resource node availability can not be negative')
        return result
    
    def optimize(self):
        status = self.solver.Solve()
        if status != pywraplp.Solver.OPTIMAL:
            raise RuntimeError("The problem does not have an optimal solution")
        return status


if __name__ == '__main__':
    ################# items available ######################
    items_available = dict()

    # custom
    # items_available['Desc_OreIron_C'] = 480
    # items_available['Desc_OreCopper_C'] = 480
    # items_available['Desc_Coal_C'] = 240
    # items_available['Desc_Stone_C'] = 480
    
    # current production (state: state: CO2-Neutral)
    items_available = {
        item_name: amount
        for item_name, amount
        in utils.parse_items('Autonation4.0.csv').items()
        if not 'Packaged' in item_name and not 'Water' in item_name
    }

    ################# recipes ######################
    recipes=game.RECIPES

    # recipes=dict()
    # recipes['Recipe_IngotIron_C'] = game.RECIPES['Recipe_IngotIron_C']
    # recipes['Recipe_IngotCopper_C'] = game.RECIPES['Recipe_IngotCopper_C']
    # recipes['Recipe_WaterExtractorWater_C'] = game.RECIPES['Recipe_WaterExtractorWater_C']
    # recipes['Recipe_Alternate_SteamedCopperSheet_C'] = game.RECIPES['Recipe_Alternate_SteamedCopperSheet_C']

    ################# resource nodes available ######################
    # resource_nodes_available = game.NODES_AVAILABLE
    
    # Current coverage (state: CO2-Neutral)
    resource_nodes_available=dict()
    resource_nodes_available['Recipe_MinerMk3Stone_C'] =                       game.NODES_AVAILABLE['Recipe_MinerMk3Stone_C'] - (0 * 0.5   + 4   + 1 * 2)
    resource_nodes_available['Recipe_MinerMk3OreIron_C'] =                     game.NODES_AVAILABLE['Recipe_MinerMk3OreIron_C'] - (5 * 0.5   + 7   + 8 * 2)
    resource_nodes_available['Recipe_MinerMk3OreCopper_C'] =                   game.NODES_AVAILABLE['Recipe_MinerMk3OreCopper_C'] - (2 * 0.5   + 5  + 2 * 2)
    resource_nodes_available['Recipe_MinerMk3OreGold_C'] =                     game.NODES_AVAILABLE['Recipe_MinerMk3OreGold_C'] - (0 * 0.5   + 2   + 1 * 2)
    resource_nodes_available['Recipe_MinerMk3Coal_C'] =                        game.NODES_AVAILABLE['Recipe_MinerMk3Coal_C'] - (0 * 0.5   + 4  + 3 * 2)
    resource_nodes_available['Recipe_MinerMk3Sulfur_C'] =                      game.NODES_AVAILABLE['Recipe_MinerMk3Sulfur_C'] - (0 * 0.5   + 3   + 1 * 2)
    resource_nodes_available['Recipe_MinerMk3OreBauxite_C'] =                  game.NODES_AVAILABLE['Recipe_MinerMk3OreBauxite_C'] - (5 * 0.5   + 2   + 2 * 2)
    resource_nodes_available['Recipe_MinerMk3RawQuartz_C'] =                   game.NODES_AVAILABLE['Recipe_MinerMk3RawQuartz_C'] - (0 * 0.5   + 3  + 0 * 2)
    resource_nodes_available['Recipe_MinerMk3OreUranium_C'] =                  game.NODES_AVAILABLE['Recipe_MinerMk3OreUranium_C'] - (0 * 0.5   + 2   + 0 * 2)
    resource_nodes_available['Recipe_OilExtractorLiquidOil_C'] =               game.NODES_AVAILABLE['Recipe_OilExtractorLiquidOil_C'] - (1 * 0.5  + 4  + 4 * 2)
    resource_nodes_available['Recipe_ResourceWellPressurizerNitrogenGas_C'] =  game.NODES_AVAILABLE['Recipe_ResourceWellPressurizerNitrogenGas_C'] - (1 * 0.5   + 0   + 9 * 2)
    resource_nodes_available['Recipe_ResourceWellPressurizerLiquidOil_C'] =    game.NODES_AVAILABLE['Recipe_ResourceWellPressurizerLiquidOil_C'] - (0 * 0.5   + 0   + 0 * 2)


    problem = SatisfactoryLP(recipes=recipes,
                             items_available=items_available,
                             resource_nodes_available=resource_nodes_available,
                             free_power=10000)

    ################# minimal production rates ######################

    # Goal: Produce at least 1 item of every kind (except impractical items)
    problem.define_sell_rates({
        item_name: 1 for item_name in game.ITEMS
        if not item_name in game.NON_PRODUCABLE_ITEMS
        and not item_name in game.NON_SELLABLE_ITEMS
        and not item_name in game.RADIOACTIVE_ITEMS
        and not item_name in game.LIQUID_ITEMS
        and not item_name in game.ITEMS_FROM_MINING
        and not 'Ingot' in item_name
    })

    # problem.set_objective_max_sink_points()
    # problem.set_objective_min_resources_spent(weighted=True)
    problem.set_objective_min_recipes()

    print("Number of variables =", problem.solver.NumVariables())
    print("Number of constraints =", problem.solver.NumConstraints())

    status = problem.optimize()

    problem.report()
    # problem.report_shadow_prices()

    utils.write_recipes(problem.get_recipes_used(), 'construction_plan.json')
    