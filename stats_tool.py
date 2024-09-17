from argparse import ArgumentParser
import os
from pprint import pprint

import game
import save_uncompressor
import save_parser
import instantiator
from data_types import *


def print_actors(actors: Iterable[Actor]):
    print('--------------------Actors--------------------------------')
    for actor in actors:
        print(actor)


def extract_existing_recipes(factories: Iterable[Factory]) -> dict:
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


def print_production_rates(factories: Iterable[Factory]):
    recipe_amount = extract_existing_recipes(factories)
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


def print_factory_status(factories: Iterable[Factory]):
    print('--------------------Factory status (Problem!) --------------------------------')
    for factory in factories:
        if factory.get_problems():
            print(factory, factory.get_problems())


def print_milestone_progress(factories: Iterable[Factory],
                             schematic_manager: SchematicManager):
    print('--------------------Milestone Progress --------------------------------')
    milestone_name = schematic_manager.active_schematic
    milestone_cost = game.SCHEMATICS[milestone_name]['cost']
    payoff = schematic_manager.costs_paid_off.get(milestone_name, {})
    recipe_amount = extract_existing_recipes(factories)
    item_rates = calculate_item_production(recipe_amount)
    max_time = 0
    for item_name, target_amount in milestone_cost.items():
        payoff_amount = payoff.get(item_name, 0)
        item_rate = item_rates.get(item_name, 0)
        if item_rate > 0:
            estimated_time = (target_amount - payoff_amount) / item_rate
        else:
            estimated_time = float('inf')
        print(f'{item_name}: {payoff_amount}/{target_amount}',
              f'+{item_rate:.2f}/min => {estimated_time:.2f} min')
        max_time = max(max_time, estimated_time)
    print(f'Time to finish: {max_time:.2f} min')


def print_game_phase_progress(factories: Iterable[Factory],
                              game_phase_manager: GamePhaseManager):
    print('--------------------Game Phase Progress --------------------------------')
    game_phase_name = game_phase_manager.active_phase
    game_phase_cost = game.SCHEMATICS[game_phase_name]['cost']
    payoff = game_phase_manager.costs_paid_off
    recipe_amount = extract_existing_recipes(factories)
    item_rates = calculate_item_production(recipe_amount)
    max_time = 0
    for item_name, target_amount in game_phase_cost.items():
        payoff_amount = payoff.get(item_name, 0)
        item_rate = item_rates.get(item_name, 0)
        if item_rate > 0:
            estimated_time = (target_amount - payoff_amount) / item_rate
        else:
            estimated_time = float('inf')
        print(f'{item_name}: {payoff_amount}/{target_amount}',
              f'+{item_rate:.2f}/min => {estimated_time:.2f} min')
        max_time = max(max_time, estimated_time)
    print(f'Time to finish: {max_time:.2f} min')
    

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
    world = instantiator.instantiate_world(objects)

    # print stats
    # print_actors(actors)
    # print_production_rates(world.get_factories())
    print_factory_status(world.get_factories())
    if world.get_schematic_manager().has_active_schematic():
        print_milestone_progress(world.get_factories(), world.get_schematic_manager())
    if world.get_game_phase_manager().has_active_phase():
        print_game_phase_progress(world.get_factories(), world.get_game_phase_manager())


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('compressed_save_file')
    args = parser.parse_args()

    main(args.compressed_save_file)
