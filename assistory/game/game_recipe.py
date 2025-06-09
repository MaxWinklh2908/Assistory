import json
import os
from typing import Dict, Iterable, Any, Optional

import numpy as np

from .base_types import Flags, Values
from .game_item import ITEMS, ITEM_NAMES_EXTRACTION, ItemValues, ItemFlags
from .game_building import BUILDINGS, is_fracking, BuildingValues, BuildingFlags
from .game_resource_node import get_resource_node_name, ResourceNodeValues
from .utils import transform_to_dict


# Handcrafted cycle is faster than building recipe by this factor
# Note: Additionally, cycle is affected by recipe['manualTimeMultiplier']
HANDCRAFT_CYCLE_MULTIPLIER = 0.125


with open('data/data.json', 'r') as fp:
    data = json.load(fp)


# recipes in buildings
def define_recipes():
    recipes = dict()

    for recipe_name, v in data['recipes'].items():
        if len(v['producedIn']) > 1:
            raise ValueError(f'Expect at most one production facility for {recipe_name}. '
                             f'Got: {v["producedIn"]}.')
        if not all(building_name in BUILDINGS for building_name in v['producedIn']):
            raise ValueError('Unknown buildings:', v['producedIn'])
        if v['inMachine'] and len(v['producedIn']) != 1:
            raise ValueError('Machine recipes must define one producedIn building')
        if not v['inMachine'] and not v['inWorkshop'] and not v['inHand']:
            raise ValueError('Recipes must be either machine or handcraft')

        ingredients = transform_to_dict(v['ingredients'])
        products = transform_to_dict(v['products'])

        recipes[recipe_name] = {
            'name': v['name'],
            'ingredients': ItemValues(ingredients),
            'products': ItemValues(products),
            'producedIn': set(v['producedIn']),
            'time': float(v['time']),
            'manualTimeMultiplier': float(v['manualTimeMultiplier'])
        }

    return recipes
# recipies define ingredients, products, production facility and production time
RECIPES = define_recipes()


def get_extracted_resource_name(recipe_name: str) -> Optional[str]:
    """
    Return the resource name that is extracted by the recipe if possible.

    Args:
        recipe_name (str): Name of the recipe

    Returns:
        Optional[str]: Resource name if recipe extracts a resource. Otherwise None.
    """
    recipe = RECIPES[recipe_name]
    extracted_items = recipe['products'].as_dict_ignoring(ignore_value=0)
    if len(extracted_items) != 1:
        return None
    resource_name = list(extracted_items)[0]
    if resource_name in ITEM_NAMES_EXTRACTION:
        return resource_name
    else:
        return None


# Alternate recipes are unlocked by research
RECIPE_NAMES_ALTERNATE = {
    recipe_name
    for recipe_name in RECIPES
    if data['recipes'][recipe_name]['alternate']
}


# Automated recipes have a producedIn building
RECIPE_NAMES_AUTOMATED = {
    recipe_name
    for recipe_name in RECIPES
    if data['recipes'][recipe_name]['inMachine']
}


# Handcraft recipes can be executed by hand (and often by a machine)
RECIPE_NAMES_HANDCRAFTED = {
    recipe_name
    for recipe_name in RECIPES
    if (data['recipes'][recipe_name]['inWorkshop'] or
        data['recipes'][recipe_name]['inHand'])
}


# helper structure to find recipes
def define_item_to_recipe_mappings():
    consumed_by = { item_name: set() for item_name in ITEMS}
    produced_by = { item_name: set() for item_name in ITEMS}
    for recipe_name in RECIPES:
        for item_name in RECIPES[recipe_name]['ingredients'].as_dict_ignoring(0):
            consumed_by[item_name].add(recipe_name)
        for item_name in RECIPES[recipe_name]['products'].as_dict_ignoring(0):
            produced_by[item_name].add(recipe_name)
    return consumed_by, produced_by
consumed_by, produced_by = define_item_to_recipe_mappings()

def define_building_to_recipe_mapping():
    building_name2recipe_name = {building_name: [] for building_name in BUILDINGS}
    for recipe_name in RECIPES:
        for building_name in RECIPES[recipe_name]['producedIn']:
            building_name2recipe_name[building_name].append(recipe_name)
    return building_name2recipe_name
produced_in = define_building_to_recipe_mapping()


class RecipeValues(Values):

    def __init__(self,
                 data: Dict[str, Any]=dict(),
                 omega: Iterable[str]=RECIPES,
                 default_value: Any=0):
        super().__init__(data, omega, default_value)

    @classmethod
    def from_array(cls,
                   array: np.ndarray,
                   omega: Iterable[str]=RECIPES
                   ) -> 'RecipeValues':
        return cls._from_array(array, omega)
    
    @classmethod
    def load(cls,
             file_path: os.PathLike,
             omega: Iterable[str]=RECIPES
             ) -> 'RecipeValues':
        return super()._load(file_path, omega)
    
    def get_item_rate_balance(self) -> ItemValues:
        """
        Return the overall balance of the item rate by summing up ingredients
        and products production of these recipes.

        Returns:
            ItemAmounts: Item rate balance. Elements can be negative.
        """
        item_rates = ItemValues()
        for recipe_name, recipe_amount in self.items():
            recipe = RECIPES[recipe_name]
            cylce_time = recipe['time'] / 60 # in min
            factor = recipe_amount / cylce_time
            # TODO: removing zero filtering is too slow because of large sum result
            ingredients = recipe['ingredients'].as_dict_ignoring(0)
            for item_name, item_amount in ingredients.items():
                item_rates[item_name] -= item_amount * factor
            products = recipe['products'].as_dict_ignoring(0)
            for item_name, item_amount in products.items():
                item_rates[item_name] += item_amount * factor
        return item_rates
    
    def get_item_rate_balance_handcraft(self) -> ItemValues:
        """
        Return the overall handcrafting balance of the item rate by summing up
        ingredients and products production of these recipes.

        Returns:
            ItemAmounts: Item rate balance. Elements can be negative.
        """
        item_rates = ItemValues()
        for recipe_name, recipe_amount in self.items():
            if not recipe_name in RECIPE_NAMES_HANDCRAFTED:
                if recipe_amount > 0:
                    raise ValueError(f'Recipe {recipe_name} is not allowed for handcrafting')
                else:
                    continue
            recipe = RECIPES[recipe_name]
            cylce_time_automated = recipe['time'] / 60 # in min
            cycle_time_multiplier = HANDCRAFT_CYCLE_MULTIPLIER * recipe['manualTimeMultiplier']
            cylce_time = cylce_time_automated * cycle_time_multiplier
            factor = recipe_amount / cylce_time
            ingredients = recipe['ingredients'].as_dict_ignoring(0)
            for item_name, item_amount in ingredients.items():
                item_rates[item_name] -= item_amount * factor
            products = recipe['products'].as_dict_ignoring(0)
            for item_name, item_amount in products.items():
                item_rates[item_name] += item_amount * factor
        return item_rates

    def get_buildings(self) -> BuildingValues:
        """
        Return the amount of buildings in which these recipes are active. Note
        that the amount of buildings is fractional while in reality this is not
        possible: Two times 50% of recipes produced in the same building sum up
        to a building amount of 1.

        Returns:
            BuildingAmounts: Amount of buildings
        """
        all_buildings = BuildingValues()
        for recipe_name, amount in self.items():
            # either zero or one item
            for building_name in RECIPES[recipe_name]['producedIn']:
                all_buildings[building_name] += amount
        return all_buildings

    def get_resource_nodes_used(self) -> ResourceNodeValues:
        """
        Return the amount of resource nodes that is required for these recipes.

        Returns:
            ResourceNodeValues: Amount of resource nodes
        """
        node_amounts = ResourceNodeValues()
        for recipe_name in self.as_dict_ignoring(ignore_value=0):
            resource_name = get_extracted_resource_name(recipe_name)
            if resource_name is None or resource_name == 'Desc_Water_C':
                continue
            recipe = RECIPES[recipe_name]
            if recipe_name in RECIPE_NAMES_HANDCRAFTED:
                continue # handcrafting is not blocking resource node
            building_name = list(recipe['producedIn'])[0]
            fracking = is_fracking(building_name)
            resource_node_name = get_resource_node_name(resource_name, fracking)
            node_amounts[resource_node_name] += self[recipe_name]
        return node_amounts


class RecipeFlags(Flags):
    def __init__(self,
                 data: Iterable[str]=[],
                 omega: Iterable[str]=RECIPES):
        super().__init__(data, omega)

    @classmethod
    def from_array(cls,
                   array: np.ndarray,
                   omega: Iterable[str]=RECIPES
                   ) -> 'RecipeFlags':
        return cls._from_array(array, omega)

    @classmethod
    def load(cls,
             file_path: os.PathLike,
             omega: Iterable[str]=RECIPES
             ) -> 'RecipeFlags':
        return super()._load(file_path, omega)

    def get_items_produced(self) -> ItemFlags:
        """
        Get all items that are produced by at least one of the recipes.

        Returns:
            ItemFlags: Item names
        """
        return ItemFlags({
            item_name
            for item_name in ITEMS
            if produced_by[item_name] & self
        })

    def get_items_consumed(self) -> ItemFlags:
        """
        Get all items that are consumed by at least one of the recipes.

        Returns:
            ItemFlags: Item names
        """
        return ItemFlags({
            item_name
            for item_name in ITEMS
            if consumed_by[item_name] & self
        })

    def get_buildings_involved(self) -> BuildingFlags:
        building_names = set()
        for recipe_name in self:
            building_names |= RECIPES[recipe_name]['producedIn']
        return BuildingFlags(building_names)
