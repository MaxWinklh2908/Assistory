from argparse import ArgumentParser
import os
from pprint import pprint

import game
import save_uncompressor
import save_parser
import instantiator
from data_types import *


def print_actors(builds: Iterable[Buildable]):
    print('--------------------Object properties--------------------------------')
    for build in builds:
        print(build)


def extract_existing_recipes(builds: Iterable[Buildable]) -> dict:
    recipes = dict()
    for building in builds:
        if isinstance(building, ManufacturingBuilding):
            recipe_name = building.current_recipe_name
            if not recipe_name in game.RECIPES:
                print('WARNING Skip unknown recipe:', recipe_name)
                continue
            if building.is_production_paused:
                print('WARNING Production paused:', recipe_name)
                continue
            rate = building.get_effective_rate()
            recipes[recipe_name] = recipes.get(recipe_name, 0) + rate
        # TODO:
        # elif isinstance(building, FrackingBuilding):
        #     rate = building.get_effective_rate()
    return recipes


def calculate_item_production(recipes: dict) -> dict:
    item_rates = dict()
    for recipe_name, recipe_amount in recipes.items():
        recipe = game.RECIPES[recipe_name]
        cylce_time = recipe['time'] / 60 # in min
        for item_name, item_amount in recipe['ingredients'].items():
            rate = item_amount / cylce_time * recipe_amount
            item_rates[item_name] = item_rates.get(item_name, 0) - rate
        for item_name, item_amount in recipe['products'].items():
            rate = item_amount / cylce_time * recipe_amount
            item_rates[item_name] = item_rates.get(item_name, 0) + rate
    return {item_name:rate for item_name,rate in item_rates.items() if rate != 0}


def print_production_rates(builds: Iterable[Buildable]):
    recipe_amount = extract_existing_recipes(builds)
    print('--------------------Recipe Rates --------------------------------')
    pprint({
        recipe_name: amount
        for recipe_name, amount in recipe_amount.items()
        # if amount != 0
    })
    item_amount = calculate_item_production(recipe_amount)
    print('--------------------Item Rates --------------------------------')
    pprint({
        item_name: amount
        for item_name, amount in item_amount.items()
        if amount != 0
    })


def print_factory_status(builds: Iterable[Buildable]):
    print('--------------------Factory status (Problem!) --------------------------------')
    for build in builds:
        if build.get_problems():
            print(build, build.get_problems())


def main(compressed_save_file: str):
    # read file
    save_file_name = os.path.basename(compressed_save_file)
    uncompressed_save_file = os.path.join('/tmp', save_file_name[:-4] + '.bin')
    save_uncompressor.uncompress_save_file(compressed_save_file, uncompressed_save_file)
    with open(uncompressed_save_file, 'rb') as fp:
        data = fp.read()
    
    # parse file
    reader = save_parser.UncompressedReader(data)
    objects = reader.read()
    actors = instantiator.instantiate_objects(objects)

    # print stats
    # print_actors(actors)
    print_production_rates(actors)
    print_factory_status(actors)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('compressed_save_file')
    args = parser.parse_args()

    main(args.compressed_save_file)
