from argparse import ArgumentParser
import json

import networkx as nx
import matplotlib.pyplot as plt

import game


def check_plan(plan: dict):
    for recipe_name, amount in plan.items():
        if not recipe_name in game.RECIPES:
            raise RuntimeError(f'Unknown recipe {recipe_name}')
        if amount < 0:
            raise RuntimeError(f'Invalid (negative) amount of {recipe_name}')


def main(plan: dict):
    check_plan(plan)

    # create network
    G = nx.DiGraph()
    for recipe_name in plan:
        if plan[recipe_name] == 0:
            continue
        G.add_edges_from([
            (game.get_bare_item_name(item_name), recipe_name)
            for item_name in game.RECIPES[recipe_name]['ingredients']
        ])
        G.add_edges_from([
            (recipe_name, game.get_bare_item_name(item_name))
            for item_name in game.RECIPES[recipe_name]['products']
        ])
    
    # draw network
    resource_recipes = [
        recipe_name
        for recipe_name in plan
        if game.RECIPES[recipe_name]['producedIn'] in game.MINING_FACILITIES
    ]
    manufacturing_nodes = nx.subgraph(G, 
        filter(lambda recipe_name: not recipe_name in resource_recipes, plan.keys()))
    mining_nodes = nx.subgraph(G, 
        filter(lambda recipe_name: recipe_name in resource_recipes, plan.keys()))
    item_nodes = nx.subgraph(G, 
        [node_name for node_name in G.nodes() if not node_name in plan])

    pos = nx.kamada_kawai_layout(G)
    nx.draw_networkx_nodes(G, nodelist=manufacturing_nodes, pos=pos, 
                           node_color='tab:blue')
    nx.draw_networkx_nodes(G, nodelist=mining_nodes, pos=pos, 
                           node_color='tab:purple')
    nx.draw_networkx_nodes(G, nodelist=item_nodes, pos=pos, 
                           node_color='tab:orange')
    nx.draw_networkx_labels(G, pos, font_size=8)
    nx.draw_networkx_edges(G, pos)
    plt.show()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('plan_file', help='JSON dict mapping recipes to amount')
    args = parser.parse_args()

    with open(args.plan_file, 'r') as fp:
        plan = json.load(fp)
    
    main(plan)
