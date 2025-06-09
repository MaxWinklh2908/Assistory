from argparse import ArgumentParser
from pathlib import Path
from typing import Optional

from assistory import game
from assistory.game import ItemValues, RecipeValues, ResourceNodeValues
from assistory.game import BuildingFlags, RecipeFlags
from assistory.save_parser import compressed_parser, save_parser
from assistory.save_parser.actor import *


ROUND_NDIGITS = 4


def load_world(save_file_compressed: str) -> World:
    reader = compressed_parser.CompressedReader.open_reader(save_file_compressed)
    data_uncompressed = reader.read()
    
    # parse file
    reader = save_parser.UncompressedReader(data_uncompressed)
    objects = reader.read()
    world = instantiate_world(objects)

    return world


def print_actors(world: World):
    print('--------------------Actors--------------------------------')
    for actor in world.actors:
        print(actor)


def print_recipes(
        recipe_amount_effective: RecipeValues,
        recipe_amount_base: RecipeValues
):
    """
    List the recipes in production.

    Args:
        recipe_amount_effective (ItemAmounts): Recipe amount considering productivity
        recipe_amount_base (ItemAmounts): Recipe amount ignoring productivity
    """
    print('--------------------Recipe Rates (Productivity/Clocking) --------------------------------')
    recipes_effective = recipe_amount_effective.round(ROUND_NDIGITS)
    recipes_base = recipe_amount_base.round(ROUND_NDIGITS)
    for recipe_name in sorted(recipe_amount_base):
        if recipes_base[recipe_name] == 0:
            continue
        rate_prod = recipes_effective[recipe_name]
        rate_clock = recipes_base[recipe_name]
        print(f'{recipe_name}: {rate_prod}/{rate_clock}')


def print_production_rates(
        recipe_amount_effective: RecipeValues,
        recipe_amount_base: RecipeValues,
):
    """
    Aggregate the items produced for selling, i.e. the items produced minus the
    items consumed.

    Args:
        recipe_amount_effective (ItemAmounts): Recipe amount considering productivity
        recipe_amount_base (ItemAmounts): Recipe amount ignoring productivity
    """
    
    item_rate_effective = recipe_amount_effective.get_item_rate_balance().round(ROUND_NDIGITS)
    item_rate_base = recipe_amount_base.get_item_rate_balance().round(ROUND_NDIGITS)
    print('--------------------Item Rates (Productivity/Clocking) --------------------------------')
    for item_name in sorted(item_rate_base):
        if item_rate_base[item_name] == 0:
            continue
        rate_clock = item_rate_base[item_name]
        rate_prod = item_rate_effective[item_name]
        unit = 'm^3/min' if item_name in game.ITEM_NAMES_LIQUID else 'items/min'
        print(f'{item_name}: {rate_prod}/{rate_clock} {unit}')


def print_problems(world: World):
    print('--------------------Factory status (Problem!) --------------------------------')
    for factory in world.get_factories():
        if factory.get_problems():
            productivity = factory.get_productivity() * 100 if factory.is_productivity_monitor_enabled else 0
            print(factory, f'| {productivity:.1f}%', factory.get_problems())


def print_factories_paused(world: World):
    print('-------------------- Factories paused--------------------------------')
    for factory in world.get_factories():
         if factory.is_production_paused:
              print(factory)


def estimate_time(target_amount: float, payoff_amount: float, item_rate: float) -> float:
    if item_rate > 0:
        return (target_amount - payoff_amount) / item_rate
    elif target_amount - payoff_amount <= 0:
        return 0
    else:
        return float('inf')


def print_payoff_progress(costs: ItemValues, payoff: ItemValues, item_rates: ItemValues):
    max_time = 0
    for item_name, target_amount in costs.as_dict_ignoring(0).items():
        payoff_amount = payoff[item_name]
        item_rate = item_rates[item_name]
        estimated_time = estimate_time(target_amount, payoff_amount, item_rate)
        print(f'{item_name}: {payoff_amount}/{target_amount}',
              f'+{item_rate:.2f}/min => {estimated_time:.2f} min')
        max_time = max(max_time, estimated_time)
    print(f'Time to finish: {max_time:.2f} min')


def print_milestone_progress(world: World):
    print('--------------------Milestone Progress --------------------------------')
    schematic_manager = world.get_schematic_manager()
    milestone_name = schematic_manager.active_schematic
    print('Active milestone:', milestone_name)
    print_payoff_progress(
        game.SCHEMATICS[milestone_name]['costs'],
        schematic_manager.costs_paid_off.get(milestone_name, ItemValues()),
        world.get_active_recipes().get_item_rate_balance()
    )


def print_game_phase_progress(world: World):
    print('--------------------Game Phase Progress --------------------------------')
    game_phase_manager = world.get_game_phase_manager()
    game_phase_name = game_phase_manager.active_phase
    print('Active Phase:', game_phase_name)
    print_payoff_progress(
        game.SCHEMATICS[game_phase_name]['costs'],
        game_phase_manager.costs_paid_off,
        world.get_active_recipes().get_item_rate_balance()
    )


def print_unlocking_progress(
        purchased_schematics: SchematicFlags,
        buildings_unlocked: BuildingFlags,
        recipes_unlocked: RecipeFlags,
        ):
    print('--------------------Unlock Progress-------------------------------')
    print('Unlocked schematics:')
    print(sorted(purchased_schematics))

    print('\nUnlocked buildings:')
    print(sorted(buildings_unlocked))
        
    print('\nUnlocked recipes:')
    print(sorted(recipes_unlocked))


def print_inventory(inventory_items: ItemValues):
    print('---------------Player Inventory + Dimensional Depot---------------')
    inventory_items.pprint(ignore_value=0)


def print_resource_nodes(resource_nodes: ResourceNodeValues):    
    print('--------------------Occupied Resource Nodes-----------------------')
    resource_nodes.round(ROUND_NDIGITS).pprint(ignore_value=0)

def main(
        compressed_save_file: str,
        output_dir: Optional[Path]=None,
        print_problems_: bool=False,
        print_actors_: bool=False,
        print_inventory_: bool=False,
        print_unlocking_: bool=False,
        print_progress_: bool=False,
        print_production_: bool=False,
        print_paused_: bool=False,
        print_occupied_resource_nodes_: bool=False,
        store_rounded: bool=False,
        ):
    def save_values(values, file_name: Path):
        values.save(file_name, ignore_value=0)
        if store_rounded:
            file_name_rounded = Path(str(file_name)[:-4] + '_rounded.yml')
            values_rounded = values.round(ROUND_NDIGITS)
            values_rounded.save(file_name_rounded, ignore_value=0)

    world = load_world(compressed_save_file)

    if print_actors_:
        print_actors(world)

    inventory_items = (
        world.get_player().get_items() + world.get_central_storage().get_items()
    )
    if print_inventory_:
        print_inventory(inventory_items)
    if not output_dir is None:
        inventory_items.save(output_dir / 'base_items.yml', ignore_value=0)

    sm = world.get_schematic_manager()
    recipes_unlocked = sm.purchased_schematics.get_recipes_unlocked()
    buildings_unlocked = sm.purchased_schematics.get_buildings_unlocked()
    if print_unlocking_:
        print_unlocking_progress(
            sm.purchased_schematics,
            buildings_unlocked,
            recipes_unlocked
        )
    if not output_dir is None:
        sm.purchased_schematics.save(output_dir / 'unlocked_schematics.yml')
        recipes_unlocked.save(output_dir / 'unlocked_recipes.yml')
        buildings_unlocked.save(output_dir / 'unlocked_buildings.yml')

    if print_progress_:
        if world.get_schematic_manager().has_active_schematic():
            print_milestone_progress(world)
        if world.get_game_phase_manager().has_active_phase():
            print_game_phase_progress(world)

    recipe_amount_effective = world.get_active_recipes()
    recipe_amount_base = world.get_active_recipes(ignore_productivity=True)
    if print_production_:
        print_recipes(recipe_amount_effective, recipe_amount_base)
        print_production_rates(recipe_amount_effective, recipe_amount_base)
    if not output_dir is None:
        save_values(recipe_amount_base, output_dir / 'base_recipe_count.yml')
        item_rate_base = recipe_amount_base.get_item_rate_balance()
        save_values(item_rate_base, output_dir / 'base_item_rate.yml')

    if print_problems_:
        print_problems(world)

    if print_paused_:
        print_factories_paused(world)

    occupied_resource_nodes = world.get_occupied_resource_nodes()
    if print_occupied_resource_nodes_:
        print_resource_nodes(occupied_resource_nodes)
    if not output_dir is None:
        save_values(occupied_resource_nodes, output_dir / 'occupied_resource_nodes.yml')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('compressed_save_file', help='Path to a save file to read stats from')
    parser.add_argument('--out', required=False, type=str, default=None,
                        help='Path to an output directory to store game stats')
    parser.add_argument('--print-problems', required=False, action='store_true',
                        help='List all detected problems of factories')
    parser.add_argument('--print-actors', required=False, action='store_true',
                        help='List of all actors')
    parser.add_argument('--print-inventory', required=False, action='store_true',
                        help='Summarize items in player inventory and dimensional depot')
    parser.add_argument('--print-unlocking', required=False, action='store_true',
                        help='List unlocked recipes and factory buildings')
    parser.add_argument('--print-progress', required=False, action='store_true',
                        help='Show progress of milestone and game phase and project goal time')
    parser.add_argument('--print-production', required=False, action='store_true',
                        help='Summarize production statistics')
    parser.add_argument('--print-paused', required=False, action='store_true',
                        help='List paused factories')
    parser.add_argument('--print-occupied-resource-nodes', required=False, action='store_true',
                        help='Summarize the number of resource nodes used')
    parser.add_argument('--print-all', required=False, action='store_true',
                        help='Print all stats')
    parser.add_argument('--store-rounded', required=False, action='store_true',
                        help='Additionally, store the files with values rounded'
                             ' to ROUND_NDIGITS digits')
    args = parser.parse_args()

    if not args.out is None:
        output_dir = Path(args.out)
        if not output_dir.exists():
            output_dir.mkdir(parents=True)
    else:
        output_dir = None

    main(
        args.compressed_save_file,
        output_dir,
        args.print_all or args.print_problems,
        args.print_all or args.print_actors,
        args.print_all or args.print_inventory,
        args.print_all or args.print_unlocking,
        args.print_all or args.print_progress,
        args.print_all or args.print_production,
        args.print_all or args.print_paused,
        args.print_all or args.print_occupied_resource_nodes,
        args.store_rounded,
    )
