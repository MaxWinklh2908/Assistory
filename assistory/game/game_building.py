import json
import os
from typing import Dict, Iterable, Any

import numpy as np

from .base_types import Flags, Values
from .game_item import ItemValues
from .utils import transform_to_dict


with open('data/data.json', 'r') as fp:
    data = json.load(fp)


def define_buildings():
    facilities = {
        building_name: {
            'power_consumption': vals['metadata']['powerConsumption'],
            'costs': ItemValues(transform_to_dict(vals['costs']))
        }
        for building_name, vals in data['buildings'].items()
    }
    # check negative power of generators
    for building_name, vals in data['buildings'].items():
        power = vals['metadata']['powerConsumption']
        if 'Generator' in building_name and power >= 0:
            raise ValueError(f'There is probably a mistake, as {building_name}'
                             f' has powerConsumption {power} (should be < 0)')
    return facilities
# Mapping of building name to power consumption and costs
# Buildings consume and produce power and items
BUILDINGS = define_buildings()
# Note: over/underclocking would make the problem non-linear


BUILDING_NAMES_EXTRACTION = [
    'Desc_MinerMk1_C',
    'Desc_MinerMk2_C',
    'Desc_MinerMk3_C',
    'Desc_WaterPump_C',
    'Desc_OilPump_C',
    'Desc_FrackingExtractor_C'
]


def is_fracking(building_name: str) -> bool:
    """
    Return whether the building is a fracking building.

    Args:
        building_name (str): Building name

    Returns:
        bool: True if building is fracking. False otherwise.
    """
    return building_name == 'Desc_FrackingExtractor_C'


class BuildingValues(Values):

    def __init__(self,
                 data: Dict[str, Any]=dict(),
                 omega: Iterable[str]=BUILDINGS,
                 default_value: Any=0):
        super().__init__(data, omega, default_value)

    @classmethod
    def from_array(cls,
                   array: np.ndarray,
                   omega: Iterable[str]=BUILDINGS
                   ) -> 'BuildingValues':
        return cls._from_array(array, omega)
    
    @classmethod
    def load(cls, 
             file_path: os.PathLike,
             omega: Iterable[str]=BUILDINGS
             ) -> 'BuildingValues':
        return super()._load(file_path, omega)
    
    def get_costs(self) -> ItemValues:
        """
        Return the items required to build these buildings.

        Returns:
            ItemAmounts: Item costs
        """
        all_costs = ItemValues()
        for building_name, building_amount in self.items():
            costs = BUILDINGS[building_name]['costs'].as_dict_ignoring(0)
            for item_name, item_amount in costs.items():
                all_costs[item_name] += building_amount * item_amount
        return all_costs
    
    def get_power_balance(self) -> float:
        """
        Return the power balance for the buildings

        Returns:
            float: Power balance. Positive means production. Negative means
                consumption.
        """
        return sum([
            amount * (-BUILDINGS[facility_name]['power_consumption'])
            for facility_name, amount in self.items()
        ])


class BuildingFlags(Flags):
    def __init__(self,
                 data: Iterable[str]=[],
                 omega: Iterable[str]=BUILDINGS):
        super().__init__(data, omega)

    @classmethod
    def from_array(cls,
                   array: np.ndarray,
                   omega: Iterable[str]=BUILDINGS
                   ) -> 'BuildingFlags':
        return cls._from_array(array, omega)

    @classmethod
    def load(cls,
             file_path: os.PathLike,
             omega: Iterable[str]=BUILDINGS
             ) -> 'BuildingFlags':
        return super()._load(file_path, omega)
