from argparse import ArgumentParser

import networkx as nx

from assistory.game import ItemValues, RecipeValues
from assistory.utils import graph_export


ROUND_DIGITS = 4
SKIP_WATER = False


def main(recipes_file: str, out_file: str, base_item_rate_file: str=None):

    production = RecipeValues.load(recipes_file)
    if not base_item_rate_file is None:
        base_item_rate = ItemValues.load(base_item_rate_file)
    else:
        base_item_rate = ItemValues()
    
    G = graph_export.create_production_graph(production, base_item_rate, ROUND_DIGITS, SKIP_WATER)

    if out_file.endswith('.gexf'):
        nx.write_gexf(G, out_file)
    else:
        raise ValueError('File type not supported: ' + out_file.split('.')[-1])


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('recipes_file',
                        help='YAML dict mapping recipes to amount')
    parser.add_argument('--out', required=True,
                        help='Path to output file (.gexf)')
    parser.add_argument('--base-item-rate-file', required=False,
                        help='YAML dict mapping items to balance')
    args = parser.parse_args()

    main(args.recipes_file, args.out, args.base_item_rate_file)
