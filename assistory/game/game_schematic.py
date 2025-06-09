import json
import os
from typing import Iterable

import numpy as np

from .base_types import Flags
from .game_item import ItemValues
from .game_recipe import RECIPES, RecipeFlags
from .game_building import BUILDINGS, BuildingFlags
from .utils import transform_to_dict


with open('data/data.json', 'r') as fp:
    data = json.load(fp)


def define_schematics():
    schematics = dict()
    for schematic_name, v in data['schematics'].items():
        cost = transform_to_dict(v['cost'])
        unlocked_recipes = set(v['unlock']['recipes'])
        unlocked_buildings = set(v['unlock']['buildings'])
        schematics[schematic_name] = {
            'name': v['name'],
            'costs': ItemValues(cost),
            'unlock_recipes': RecipeFlags(unlocked_recipes),
            'unlock_buildings': BuildingFlags(unlocked_buildings)
        }
    return schematics
SCHEMATICS = define_schematics()


# helper structure to find schematics
def define_building_recipe_to_schematic_mappings():
    unlock_recipe_by = { recipe_name: set() for recipe_name in RECIPES}
    unlock_building_by = { building_name: set() for building_name in BUILDINGS}
    for schematics_name, data in SCHEMATICS.items():
        for recipe_name in data['unlock_recipes']:
            unlock_recipe_by[recipe_name].add(schematics_name)
        for building_name in data['unlock_buildings']:
            unlock_building_by[building_name].add(schematics_name)
    
    return unlock_recipe_by, unlock_building_by
unlock_recipe_by, unlock_building_by = define_building_recipe_to_schematic_mappings()


class SchematicFlags(Flags):
    def __init__(self,
                 data: Iterable[str]=[],
                 omega: Iterable[str]=SCHEMATICS):
        super().__init__(data, omega)

    @classmethod
    def from_array(cls,
                   array: np.ndarray,
                   omega: Iterable[str]=SCHEMATICS
                   ) -> 'SchematicFlags':
        return cls._from_array(array, omega)

    @classmethod
    def load(cls,
             file_path: os.PathLike,
             omega: Iterable[str]=SCHEMATICS
             ) -> 'SchematicFlags':
        return super()._load(file_path, omega)
    
    def get_buildings_unlocked(self) -> BuildingFlags:
        """
        Get all buildings that have been unlocked by these schematics

        Returns:
            BuildingFlags: Building names
        """
        buildings_unlocked = BuildingFlags()
        for schematics_name in self:
            schematic = SCHEMATICS[schematics_name]
            buildings_unlocked |= schematic['unlock_buildings']
        return buildings_unlocked

    def get_recipes_unlocked(self) -> RecipeFlags:
        """
        Get all recipes that have been unlocked by these schematics

        Returns:
            RecipeFlags: Recipe names
        """
        buildings_unlocked = self.get_buildings_unlocked()
        recipes_unlocked = RecipeFlags()
        for schematics_name in self:
            schematic = SCHEMATICS[schematics_name]
            recipes_unlocked_schmatic = schematic['unlock_recipes']
            recipes_unlocked |= recipes_unlocked_schmatic
        recipes_unlocked = RecipeFlags({
            recipe_name for
            recipe_name in recipes_unlocked
            if all(building_name in buildings_unlocked
                   for building_name in RECIPES[recipe_name]['producedIn'])
        })
        return recipes_unlocked
