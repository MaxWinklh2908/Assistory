from typing import Dict, Tuple

import numpy as np

from assistory import game
from assistory.game import ItemValues, RecipeValues, ResourceNodeValues
from assistory.game import ItemFlags, RecipeFlags
from assistory.optim.static_flow_problem import StaticFlowLP, ReturnCode
from assistory.optim.static_flow_problem_config import StaticFlowLPConfig
from assistory.optim.static_production_problem import StaticProductionLP
from assistory.optim.static_production_problem_config import StaticProductionLPConfig


def get_producable_items(
        base_item_rate: ItemValues=ItemValues(),
        recipe_count_upper_limits: RecipeValues=RecipeValues(omega=game.RECIPE_NAMES_AUTOMATED),
        recipe_group_count_upper_limits: Dict[Tuple[str], float]=dict(),
    ) -> ItemFlags:
    """Return all items that can theoretically be produced with the given
    flow problem configuration. The item balance is enforced to be nonnegative.
    Items from the base item rate are not automatically producable.

    Args:
        base_item_rate (ItemAmounts, optional): Nonnegative amounts of freely
            availabel items. Defaults to all 0.
        recipe_count_upper_limits (RecipeAmounts, optional): Equivalent to
            StaticFlowLPConfig.recipe_count_upper_limits. Defaults to all 0.
        recipe_group_count_upper_limits (Dict[Tuple[str], float], optional): Equivalent
            to StaticFlowLPConfig.recipe_group_count_upper_limits. Defaults to {}.

    Returns:
        ItemFlags: Item names of producable items
    """
    if min(base_item_rate.values()) < 0:
        raise ValueError('Base item rate must not be negative')
    producable_item_names = ItemFlags()
    for item_name in game.ITEMS:
        producable_lp_config = StaticFlowLPConfig(
            base_item_rate=base_item_rate,
            recipe_count_upper_limits=recipe_count_upper_limits,
            recipe_group_count_upper_limits=recipe_group_count_upper_limits,
            # overwrite the objective
            maximize_item_rate_balance=True,
            item_weights={item_name: 1.0},
        )
        lp = StaticFlowLP(producable_lp_config)
        code = lp.optimize()
        if code != ReturnCode.OPTIMAL:
            raise RuntimeError(f'Unexpected status: {code}')
        if lp.objective_value - base_item_rate[item_name] > 1e-7:
            producable_item_names.add(item_name)
    return producable_item_names


def is_power_producable(
        available_resource_nodes: ResourceNodeValues=ResourceNodeValues(game.NODE_RECIPES_AVAILABLE),
        unlocked_recipes: RecipeFlags=RecipeFlags(game.RECIPE_NAMES_AUTOMATED, omega=game.RECIPE_NAMES_AUTOMATED),
        base_item_rate: ItemValues=ItemValues()
    ) -> Tuple[bool]:
    """Return wether prower is available given unlocked recipes, existing
    items rate and available resource nodes.

    Args:
        available_resource_nodes (ResourceNodeAmounts, optional):
            Available resource nodes by resource node name.
            Defaults to game.NODE_RECIPES_AVAILABLE.
        unlocked_recipes (RecipeFlags): Names of available automated recipes.
            Defaults to all automated recipes.
        base_item_rate (ItemAmounts, optional): Available existing item
            production. Defaults to all 0.

    Returns:
        Tuple[bool]: Two bool values:
            1. Wether automatic power production chain is unlocked
            2. Whether limited resources are the cause for no power being
            available. Is False if first value is False
    """
    if min(base_item_rate.values()) < 0:
        raise ValueError('Base item rate must not be negative')
    production_lp_config = StaticProductionLPConfig(
        unlocked_recipes=unlocked_recipes,
        base_item_rate=base_item_rate,
        base_power=-10,
        maximize_sink_points=True,
    )
    lp = StaticProductionLP(production_lp_config)
    code = lp.optimize()
    producation_chain_incomplete = code != ReturnCode.OPTIMAL
    
    production_lp_config.available_resource_nodes=available_resource_nodes
    lp = StaticProductionLP(production_lp_config)
    code = lp.optimize()
    resources_missing = not producation_chain_incomplete and code != ReturnCode.OPTIMAL
    
    return producation_chain_incomplete, resources_missing


def get_feasibility_hints(production_lp_config: StaticProductionLPConfig):
    """
    Get hints how to make an infeasible problem feasible by analyzing the
    problem configuration
    """
    # Limits recipe count
    ones_recipe = RecipeValues(omega=game.RECIPE_NAMES_AUTOMATED)
    ones_recipe.set_values(1)
    recipe_count_upper_limits = RecipeValues.from_array(
        np.minimum(
            ones_recipe.as_array(),
            production_lp_config.get_recipe_count_upper_limits().as_array()
        ),
        omega=game.RECIPE_NAMES_AUTOMATED
    )

    base_item_rate_producing = ItemValues({
        item_name: rate
        for item_name, rate in production_lp_config.base_item_rate.items()
        if rate >= 0
    })
    producable_items = get_producable_items(
        base_item_rate_producing,
        recipe_count_upper_limits,
        production_lp_config.get_recipe_group_count_upper_limits()
    )

    for item_name, ratio in production_lp_config.sell_rate_ratio.items():
        if ratio != 0 and not item_name in producable_items:
            print(f'CRITICAL: {item_name} is not producable. Ratio can not be specified')

    for item_name, value in production_lp_config.sell_rate_lower_limits.items():
        if value > 0 and not item_name in producable_items:
            print(f'{item_name} is not producable. Minimum sell rate can not be specified')

    if production_lp_config.maximize_sell_rate:
        if not any({
            weight > 0 and item_name in producable_items
            for item_name, weight in production_lp_config.weights_sell_rate.items()
        }):
            print(
                'WARNING: None of the weighted items is not producable. '
                'Maximizing sell rate is trivially 0'
            )
    for item_name, rate in production_lp_config.base_item_rate.items():
        if rate < 0:
            print(f'WARNING: Base item rate of {item_name} is negative.'
                  ' The optimization maybe can not neutralize this need.')

    producation_chain_incomplete, resources_missing = is_power_producable(
        production_lp_config.available_resource_nodes,
        production_lp_config.unlocked_recipes,
        base_item_rate_producing
    )

    if producation_chain_incomplete:
        print('Missing recipes in production chain to produce power')

    if resources_missing:
        print('Missing resources to produce power')
