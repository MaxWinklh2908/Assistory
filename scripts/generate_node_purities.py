"""
extracting the purities can be done using the [interactive map](https://satisfactory-calculator.com/en/interactive-map):
- Create an empty game save with power disabled ("no power")
- Load this game save into the interactive map
- Place miners on all resource nodes and oil extractors on all oil nodes
- export modified game save back to game
- launch the game save
- save the game after about 10 seconds after the miners stared mining.
- Now the inventory of the miners/extractors contain different amount of items which can be used to calculate the node purity

Important: Oil extractors on pure nodes run full very fast (after about 12 sec) but resource extractors on impure nodes extract first 2 items very slow (about 19 sec). To solve this problem, separate the generation for solid and liquid nodes by using two different save files and fusing the results.

Note:
- This is only possible for miners and oil extractors (which make up most of the resources). It is not possible to place extractors on resource wells in the interactive map.
- Some nodes are blocked by obstacles. This is not a problem for this method
- Water extractors in water are ignored as they have no purity (There is a resource for every water area but this ignored)

Further steps:
- Add (around 30) geysir nodes manually using interactive map. TODO: automate
- Add resource wells manually. Needs to be done manually, as power is required to build extractor but iterative building blocks estimating purity from items in inventory
- Water wells must be added to estimate the water produced from save file when using resource wells

"""

from argparse import ArgumentParser
from matplotlib import pyplot as plt
import json

# add assistory to path
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from assistory.save_parser import compressed_parser, save_parser
from assistory.save_parser.actor import *


STARTUP_TIME = 15 #sec
THRS_SOLID_IMPURE_NORMAL = 45 # items/min
THRS_SOLID_NORMAL_PURE = 90 # items/min
THRS_OIL_IMPURE_NORMAL = 90_000 # liters/min
THRS_OIL_NORMAL_PURE = 180_000 # liters/min


def load_world(save_file_compressed: str) -> World:
    reader = compressed_parser.CompressedReader.open_reader(save_file_compressed)
    data_uncompressed = reader.read()
    
    # parse file
    reader = save_parser.UncompressedReader(data_uncompressed)
    objects = reader.read()
    world = instantiate_world(objects)

    return world


def estimate_production_duration(extractor: FrackingBuilding):
    if 'Recipe_MinerMk1_C' == extractor.build_with_recipe:
        return extractor.current_productivity_measurement_produce_duration - STARTUP_TIME
    elif 'Recipe_OilPump_C' == extractor.build_with_recipe:
        return extractor.current_productivity_measurement_produce_duration
    else:
        raise ValueError('Can not handle building from ' + extractor.build_with_recipe)


def extract_node_inventory_amount(extractor: FrackingBuilding) -> list:
    items = extractor.get_output_inventory_items()
    if len(items) != 1:
        raise RuntimeError(str(extractor), str(items))
    if 'Recipe_MinerMk1_C' == extractor.build_with_recipe:
        return list(items.values())[0]
    elif 'Recipe_OilPump_C' == extractor.build_with_recipe:
        return list(items.values())[0]
    else:
        raise ValueError('Can not handle building from ' + extractor.build_with_recipe)


def estimate_purity(extractor: FrackingBuilding):
    produce_duration = estimate_production_duration(extractor)
    amount = extract_node_inventory_amount(extractor)
    item_rate = (amount / produce_duration) * 60
    if 'Recipe_MinerMk1_C' == extractor.build_with_recipe:
        if item_rate < THRS_SOLID_IMPURE_NORMAL:
            return 'impure'
        elif item_rate < THRS_SOLID_NORMAL_PURE:
            return 'normal'
        else:
            return 'pure'
    elif 'Recipe_OilPump_C' == extractor.build_with_recipe:
        if item_rate < THRS_OIL_IMPURE_NORMAL:
            return 'impure'
        elif item_rate < THRS_OIL_NORMAL_PURE:
            return 'normal'
        else:
            return 'pure'
    else:
        raise ValueError('Can not handle building from ' + extractor.build_with_recipe)

def main(compressed_save_file: str, dry_run: bool=False):
    world = load_world(compressed_save_file)

    # applicable to miners and oil extractors only
    extractors = [
        factory
        for factory in world.get_factories()
        if factory.build_with_recipe in {'Recipe_MinerMk1_C', 'Recipe_OilPump_C'}
    ]

    for ex in extractors:
        if ex.is_production_paused:
            raise RuntimeError('Production paused:')(ex)

    # Debugging
    produce_duration = estimate_production_duration(extractors[0])
    print('produce_duration ingame:', extractors[0].current_productivity_measurement_produce_duration)
    print('produce_duration adjusted:', produce_duration)

    inventory_amounts = [
        extract_node_inventory_amount(ex)
        for ex in extractors
    ]
    print('Unique amounts:', set(inventory_amounts))

    plt.hist(inventory_amounts)
    plt.xlabel('item amount')
    plt.title('Inventory amounts')
    plt.show()
    
    resource_nodes = dict()
    for ex in extractors:
        purity = estimate_purity(ex)
        resource_nodes[ex.resource_node_name] = {
            "resource": ex.resource_name,
            "fracking": False,
            "purity": purity
        }

    item_rates = [
        extract_node_inventory_amount(ex) / estimate_production_duration(ex) * 60
        for ex in extractors
    ]
    print('Unique item rates:', set(item_rates))
    plt.hist(item_rates)
    plt.xlabel('item rate')
    plt.title('Item rates')
    plt.show()

    if not dry_run:
        with open('data/solid_resource_nodes.json', 'w') as fp:
            json.dump(resource_nodes, fp, indent=4)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('compressed_save_file', help='Path to a save file to read stats from')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    main(args.compressed_save_file, dry_run=args.dry_run)
