from argparse import ArgumentParser
import json
import os

import numpy as np

import instantiator
import rapid_production
import game
import utils
import save_reader, save_uncompressor, save_parser
from data_types import *


def load_world(compressed_save_file: str) -> World:
    save_file_name = os.path.basename(compressed_save_file)
    uncompressed_save_file = os.path.join('/tmp', save_file_name[:-4] + '.bin')
    save_uncompressor.uncompress_save_file(compressed_save_file, uncompressed_save_file)

    reader = save_parser.open_reader(uncompressed_save_file)
    objects = reader.read()
    world = instantiator.instantiate_world(objects)
    return world


def read_stack_item(payload: bytes) -> str:
    reader = save_reader.SaveReader(payload)
    reader.idx += 4
    return reader.read_string()


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
                print('WARNING Skip unknown recipe:', recipe_name)
                continue
            if factory.is_production_paused:
                print('WARNING Production paused:', recipe_name)
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
    # ignore production with handcrafted input TODO: find other solution
    E_recipes['Recipe_Biofuel_C'] = 0
    start_conf = rapid_production.StartConfiguration(
        data_conf,
        S = np.array(utils.vectorize(S_items, game.ITEMS)),
        G = np.array(utils.vectorize(G_items, game.ITEMS)),
        E = np.array(utils.vectorize(E_recipes, game.RECIPES)),
    )

    solver, values, minimal_steps = rapid_production.solve(data_conf, start_conf)
    print(f'Minimal number of steps: {minimal_steps}')
    rapid_production.print_solution_dict(minimal_steps, *values)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('compressed_save_file')
    parser.add_argument('target_item_file')
    args = parser.parse_args()
    main(args.compressed_save_file, args.target_item_file)
