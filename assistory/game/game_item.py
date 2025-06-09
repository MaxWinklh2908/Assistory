import json
import os
from typing import Dict, Iterable, Any

import numpy as np

from .base_types import Flags, Values


with open('data/data.json', 'r') as fp:
    data = json.load(fp)


def define_items() -> dict:
    return {
        item_name:v for item_name,v in data['items'].items()
    }
ITEMS = define_items()

def define_non_sellable_items() -> list:
    return [
        item_name
        for item_name, item_data in ITEMS.items()
        if item_data['sinkPoints'] == 0
        or item_data['liquid']
    ]
ITEM_NAMES_NON_SELLABLE = define_non_sellable_items()

def define_radioactive_items() -> list:
    return [
        item_name
        for item_name, item_data in ITEMS.items()
        if item_data['radioactiveDecay'] > 0
    ]
ITEM_NAMES_RADIOACTIVE = define_radioactive_items()

def define_liquid_items() -> list:
    return [
        item_name
        for item_name, item_data in ITEMS.items()
        if item_data['liquid']
    ]
ITEM_NAMES_LIQUID = define_liquid_items()

def define_items_extraction():
    return list(data['resources'].keys())
ITEM_NAMES_EXTRACTION = define_items_extraction()


class ItemValues(Values):
    def __init__(self,
                 data: Dict[str, Any]=dict(),
                 omega: Iterable[str]=ITEMS,
                 default_value: Any=0):
        super().__init__(data, omega, default_value)

    @classmethod
    def from_array(cls,
                   array: np.ndarray,
                   omega: Iterable[str]=ITEMS
                   ) -> 'ItemValues':
        return cls._from_array(array, omega)

    @classmethod
    def load(cls,
             file_path: os.PathLike,
             omega: Iterable[str]=ITEMS
             ) -> 'ItemValues':
        return super()._load(file_path, omega)


class ItemFlags(Flags):
    def __init__(self,
                 data: Iterable[str]=[],
                 omega: Iterable[str]=ITEMS):
        super().__init__(data, omega)

    @classmethod
    def from_array(cls,
                   array: np.ndarray,
                   omega: Iterable[str]=ITEMS
                   ) -> 'ItemFlags':
        return cls._from_array(array, omega)

    @classmethod
    def load(cls,
             file_path: os.PathLike,
             omega: Iterable[str]=ITEMS
             ) -> 'ItemFlags':
        return super()._load(file_path, omega)
