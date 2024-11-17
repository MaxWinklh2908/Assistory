import json
from typing import Iterable, List, Set


def write_result(recipes: dict, items_sold: dict, available_items: dict,
                 file_path: str):
    data = {
        'recipes': recipes,
        'items_sold': items_sold,
        'items_available': {k:v for k,v in available_items.items() if v > 0 },
    }
    with open(file_path, 'w') as fp:
        json.dump(data, fp)


def read_result(file_path) -> tuple:
    with open(file_path, 'r') as fp:
        data = json.load(fp)
    return data['recipes'], data['items_sold'], data['items_available']


def read_resource_nodes(file_path: str, node_recipes: Set[str]) -> dict:
    with open(file_path, 'r') as fp:
        data = json.load(fp)

    for node_name in data:
        if not node_name in node_recipes:
            print('ERROR Unknown resource node:', node_name)
            result = False
        if data[node_name] < 0:
            raise ValueError('Resource node availability can not be negative')
    return data


def transform_to_dict(items: List[dict]) -> dict:
    """Transform a list of item amount dicts to a dict mapping the item name
    to the amount.

    Args:
        items (List[dict]): list of dicts with "item" and "amount" keys

    Returns:
        dict: mapping from item to amount
    """
    return {
        d['item']: d['amount']
        for d in items
    }


def vectorize(name2count: dict, base_names: Iterable) -> list:
    for item_name in name2count:
        if not item_name in base_names:
            raise ValueError('Unknown item: ', item_name)
    return [name2count.get(name,0) for name in base_names]


def unvectorize(counts: Iterable, base_names: Iterable) -> dict:
    return {
        name: amount
        for amount, name in zip(counts, base_names)
        if amount != 0
    }
