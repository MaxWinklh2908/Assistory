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
from dataclasses import dataclass, field
from typing import Dict, Tuple
import yaml

from assistory import game
from assistory.game import ItemValues, RecipeValues, ResourceNodeValues, RecipeFlags
from assistory.optim import static_flow_problem_config


def get_default_node_recipes_all(x: float) -> ResourceNodeValues:
    out = ResourceNodeValues()
    out.set_values(x)
    return out


@dataclass
class StaticProductionLPConfig():

    # TODO: allow_selling_liquid: bool = False
    # TODO: allow_selling_zero_sink_point_items: bool = False
    # TODO: disable_power: bool = False
    
    # Nonnegative minimum sell rate of items that must be achieved. Defaults
    # to all 0.
    sell_rate_lower_limits: ItemValues = field(
        default_factory=ItemValues
    )
    
    # A ratio (>0) of sell rates that must be enforced as mapping from item name
    # to ratio. All items with value == 0 are ignored. Defaults to all 0.
    sell_rate_ratio: ItemValues = field(
        default_factory=ItemValues
    )
    
    # Nonnegative available resource nodes. Defaults to game.NODE_RECIPES_AVAILABLE.
    available_resource_nodes: ResourceNodeValues = field(
        default_factory=lambda: ResourceNodeValues(game.NODE_RECIPES_AVAILABLE)
    )
    
    # Names of available automated recipes. All undefined recipes are unavailable.
    # Defaults to all recipes.
    unlocked_recipes: RecipeFlags = field(
        default_factory=lambda: RecipeFlags(game.RECIPES)
    )
    
    # Additionally extend power constraint in MW. May be negative.
    # Defaults to 0.
    base_power: float = 0
    
    # Available existing item production (in items/minute). May be negative.
    # Defaults to all 0.
    base_item_rate: ItemValues = field(
        default_factory=ItemValues
    )


    # TODO: Better typing to connect objective with weights

    # Set objective: Maximize sink point earning rate
    maximize_sink_points: bool = False

    # Set objective: Minimize the number of resource node recipes
    minimize_resource_node_usage: bool = False
    # Custom nonnegative weights of resource nodes in the sum. Exclude item from
    # the objective by setting it's weight to 0. Defaults to all 1.
    weights_resource_node: ResourceNodeValues = field(
        default_factory=lambda: get_default_node_recipes_all(1)
    )
    # The weights of the resource node are deduced from the available resource nodes
    deduce_weights_resource_node_from_available_resource_nodes: bool = False

    # Set objective: Minimize the overall number of recipes
    minimize_recipe_count: bool = False
    # Custom nonnegative weights of recipes in overall sum. Exclude recipe from
    # the objective by setting it's weight to 0. Defaults to all 1.
    weights_recipe: RecipeValues = field(
        default_factory=lambda: static_flow_problem_config.get_default_recipes_all(1)
    )
    
    # Set objective: Maximize the sum of the sell rates
    maximize_sell_rate: bool = False
    # Custom nonnegative weights of items in the sum. Exclude item from
    # the objective by setting it's weight to 0. Defaults to all 1.
    weights_sell_rate: ItemValues = field(
        default_factory=lambda: static_flow_problem_config.get_default_items_all(1)
    )

    def check(self):
        static_flow_problem_config.test_not_negative(
            self.sell_rate_lower_limits,
            'Lower limit of sell rates',
        )
        static_flow_problem_config.test_not_negative(
            self.sell_rate_ratio,
            'Sell rate ratio'
        )
        static_flow_problem_config.test_not_negative(
            self.available_resource_nodes,
            'Available resource nodes',
        )
        static_flow_problem_config.test_not_negative(
            self.weights_resource_node,
            'Resource node weights',
        )
        static_flow_problem_config.test_not_negative(
            self.weights_recipe,
            'Recipe weights',
        )
        static_flow_problem_config.test_not_negative(
            self.weights_sell_rate,
            'Sell rate weights',
        )
        if (self.deduce_weights_resource_node_from_available_resource_nodes
                and self.weights_resource_node != get_default_node_recipes_all(1)
            ):
            print('WARNING: Deduce resource node weights from the available'
                  ' resource nodes and overwrite weights_resource_node')

    def get_recipe_count_upper_limits(self) -> RecipeValues:
        """
        Get the upper recipe count limits based on the unlocked recipes

        Returns:
            RecipeAmounts: Limit of recipe count with values either 0 or inf
        """
        recipe_count_upper_limits = RecipeValues(omega=game.RECIPE_NAMES_AUTOMATED)
        for recipe_name in self.unlocked_recipes:
            if not recipe_name in game.RECIPE_NAMES_AUTOMATED:
                continue
            recipe_count_upper_limits[recipe_name] = float('inf')
        return recipe_count_upper_limits

    def get_recipe_group_count_upper_limits(self) -> Dict[Tuple[str], float]:
        """
        Get the upper recipe group count limits based on the available resource
        nodes.

        Returns:
            Dict[Tuple[str], float]: Limit of recipe group count by recipe group
        """
        recipe_group_count_upper_limits = dict()
        for resource_node_name, values in game.RESOURCE_NODES.items():
            amount = self.available_resource_nodes[resource_node_name]
            recipe_group_count_upper_limits[values['extraction_recipes']] = amount
        return recipe_group_count_upper_limits
    
    
    def get_weights_resource_node(self) -> ResourceNodeValues:
        """
        Return the weights of each resource node. This depends on the option
        deduce_weights_resource_node_from_available_resource_nodes.

        Returns:
            ResourceNodeAmounts: Weights of resource nodes
        """
        
        if self.deduce_weights_resource_node_from_available_resource_nodes:
            # fill weights_resource_node with 1/amount for all available resource nodes
            weights_resource_node = ResourceNodeValues()
            for resource_node_name in game.RESOURCE_NODES:
                amount = self.available_resource_nodes[resource_node_name]
                if amount > 0:
                    weights_resource_node[resource_node_name] = 1/amount
        else:
            weights_resource_node = self.weights_resource_node.copy()

        return weights_resource_node

    @staticmethod
    def load_from_file(file_path: str) -> 'StaticProductionLPConfig':
        with open(file_path, 'r') as fp:
            config_data = yaml.safe_load(fp)
        if 'sell_rate_lower_limits' in config_data:
            config_data['sell_rate_lower_limits'] = ItemValues(
                config_data['sell_rate_lower_limits']
            )
        if 'sell_rate_ratio' in config_data:
            config_data['sell_rate_ratio'] = ItemValues(
                config_data['sell_rate_ratio']
            )
        if 'available_resource_nodes' in config_data:
            config_data['available_resource_nodes'] =  ResourceNodeValues(
                config_data['available_resource_nodes']
            )
        if 'base_item_rate' in config_data:
            config_data['base_item_rate'] = ItemValues(
                config_data['base_item_rate']
            )
        if 'weights_resource_node' in config_data:
            config_data['weights_resource_node'] = ResourceNodeValues(
                config_data['weights_resource_node']
            )
        if 'weights_recipe' in config_data:
            config_data['weights_recipe'] = RecipeValues(
                config_data['weights_recipe'],
                omega=game.RECIPE_NAMES_AUTOMATED
            )
        if 'weights_sell_rate' in config_data:
            config_data['weights_sell_rate'] = ItemValues(
                config_data['weights_sell_rate']
            )
        config = StaticProductionLPConfig(**config_data)
        config.check()
        return config
