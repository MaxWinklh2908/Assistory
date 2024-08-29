import csv
import json

import game


def parse_items(file_path: str):
    with open(file_path, 'r') as fp:
        data = fp.readlines()

    # Skip total row and header row
    data = data[2:]

    item_name2class_name = {
        item['name']: item['className']
        for item in game.data['items'].values()
    }

    resources_available = {
        item_name:0 for item_name in game.ITEMS
    }

    for row in csv.reader(data, delimiter=';'):
        item_name = row[0]
        if not item_name in item_name2class_name:
            print('Warning: Skip unknown item:', item_name)
            continue
        balance = float(row[3].replace(',', '.'))
        if balance <= 0:
            continue
        resources_available[item_name2class_name[item_name]] = balance

    return resources_available


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


def read_resource_nodes(file_path: str) -> dict:
    with open(file_path, 'r') as fp:
        data = json.load(fp)

    for node_name in data:
        if node_name not in game.NODES_AVAILABLE:
            print('ERROR Unknown resource node:', node_name)
            result = False
        if data[node_name] < 0:
            raise ValueError('Resource node availability can not be negative')
    return data
