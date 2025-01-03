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

from assistory.game import game


RETURN_CODES = {
 2: 'INFEASIBLE',
 5: 'MODEL_INVALID',
 6: 'NOT_SOLVED',
 0: 'OPTIMAL',
 3: 'UNBOUNDED',
}

# TODO: Make neutralization of non-sellable item production optional
class SatisfactoryLP:

    def __init__(self, recipes: dict,
                 items_available: dict=dict(),
                 resource_nodes_available: dict=game.NODE_RECIPES_AVAILABLE,
                 free_power: float=0):
        """Create a Satisfactory Linear Program

        Args:
            recipes (dict): Available recipes
            items_available (dict, optional): Available existing item
                production (in items/minute). Defaults to dict().
            resource_nodes_available (dict, optional): Available mining recipes
                where items (by miners) and power (by geotermal generator) can
                be generated. Defaults to game.NODE_RECIPES_AVAILABLE.
            free_power (float, optional): Additionally extend power constraint.
                Defaults to 0.

        Raises:
            RuntimeError: Invalid parameters given
        """

        if not self._check_parameters(items_available, resource_nodes_available):
            exit(1)

        self._recipes = recipes
        self.items_available = items_available
        self.resource_nodes_available = resource_nodes_available
        self.free_power = free_power

        self._objective_specific_report = lambda: None
        self.producable_items = None

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
        # self._define_non_sellable_items() # why is that needed?
        self._define_resource_node_constraints()

    def _check_parameters(self, resources_available: dict,
                         resource_nodes_available: dict) -> bool:
        result = True
        for item_name in resources_available:
            if not item_name in game.ITEMS:
                print('ERROR Unknown item:', item_name)
                result = False
            if resources_available[item_name] < 0:
                raise ValueError('Resource node availability can not be negative')
        for node_name in resource_nodes_available:
            if node_name not in game.NODE_RECIPES_AVAILABLE:
                print('ERROR Unknown resource node:', node_name)
                result = False
            if resource_nodes_available[node_name] < 0:
                raise ValueError('Resource node availability can not be negative')
        return result
    
    def get_recipes_used(self) -> dict:
        return {
            recipe_name: self.var_recipes_used[recipe_name].solution_value()
            for recipe_name in game.RECIPES
            if self.var_recipes_used[recipe_name].solution_value() > 0
        }
    
    def get_items_sold(self) -> dict:
        return {
            item_name: self.var_item_sold[item_name].solution_value()
            for item_name in game.ITEMS
            if self.var_item_sold[item_name].solution_value() > 0
        }
    
    def get_producable_items(self) -> set:
        if self.producable_items is None:
            self.producable_items = get_producable_items(self._recipes,
                                                        self.items_available,
                                                        self.resource_nodes_available)
        return self.producable_items.copy()

    def optimize(self) -> int:
        """Find the optimal solution for the problem.

        Returns:
            int: Solver return code
        """
        return self.solver.Solve()

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
        for item_name in game.ITEMS_NON_SELLABLE:
            self.solver.Add(self.var_item_sold[item_name] == 0,
                            f'Non-sellable_{item_name}')
            
    def define_sell_rate_ratio(self, item_rate_ratios: dict):
        """Specify the fraction of each item to the overall item rate.

        Args:
            item_rate_ratios (dict): Mapping of item names to a sell rate.
            The ratio is the fractio of this sell rate over the sell rate sum
            of all items.
        """
        # TODO: Together with maxi. item rate is alternative to iterative fastest production
        if any(k < 0 for k in item_rate_ratios.values()):
            raise ValueError('Expect nonnegative ratios')
        item_rate_ratios = {item_name: ratio
                           for item_name, ratio in item_rate_ratios.items()
                           if ratio > 0}

        producable_items = self.get_producable_items()
        for item_name, ratio in item_rate_ratios.items():
            if ratio == 0:
                continue
            if item_name in game.ITEMS_NON_SELLABLE:
                raise ValueError('Can not require selling of: ' + item_name)

            if not item_name in producable_items:
                raise ValueError('Can not require production of: ' + item_name)

        sell_ratio_factor = self.solver.NumVar(0, self.solver.infinity(), 'Sell_ratio_factor')
        for item_name, ratio in item_rate_ratios.items():
            sell_rate = (
                self.items_available.get(item_name, 0)
                + self.produced_in_all_recipes[item_name]
                - self.consumed_in_all_recipes[item_name]
            )
            ratio = item_rate_ratios[item_name]
            self.solver.Add(sell_rate / ratio == sell_ratio_factor, f'Sell_ratio_{item_name}')
    
    def define_sell_rates(self, production_rate: dict):
        """
        Achieve a certain minimum production rate of items. The rates are
        defined in items/minute.

        Args:
            production_rates (dict): Set constraints to achieve at least these
            production rates of items
        """
        producable_items = self.get_producable_items()
        for item_name, rate in production_rate.items():
            if rate > 0 and item_name in game.ITEMS_NON_SELLABLE:
                raise ValueError('Can not require selling of: ' + item_name)

            if (rate - self.items_available.get(item_name, 0) > 0
                    and not item_name in producable_items):
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
            for facility_name in game.BUILDINGS
        }
        
        power_consumption = sum(
            amount_facility[facility_name] * facility['power_consumption']
            for facility_name, facility in game.BUILDINGS.items()
        )
        self.solver.Add(
            power_consumption - self.free_power <= 0,
            'Power_balance'
        )

    def _define_resource_node_constraints(self):
        for resource_node_name in game.NODE_RECIPES_AVAILABLE:
            amount = self.resource_nodes_available.get(resource_node_name, 0)
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
        
        for node_name in self.resource_nodes_available:
            weight = 1
            amount = self.resource_nodes_available[node_name]
            if weighted and amount > 0:
                weight = 1/amount
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
            weight = 1 # TODO: parametrize weight
            cnt_recipes += weight * self.var_recipes_used[recipe_name] 

        self.solver.Minimize(cnt_recipes)
        self._objective_specific_report = self.report_items_produced_to_sell

    def set_objective_max_item_rate(self, item_name: str):
        """Maximize the sell rate of a single item

        Args:
            item_name (str): item to maximize production
        """
        self.solver.Maximize(self.var_item_sold[item_name])
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
        for resource_node_name in game.NODE_RECIPES_AVAILABLE:
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
            for facility_name in game.BUILDINGS
        }
        
        sum_consumption = 0
        print(f'Free power: {-self.free_power} MW')
        for facility_name, facility in game.BUILDINGS.items():
            power_consumption = facility['power_consumption']
            sum_power_of_type = amount_facility[facility_name] * power_consumption
            if round(sum_power_of_type, 3) != 0:
                print(f'{game.get_bare_item_name(facility_name)}'
                      f'({round(amount_facility[facility_name], 1)}) = '
                      f' {round(sum_power_of_type, 3)} MW')
            if sum_power_of_type > 0:
                sum_consumption += sum_power_of_type
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

    
def get_producable_items(
        recipes: dict=game.RECIPES,
        items_available: dict=dict(),
        resource_nodes_available: dict=game.NODE_RECIPES_AVAILABLE) -> set:
    """Return a all items that can theoretically be produced with the given
    recipes and available items and resource nodes.

    Args:
        recipes (dict): Available recipes
            items_available (dict, optional): Available existing item
                production (in items/minute). Defaults to game.RECIPES.
            resource_nodes_available (dict, optional): Available resource nodes
                where mining recipes can be applied. Defaults to game.NODE_RECIPES_AVAILABLE.NODE_RECIPES_AVAILABLE.

    Returns:
        set: set of item names
    """
    producable_item_names = set()
    for item_name in game.ITEMS:
        lp = SatisfactoryLP(recipes, items_available, resource_nodes_available)
        # Note: calling lp.get_producable_items here would infinitely loop
        lp.set_objective_max_item_rate(item_name)
        status = lp.optimize()
        if status != pywraplp.Solver.OPTIMAL:
            raise RuntimeError('Unexpected status: ' + RETURN_CODES[status])
        rate = lp.solver.Objective().Value()
        if rate > 0:
            producable_item_names.add(item_name)
    return producable_item_names
