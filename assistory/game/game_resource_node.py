import json
import os
from typing import Dict, Iterable, Any

import numpy as np

from .utils import get_bare_name
from .base_types import Values


with open('data/data.json', 'r') as fp:
    data = json.load(fp)
with open('data/resource_nodes.json', 'r') as fp:
    resource_node_data = json.load(fp)


# effect of purity on production rate
PURITY_DURATION_FACTORS = {
    'impure': 0.5,
    'normal': 1.0,
    'pure': 2.0,
}


def get_extraction_method_name(fracking: bool) -> str:
    return 'fracking' if fracking else 'non_fracking'


def get_resource_node_name(resource_name: str, fracking: bool) -> str:
    """
    Get the resource node name from the resource name and the fracking method.

    Args:
        resource_name (str): Resource name of the node
        fracking (bool): Whether this node is a fracking node

    Returns:
        str: Name of the resource node type
    """
    method_name = get_extraction_method_name(fracking)
    return f'{resource_name}-{method_name}'


def get_resource_name(resource_node_name: str) -> str:
    """
    Get the resource that can be extracted at the resource node.

    Args:
        resource_node_name (str): Name of the resource node type

    Returns:
        str: Name of the resource node
    """
    return resource_node_name.split('-')[0]


def get_extraction_method(resource_node_name: str) -> bool:
    """
    Get the extraction method of the resource node.

    Args:
        resource_node_name (str): Name of the resource node type

    Returns:
        bool: True if it is a fracking node. False otherwise.
    """
    if resource_node_name.endswith('-' + get_extraction_method_name(True)):
        return True
    elif resource_node_name.endswith('-' + get_extraction_method_name(False)):
        return False
    else:
        raise ValueError('Not a resource node name: ' + resource_node_name)


def define_resource_nodes() -> Dict[str, str]:
    # Previously used hierarchical dict to allow identical format in JSON files (tuple key is forbidden)
    # Now use flat dict via key concatenation which is still compatible with JSON
    resource_nodes = dict()

    # Define resource nodes
    for item_name in [
            'Desc_Stone_C',
            'Desc_OreIron_C',
            'Desc_OreCopper_C',
            'Desc_OreGold_C',
            'Desc_Coal_C',
            'Desc_Sulfur_C',
            'Desc_OreBauxite_C',
            'Desc_RawQuartz_C',
            'Desc_OreUranium_C',
            'Desc_SAM_C',
        ]:
        recipe_tuple = tuple(f'Recipe_MinerMk{level}{get_bare_name(item_name)}_C' for level in (1, 2, 3))
        resource_nodes[get_resource_node_name(item_name, False)] = {
            'resource_name': item_name,
            'method_name': get_extraction_method_name(False),
            'extraction_recipes': recipe_tuple
        }
    resource_nodes[get_resource_node_name('Desc_LiquidOil_C', False)] = {
        'resource_name': 'Desc_LiquidOil_C',
        'method_name': get_extraction_method_name(False),
        'extraction_recipes': ('Recipe_OilPumpLiquidOil_C',)
    }
    resource_nodes[get_resource_node_name('special__power', False)] = {
        'resource_name': 'special__power',
        'method_name': get_extraction_method_name(False),
        'extraction_recipes': ('Recipe_GeneratorGeoThermalPower_C',)
    }

    # Define resource wells
    resource_nodes[get_resource_node_name('Desc_LiquidOil_C', True)] = {
        'resource_name': 'Desc_LiquidOil_C',
        'method_name': get_extraction_method_name(True),
        'extraction_recipes': ('Recipe_FrackingExtractorLiquidOil_C',)
    }
    resource_nodes[get_resource_node_name('Desc_NitrogenGas_C', True)] = {
        'resource_name': 'Desc_NitrogenGas_C',
        'method_name': get_extraction_method_name(True),
        'extraction_recipes': ('Recipe_FrackingExtractorNitrogenGas_C',)
    }
    resource_nodes[get_resource_node_name('Desc_Water_C', True)] = {
        'resource_name': 'Desc_Water_C',
        'method_name': get_extraction_method_name(True),
        'extraction_recipes': ('Recipe_FrackingExtractorWater_C',)
    }
    return resource_nodes
# Mapping from resource node name to its description as a
# mapping {'resource_name':, 'extraction_method':, 'extraction_recipes':}
RESOURCE_NODES = define_resource_nodes()


def define_unique_node_name_to_node_mapping():
    return resource_node_data.copy()
UNIQUE_NODES = define_unique_node_name_to_node_mapping()


def define_node_recipes_available(
        node_names: Iterable[str]
        ) -> Dict[str,float]:
    """
    Build the data structure containing amount of each available resource node

    Args:
        node_names (Iterable[str]): Node names that should be considered

    Returns:
        Dict[str, float]: Mapping from resource node name to amount
    """
    # Initialize with 0
    node_recipes_available = {
        resource_node_name: 0
        for resource_node_name in RESOURCE_NODES
    }
    # Fill with data
    for node_name in node_names:
        values = resource_node_data[node_name]
        amount = PURITY_DURATION_FACTORS[values['purity']]
        resource_node_name = get_resource_node_name(
            values['resource'],
            values['fracking']
        )
        node_recipes_available[resource_node_name] += amount
    return node_recipes_available
# Mapping from resource node name to amount available
NODE_RECIPES_AVAILABLE = define_node_recipes_available(UNIQUE_NODES.keys())


class ResourceNodeValues(Values):
    """
    Resource nodes are identified by a string RESOURCE-METHOD.
    """

    def __init__(self,
                 data: Dict[str, Any]=dict(),
                 omega: Iterable[str]=RESOURCE_NODES,
                 default_value: Any=0):
        super().__init__(data, omega, default_value)

    @classmethod
    def from_array(cls,
                   array: np.ndarray,
                   omega: Iterable[str]=RESOURCE_NODES
                   ) -> 'ResourceNodeValues':
        return cls._from_array(array, omega)

    @classmethod
    def load(cls,
             file_path: os.PathLike,
             omega: Iterable[str]=RESOURCE_NODES
             ) -> 'ResourceNodeValues':
        return super()._load(file_path, omega)
