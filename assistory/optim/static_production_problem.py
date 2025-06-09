"""
Create an optimal production, i.e. amounts of recipes, given an objective
and constraints using linear optimization.
"""
from typing import Optional

from assistory import game
from assistory.game import ItemValues, RecipeValues, BuildingValues
from assistory.optim import static_flow_problem
from assistory.optim.static_flow_problem import ReturnCode
from assistory.optim.static_flow_problem_config import StaticFlowLPConfig
from assistory.optim.static_production_problem_config import StaticProductionLPConfig


# TODO: Make neutralization of non-sellable item production optional
class StaticProductionLP:
    """
    Linear problem of the item production between automated recipes including
    power constraints
    """

    def __init__(self, production_lp_config: StaticProductionLPConfig):
        """Create a Satisfactory Linear Program

        Args:
            production_lp_config (StaticProductionLPConfig): Configuration of
                the static production linear program
        """
        production_lp_config.check()

        self.objective_value: Optional[float] = None

        self._objective_specific_report = lambda: None

        flow_lp_config = StaticFlowLPConfig()
        flow_lp_config.base_item_rate = production_lp_config.base_item_rate.copy()

        # define locked recipes
        flow_lp_config.recipe_count_upper_limits = production_lp_config.get_recipe_count_upper_limits()
        
        # In a fully automated production, each produced item must be able
        # to be put into the sink to be consumed by a sink.
        # Liquids and some items can not be put to sink.
        for item_name in game.ITEM_NAMES_NON_SELLABLE:
            flow_lp_config.item_rate_balance_upper_limits[item_name] = 0

        # Resource node constraints
        flow_lp_config.recipe_group_count_upper_limits = production_lp_config.get_recipe_group_count_upper_limits()

        # Sell rate ratio
        flow_lp_config.item_rate_balance_ratio = production_lp_config.sell_rate_ratio.copy()
        # TODO: Together with maxi. item rate is alternative to iterative fastest production

        # Minimum sell rate
        flow_lp_config.item_rate_balance_lower_limits.update(
            production_lp_config.sell_rate_lower_limits
        )

        # objective maximize_sink_points
        if production_lp_config.maximize_sink_points:
            flow_lp_config.maximize_item_rate_balance = True
            flow_lp_config.item_weights = ItemValues({
                item_name: item_data["sinkPoints"]
                for item_name, item_data in game.ITEMS.items()
            })
            self._objective_specific_report = self._report_sold_items

        # objective min resource node usage
        if production_lp_config.minimize_resource_node_usage:
            flow_lp_config.minimize_recipe_count = True
            weights_resource_node = production_lp_config.get_weights_resource_node()

            # All other reciepes shell not be limited -> weight of 0 ignores them in objective
            flow_lp_config.recipe_weights = RecipeValues(omega=game.RECIPE_NAMES_AUTOMATED)

            # Recipes from nodes with amount = 0 are limited by recipe group -> No positive weight required
            for resource_node_name, weight in weights_resource_node.items():
                for recipe_name in game.RESOURCE_NODES[resource_node_name]['extraction_recipes']:
                    flow_lp_config.recipe_weights[recipe_name] = weight
            self._objective_specific_report = self._report_resource_nodes_required

        # objective: minimize number of recipes
        if production_lp_config.minimize_recipe_count:
            flow_lp_config.minimize_recipe_count = True
            flow_lp_config.recipe_weights = production_lp_config.weights_recipe.copy()

        # objective: maximize item rates balance (sell rate)
        if production_lp_config.maximize_sell_rate:
            flow_lp_config.maximize_item_rate_balance = True
            flow_lp_config.item_weights = production_lp_config.weights_sell_rate.copy()
            self._objective_specific_report = self._report_sold_items

        # instantiate problem here to add custom constraints later
        self.problem = static_flow_problem.StaticFlowLP(flow_lp_config)

        # power constraints
        buildings_used = self.problem.var_recipes_used.get_buildings()
        power_balance = buildings_used.get_power_balance()
        self.problem.solver.Add(
            production_lp_config.base_power + power_balance >= 0,
            'Power_balance'
        )

    def get_recipes_used(self) -> RecipeValues:
        return self.problem.get_recipes_used()
    
    def get_item_balance(self) -> ItemValues:
        return self.problem.get_item_rate_balance()
    
    def optimize(self) -> ReturnCode:
        """Find the optimal solution for the problem.

        Returns:
            ReturnCode: Solver return code
        """
        if self.objective_value != None:
            raise RuntimeError('Problem already optimized')
        code = self.problem.optimize()
        if code == ReturnCode.OPTIMAL:
            self.objective_value = self.problem.objective_value
        return code

    ################################### report ###############################

    def _report_sold_items(self):
        print("\nSold items (/min):")
        sum_sink_points = 0
        item_balance = self.get_item_balance().round(3).as_dict_ignoring(0)
        for item_name, rate in item_balance.items():
            print(f"{game.get_bare_name(item_name)} = {rate}")
            sum_sink_points += rate * game.ITEMS[item_name]["sinkPoints"]

    def _report_resource_nodes_required(self):
        print("\nRequired resource nodes:")
        resource_nodes_required = self.get_recipes_used().get_resource_nodes_used()
        resource_nodes_required.round(3).pprint(0)

    def _report_power(self):
        print("\nPower balance (MW):")        
        sum_consumption = 0
        buildings_used = self.get_recipes_used().get_buildings()
        buildings_used.get_power_balance()
        buildings_used = buildings_used.round(3).as_dict_ignoring(0)
        for facility_name, amount in buildings_used.items():
            name = game.get_bare_name(facility_name)
            sum_power_of_type = BuildingValues(
                {facility_name: amount}, omega=[facility_name]
            ).get_power_balance()
            print(f'{name}({round(amount, 3)}) = {round(sum_power_of_type, 3)}')
            sum_consumption += sum_power_of_type
        print(f'Total balance: {round(sum_consumption, 3)} MW')

    def report(self, debug=False):
        self._report_power()
        self._report_resource_nodes_required()
        
        if debug:
            self.problem.report_solution_value()
            self.problem.report_shadow_prices()

        self._objective_specific_report()
        self.problem.report()
