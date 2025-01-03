from argparse import ArgumentParser
import json

import numpy as np

from assistory.optim import rapid_production
from assistory.game import game
from assistory.utils import utils
from assistory.save_parser import save_uncompressor, save_parser
from assistory.save_parser.actor import *


def load_world(save_file_compressed: str) -> World:
    reader = save_uncompressor.CompressedReader.open_reader(save_file_compressed)
    data_uncompressed = reader.read()
    
    # parse file
    reader = save_parser.UncompressedReader(data_uncompressed)
    objects = reader.read()
    world = instantiate_world(objects)

    return world


def extract_player_inventory(player: Player) -> dict:
    player_items_all = player.get_inventory_items()
    player_items = dict()
    for item_name, amount in player_items_all.items():
        if not item_name in game.ITEMS:
            print('WARNING Skip unknown item:', item_name)
            continue
        player_items[item_name] = amount
    return player_items


def load_target_items(target_item_file: str) -> dict:
    with open(target_item_file, 'r') as fp:
        target_items = json.load(fp)
    return target_items


def extract_existing_recipes(factories: List[Factory]) -> dict:
    recipes = dict()
    for factory in factories:
        if isinstance(factory, (ManufacturingBuilding, FrackingBuilding)):
            recipe_name = factory.current_recipe_name
            if not recipe_name in game.RECIPES:
                if recipe_name:
                    print('WARNING Skip unknown recipe:', recipe_name)
                continue
            if factory.is_production_paused:
                print('WARNING Skip paused production:', recipe_name)
                continue
            rate = factory.get_effective_rate()
            recipes[recipe_name] = recipes.get(recipe_name, 0) + rate
    return recipes


def main(compressed_save_file: str, target_item_file: str):
    data_conf = rapid_production.GameDataConfiguration()
    
    world = load_world(compressed_save_file)
    S_items = extract_player_inventory(world.get_player())
    G_items = load_target_items(target_item_file)
    E_recipes = extract_existing_recipes(world.get_factories())
    
    print('Extracted existing production:')
    for recipe_name, amount in E_recipes.items():
        print(recipe_name, amount)

    start_conf = rapid_production.StartConfiguration(
        data_conf,
        S = np.array(utils.vectorize(S_items, data_conf.ITEMS)),
        G = np.array(utils.vectorize(G_items, data_conf.ITEMS)),
        E = np.array(utils.vectorize(E_recipes, data_conf.RECIPES)),
    )
    start_conf.validate()

    optim_conf = rapid_production.OptimizationConfiguration()
    optim_conf = rapid_production.OptimizationConfiguration()
    solver, values, minimal_steps = rapid_production.solve_with_binary_search(
        data_conf, start_conf, optim_conf)
    print(f'Minimal number of steps: {minimal_steps}')
    rapid_production.print_solution_dict(minimal_steps, *values, data_conf)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('compressed_save_file', help='Save file from the game save directory.'
                        ' Used to extract existing production and items from player inventory.')
    parser.add_argument('target_item_file', help='Path to the file defining the goal item'
                        ' amounts. A JSON dict containing of item amount by item name.')
    args = parser.parse_args()
    main(args.compressed_save_file, args.target_item_file)
