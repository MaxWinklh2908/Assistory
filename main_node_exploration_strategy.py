import csv

import assistory.optim.sink_point_optim as sink_point_optim
from assistory.game import game

RESOURCE_NODES = {    
        'Desc_Stone_C': 480,
        'Desc_OreIron_C': 480,
        'Desc_OreCopper_C': 480,
        'Desc_OreGold_C': 480,
        'Desc_Coal_C': 480,
        'Desc_LiquidOil_C': 240,
        'Desc_Sulfur_C': 480,
        'Desc_OreBauxite_C': 480,
        'Desc_RawQuartz_C': 480,
        'Desc_OreUranium_C': 240,
    }


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


def find_best_new_resource_node(recipes: dict, resources_available: dict):

    def calculate_optimal_sink_points(resources_available: dict):
        problem = sink_point_optim.SatisfactoryLP(recipes, resources_available)
        problem.optimize()
        return problem.solver.Objective().Value()
    
    base_score = calculate_optimal_sink_points(resources_available)
    print('Base score:', round(base_score))
    print()

    best_resource = None
    best_score = base_score
    for item_name, amount in RESOURCE_NODES.items():
        resources_extended = resources_available.copy()
        resources_extended[item_name] += amount
        score = calculate_optimal_sink_points(resources_extended)
        print(item_name, '-', round(score - base_score))
        if score > best_score:
            best_score = score
            best_resource = item_name

    print()
    if best_resource == None:
        print('No improvement possible')
    else:
        print('Best next resource:', best_resource)
        print(f'Improvement by {round(best_score - base_score)} ({base_score} -> {best_score})')



if __name__ == '__main__':
    resources_available = dict()
    # custom
    # resources_available['Desc_OreIron_C'] = 120
    # resources_available['Desc_OreCopper_C'] = 120
    
    # # current overhead
    resources_available = parse_items('data/Autonation4.0.csv')
    resources_available = {
        item_name: amount
        for item_name, amount in resources_available.items()
        if item_name in game.ITEMS
    }
    resources_available.pop('Desc_Water_C')

    recipes=game.RECIPES
    find_best_new_resource_node(recipes, resources_available)
