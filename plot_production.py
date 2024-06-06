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
    resource_node_names = []
    manufacturing_node_names = []
    for recipe_name, rate in plan.items():
        if plan[recipe_name] == 0:
            continue
        recipe = game.RECIPES[recipe_name]
        recipe_node_name = f'{recipe_name}\n{round(rate, 2)}'
        for item_name, amount in recipe['ingredients'].items():
            G.add_edge(
                game.get_bare_item_name(item_name),
                recipe_node_name,
                flow=round(rate * amount * 60/recipe['time'], 4)
            )
        for item_name, amount in recipe['products'].items():
            G.add_edge(
                recipe_node_name,
                game.get_bare_item_name(item_name),
                flow=round(rate * amount * 60/recipe['time'], 4)
            )

        if game.RECIPES[recipe_name]['producedIn'] in game.MINING_FACILITIES:
            resource_node_names.append(recipe_node_name)
        else:
            manufacturing_node_names.append(recipe_node_name)
    
    # draw network
    manufacturing_nodes = nx.subgraph(G,
        filter(lambda name: name in manufacturing_node_names,
               G.nodes()))
    mining_nodes = nx.subgraph(G,
        filter(lambda name: name in resource_node_names,
               G.nodes()))
    recipe_node_names = manufacturing_node_names + resource_node_names
    item_nodes = nx.subgraph(G,
        [node_name for node_name in G.nodes()
         if not node_name in recipe_node_names])
    labels = {
        (u, v): str(data['flow'])
        for (u, v, data) in G.edges.data()
    }

    pos = nx.kamada_kawai_layout(G)
    pos = nx.spring_layout(G, pos=pos, iterations=10)
    nx.draw_networkx_nodes(G, nodelist=manufacturing_nodes, pos=pos, 
                           node_color='tab:blue')
    nx.draw_networkx_nodes(G, nodelist=mining_nodes, pos=pos, 
                           node_color='tab:purple')
    nx.draw_networkx_nodes(G, nodelist=item_nodes, pos=pos, 
                           node_color='tab:orange')
    nx.draw_networkx_labels(G, pos, font_size=8)
    nx.draw_networkx_edges(G, pos)
    nx.draw_networkx_edge_labels(G, pos, labels, font_size=6)
    plt.show()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('plan_file', help='JSON dict mapping recipes to amount')
    args = parser.parse_args()

    with open(args.plan_file, 'r') as fp:
        plan = json.load(fp)
    
    main(plan)
