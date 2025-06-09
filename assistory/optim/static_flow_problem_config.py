from dataclasses import dataclass, field
from typing import Dict, Tuple

from assistory.game import ItemValues, RecipeValues
from assistory import game


def get_default_recipes_all(x) -> RecipeValues:
    out = RecipeValues(omega=game.RECIPE_NAMES_AUTOMATED)
    out.set_values(x)
    return out


def get_default_items_all(x) -> ItemValues:
    out = ItemValues()
    out.set_values(x)
    return out


def test_not_negative(data: dict, data_name: str):
    invalid_data_subset = {
        key: value
        for key, value in data.items()
        if value < 0
    }
    if invalid_data_subset:
        raise ValueError(
            f'{invalid_data_subset}\n{data_name} can not be negative.'
        )


def test_upper_not_under_lower(
        upper_data: dict,
        upper_name: str,
        lower_data: dict,
        lower_name: str
    ):
    shared_keys = set(upper_data).intersection(set(lower_data))
    for key in shared_keys:
        if upper_data[key] < lower_data[key]:
            raise ValueError(
                f'Values of {upper_name} can not be smaller than {lower_name}'
            )


def test_at_least_one_greater_zero(data: dict, data_name: str):
    filtered_data = {
        item_name: weight
        for item_name, weight in data.items()
        if weight > 0
    }
    if not filtered_data:
        raise ValueError(f'At least one entry of {data_name} must be greater 0')


# TODO: document
@dataclass
class StaticFlowLPConfig:

    ############################## parameters ################################

    # Items from existing or manual production that are added to the item rate
    # balance. Can be negative to express a need of an existing production. 
    # Defaults to all 0.
    base_item_rate: ItemValues = field(
        default_factory=lambda: ItemValues()
    )

    ############################### contraints ###############################

    # Nonnegative maximal value of the item rate balance. Items with value inf
    # are ignored. Defaults to all inf.
    item_rate_balance_upper_limits: ItemValues = field(
        default_factory=lambda: get_default_items_all(float('inf'))
    )
    
    # Nonnegative minimal value of the item rate balance. Defaults to all 0.
    item_rate_balance_lower_limits: ItemValues = field(
        default_factory=lambda: ItemValues()
    )

    # Ratio (> 0) of the item rate balance by item name. Items with value 0
    # are ignored. Defaults to all 0.
    item_rate_balance_ratio: ItemValues = field(
        default_factory=lambda: ItemValues()
    )

    # Nonnegative maximal value of the recipe count. Defaults to all inf.
    recipe_count_upper_limits: RecipeValues = field(
        default_factory=lambda: get_default_recipes_all(float('inf'))
    )
    
    # Nonnegative minimal value of the recipe count. Defaults to all 0.
    recipe_count_lower_limits: RecipeValues = field(
        default_factory=lambda: get_default_recipes_all(0)
    )

    # Nonnegative maximal value of the recipe group count. Undefined items
    # are ignored. Defaults to {}.
    recipe_group_count_upper_limits: Dict[Tuple[str], float] = field(
        default_factory=dict
    )
    
    # Nonnegative minimal value of the recipe group count. Undefined items
    # default to 0. Defaults to {}.
    recipe_group_count_lower_limits: Dict[Tuple[str], float] = field(
        default_factory=dict
    ) 
    
    ############################### objective ################################
    
    # Nonnegative recipe weights. Recipes with weight 0 are ignored.
    # Defaults to all 1.
    recipe_weights: RecipeValues = field(
        default_factory=lambda: get_default_recipes_all(1)
    )

    # Minimize the number of recipes according to the recipe weights
    minimize_recipe_count: bool = False
    
    # Maximize the number of recipes according to the recipe weights
    maximize_recipe_count: bool = False
    
    # Nonnegative item weights. Items with weight 0 are ignored.
    # Defaults to all 1.
    item_weights: ItemValues = field(
        default_factory=lambda: get_default_items_all(1)
    )
    
    # Minimize the item rate balance according to the item weights
    minimize_item_rate_balance: bool = False
    
    # Maximize the item rate balance according to the item weights
    maximize_item_rate_balance: bool = False

    def check(self):
        """
        Check if the parameters represent a valid configuration. Raise an
        exception otherwise.
        """        

        test_not_negative(
            self.item_rate_balance_upper_limits,
            'Upper limit of item rate balance',
        )
        test_not_negative(
            self.item_rate_balance_lower_limits,
            'Lower limit of item rate balance',
        )
        test_upper_not_under_lower(
            self.item_rate_balance_upper_limits,
            'Upper limit of item rate balance',
            self.item_rate_balance_lower_limits,
            'Lower limit of item rate balance',
        )

        test_not_negative(
            self.item_rate_balance_ratio,
            'Item rate balance ratio'
        )

        test_not_negative(
            self.recipe_count_upper_limits,
            'Upper limit of recipe count',
        )
        test_not_negative(
            self.recipe_count_lower_limits,
            'Lower limit of recipe count',
        )
        test_upper_not_under_lower(
            self.recipe_count_upper_limits,
            'Upper limit of recipe count',
            self.recipe_count_lower_limits,
            'Lower limit of recipe count',
        )
        
        test_not_negative(
            self.recipe_group_count_upper_limits,
            'Upper limit of recipe group count'
        )
        test_not_negative(
            self.recipe_group_count_lower_limits,
            'Lower limit of recipe group count'
        )
        test_upper_not_under_lower(
            self.recipe_group_count_upper_limits,
            'Upper limit of recipe group count',
            self.recipe_group_count_lower_limits,
            'Lower limit of recipe group count',
        )

        # selection of objective
        objectives = (
            self.minimize_recipe_count,
            self.maximize_recipe_count,
            self.minimize_item_rate_balance,
            self.maximize_item_rate_balance,
        )
        if sum(objectives) > 1:
            raise ValueError('Define only one objective at a time')
        elif sum(objectives) == 0:
            raise ValueError('Define at least one objective')
        
        # objective weights
        if self.maximize_item_rate_balance or self.minimize_item_rate_balance:
            test_at_least_one_greater_zero(
                self.item_weights,
                'Item weights'
            )
        if self.maximize_recipe_count or self.minimize_recipe_count:
            test_at_least_one_greater_zero(
                self.recipe_weights,
                'Recipe weights'
            )
        test_not_negative(
            self.item_weights,
            'Item weights'
        )
        test_not_negative(
            self.recipe_weights,
            'Recipe weights'
        )

        # boundedness check (only necessary not sufficient)
        if ((self.maximize_recipe_count or self.maximize_item_rate_balance)
            and not any((
            self.item_rate_balance_upper_limits, # limit products
            self.item_rate_balance_lower_limits, # limit ingredients given base rate
            self.recipe_count_upper_limits,
            self.recipe_group_count_upper_limits,
        ))):
            raise ValueError('Define limits on recipe count or item rate balance')
