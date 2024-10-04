from argparse import ArgumentParser
import math

import networkx as nx
import matplotlib.pyplot as plt

import game
import utils


EXCLUDED_ITEMS = [
]
EXCLUDED_RECIPES = [
    # 'Recipe_SpikedRebar_C',
    # 'Recipe_FilterHazmat_C',
    # 'Recipe_Alternate_AutomatedMiner_C',
    # 'Recipe_Cartridge_C',
    # 'Recipe_FilterGasMask_C',
    # 'Recipe_Alternate_Nobelisk_1_C',
    # 'Recipe_Alternate_Gunpowder_1_C',
    # 'Recipe_Alternate_Beacon_1_C'
]
ONLY_ITEMS = [
    # 'Desc_PressureConversionCube_C'
]


def check_plan(recipes: dict, items_sold: dict):
    for recipe_name, amount in recipes.items():
        if not recipe_name in game.RECIPES:
            raise RuntimeError(f'Unknown recipe {recipe_name}')
        if amount < 0:
            raise RuntimeError(f'Invalid (negative) amount of {recipe_name}')
    for item_name in items_sold:
        if not item_name in game.ITEMS:
            print('ERROR Unknown item:', item_name)
            result = False
        if items_sold[item_name] < 0:
            raise ValueError('Resource node availability can not be negative')


def calc_flow(rate: float, recipe: dict, amount: int) -> float:
    return rate * amount * 60/recipe['time']


def main(recipes: dict, items_sold: dict, items_available: dict):
    check_plan(recipes, items_sold)

    item_amount = items_available.copy()

    # create network
    G = nx.DiGraph()
    resource_node_names = []
    manufacturing_node_names = []
    i = 0
    for recipe_name, rate in recipes.items():
        if recipe_name in EXCLUDED_RECIPES:
            continue
        if recipes[recipe_name] == 0:
            continue
        if recipe_name == 'Recipe_WaterExtractorWater_C':
            continue
        recipe = game.RECIPES[recipe_name]
        
        if (
            ONLY_ITEMS
            and not any(item_name in ONLY_ITEMS for item_name in recipe['ingredients'])
            and not any(item_name in ONLY_ITEMS for item_name in recipe['products'])):
            continue

        
        recipe_node_name = f'{recipe_name}\n{round(rate, 2)}'
        
        # ingredients
        for item_name, amount in recipe['ingredients'].items():
            if item_name in EXCLUDED_ITEMS:
                continue
            flow = calc_flow(rate, recipe, amount)
            if item_name == 'Desc_Water_C':
                G.add_edge(
                    f'Water_{i}',
                    recipe_node_name,
                    flow=round(flow, 4),
                    weight=max(1, math.log(flow))
                )
                i += 1
                continue
            G.add_edge(
                game.ITEMS[item_name]['name'],
                recipe_node_name,
                flow=round(flow, 4),
                weight=max(1, math.log(flow))
            )
        
        # products
        for item_name, amount in recipe['products'].items():
            if item_name in EXCLUDED_ITEMS:
                continue
            flow = calc_flow(rate, recipe, amount)
            item_amount[item_name] = item_amount.get(item_name, 0) + flow
            if item_name == 'Desc_Water_C':
                G.add_edge(
                    recipe_node_name,
                    f'Water_{i}',
                    flow=round(flow, 4),
                    weight=max(1, math.log(flow))
                )
                i += 1
                continue
            G.add_edge(
                recipe_node_name,
                game.ITEMS[item_name]['name'],
                flow=round(flow, 4),
                weight=max(1, math.log(flow))
            )

        if game.RECIPES[recipe_name]['producedIn'] in game.MINING_FACILITIES:
            resource_node_names.append(recipe_node_name)
        else:
            manufacturing_node_names.append(recipe_node_name)

    available_item_node_names = []
    for item_name, amount in items_available.items():
        if amount == 0:
            continue
        if not item_name in ONLY_ITEMS or item_name in EXCLUDED_ITEMS:
            continue
        item_node_name = game.ITEMS[item_name]['name'] + '\n(available)'
        G.add_edge(
            item_node_name,
            game.ITEMS[item_name]['name'],
            flow=round(amount, 4),
            weight=max(1, math.log(amount))
        )
        available_item_node_names.append(item_node_name)

    sold_item_node_names = []
    for item_name, amount in items_sold.items():
        if amount == 0:
            continue
        if not item_name in ONLY_ITEMS or item_name in EXCLUDED_ITEMS:
            continue
        sold_item_node_name = game.ITEMS[item_name]['name']  + '\n(sell)'
        G.add_edge(
            game.ITEMS[item_name]['name'],
            sold_item_node_name,
            flow=round(amount, 4)
        )
        sold_item_node_names.append(sold_item_node_name)
    
    # draw network
    manufacturing_nodes = nx.subgraph(G,
        filter(lambda name: name in manufacturing_node_names,
               G.nodes()))
    mining_nodes = nx.subgraph(G,
        filter(lambda name: name in resource_node_names,
               G.nodes()))
    sold_item_nodes = nx.subgraph(G,
        filter(lambda name: name in sold_item_node_names,
               G.nodes()))
    available_item_nodes = nx.subgraph(G,
        filter(lambda name: name in available_item_node_names,
               G.nodes()))
    recipe_node_names = (
        manufacturing_node_names
        + resource_node_names
        + sold_item_node_names
        + available_item_node_names
    )
    item_nodes = nx.subgraph(G,
        [node_name for node_name in G.nodes()
         if not node_name in recipe_node_names])
    labels = {
        (u, v): str(data['flow'])
        for (u, v, data) in G.edges.data()
    }

    print('Items in cycle:')
    for item_name, amount in sorted(item_amount.items()):
        print(item_name, amount)

    # pos = nx.kamada_kawai_layout(G)
    # TODO: Use clusters to plot manual assingment of recipes to sites
    pos = nx.spring_layout(G, iterations=50, weight='weight')
    # pos = nx.shell_layout(G)
    nx.draw_networkx_nodes(G, nodelist=manufacturing_nodes, pos=pos, 
                           node_color='tab:blue', label='Manufacturing')
    nx.draw_networkx_nodes(G, nodelist=mining_nodes, pos=pos, 
                           node_color='tab:purple', label='Mining')
    nx.draw_networkx_nodes(G, nodelist=sold_item_nodes, pos=pos, 
                           node_color='tab:red', label='Sold Item')
    nx.draw_networkx_nodes(G, nodelist=available_item_nodes, pos=pos, 
                           node_color='tab:green', label='Available Item')
    nx.draw_networkx_nodes(G, nodelist=item_nodes, pos=pos, 
                           node_color='tab:orange', label='Item')
    nx.draw_networkx_labels(G, pos, font_size=8)
    nx.draw_networkx_edges(G, pos)
    nx.draw_networkx_edge_labels(G, pos, labels, font_size=6)
    plt.legend()
    plt.tight_layout()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('plan_file', help='JSON dict mapping recipes to amount')
    args = parser.parse_args()

    recipes, items_sold, items_available = utils.read_result(args.plan_file)
    
    main(recipes, items_sold, items_available)
    plt.title(args.plan_file)
    plt.show()
