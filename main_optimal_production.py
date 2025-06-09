from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
import yaml

from assistory import game
from assistory.game import RecipeFlags
from assistory.optim.static_production_problem import StaticProductionLP, StaticProductionLPConfig
from assistory.optim.static_flow_problem import ReturnCode
from assistory.optim import feasibility_hints
from assistory.save_parser.actor import *


ROUND_NDIGITS = 4


@dataclass
class OptimalProductionProblemUserConfig():

    # File containing a StaticProductionLPConfig
    static_production_config_file: str

    # File containing unlocked recipes
    unlocked_recipes_file: str = ''
    
    # file containing the base item rate
    base_item_rate_file: str = ''

    # File containing numbers of available resource nodes. Use game.Resource_nodes_available if ''.
    available_resource_nodes_file: str = ''

    # file containing occupied resource nodes
    occupied_resource_nodes_file: str = ''

    @staticmethod
    def load_from_file(file_path: str) -> 'OptimalProductionProblemUserConfig':
        with open(file_path, 'r') as fp:
            config_data = yaml.safe_load(fp)
        return OptimalProductionProblemUserConfig(**config_data)
    
    def load_unlocked_automated_recipes(self) -> RecipeFlags:
        """
        Return unlocked recipes filtered by automated recipes only.

        Returns:
            RecipeFlags: Names of unlocked recipes
        """
        if len(self.unlocked_recipes_file) == 0:
            raise RuntimeError(f'unlocked_recipes_file not defined')
        unlocked_reciepes = RecipeFlags.load(self.unlocked_recipes_file)
        return RecipeFlags(
            set(unlocked_reciepes) & set(game.RECIPE_NAMES_AUTOMATED),
            omega=game.RECIPE_NAMES_AUTOMATED
        )

    def load_base_item_rate(self) -> ItemValues:
        if len(self.base_item_rate_file) == 0:
            raise RuntimeError(f'base_item_rate_file not defined')
        return ItemValues.load(self.base_item_rate_file)

    def load_available_resource_nodes(self) -> ResourceNodeValues:
        if len(self.available_resource_nodes_file) == 0:
            raise RuntimeError(f'available_resource_nodes_file not defined')
        return ResourceNodeValues.load(self.available_resource_nodes_file)

    def load_occupied_resource_nodes(self) -> ResourceNodeValues:
        if len(self.occupied_resource_nodes_file) == 0:
            raise RuntimeError(f'occupied_resource_nodes_file not defined')
        return ResourceNodeValues.load(self.occupied_resource_nodes_file)


def load_and_update_production_config(
        optimal_production_config: OptimalProductionProblemUserConfig
    ) -> StaticProductionLPConfig:

    production_lp_config = StaticProductionLPConfig.load_from_file(
        optimal_production_config.static_production_config_file
    )

    if (optimal_production_config.unlocked_recipes_file and
        set(production_lp_config.unlocked_recipes) != set(game.RECIPES)):
        raise ValueError('Either specify locked recipes in production lp config or load it from file')
    if (optimal_production_config.base_item_rate_file and
        production_lp_config.base_item_rate != ItemValues()):
        raise ValueError('Either specify base item rate in production lp config or load it from file')
    if (optimal_production_config.available_resource_nodes_file and
        production_lp_config.available_resource_nodes != ResourceNodeValues(game.NODE_RECIPES_AVAILABLE)):
        raise ValueError('Either specify available nodes in production lp config or load it from file')


    if optimal_production_config.unlocked_recipes_file:
        production_lp_config.unlocked_recipes = optimal_production_config.load_unlocked_automated_recipes()
    
    if optimal_production_config.base_item_rate_file:
        production_lp_config.base_item_rate = optimal_production_config.load_base_item_rate()

    if optimal_production_config.available_resource_nodes_file:
        production_lp_config.available_resource_nodes = optimal_production_config.load_available_resource_nodes()

    if optimal_production_config.occupied_resource_nodes_file:
        occupied_resource_nodes = optimal_production_config.load_occupied_resource_nodes()
        production_lp_config.available_resource_nodes = (
            production_lp_config.available_resource_nodes
            - occupied_resource_nodes
        )
        print('\nUpdated available resources:')
        production_lp_config.available_resource_nodes.round(ROUND_NDIGITS).pprint()

    production_lp_config.check()
    return production_lp_config


def main(
        optimal_production_config: OptimalProductionProblemUserConfig,
        recipes_out_file: Path=None,
        debug: bool=False,
        store_rounded: bool=False,
):
    production_lp_config = load_and_update_production_config(optimal_production_config)

    problem = StaticProductionLP(production_lp_config)
    status = problem.optimize()
    if status != ReturnCode.OPTIMAL:
        print(f"The problem does not have an optimal solution: {status}")
        if debug:
            print('\nChecking production config...')
            feasibility_hints.get_feasibility_hints(production_lp_config)
        else:
            print('Run again with --debug to get hints why this is the case')
        exit(1)

    problem.report(debug)

    if not recipes_out_file is None:
        recipes_used = problem.get_recipes_used()
        recipes_used.save(recipes_out_file, ignore_value=0)
        if store_rounded:
            recipes_used_rounded = recipes_used.round(ROUND_NDIGITS)
            recipes_out_rounded_file = (
                recipes_out_file.parent
                / (recipes_out_file.stem + '_rounded' + recipes_out_file.suffix)
            )
            recipes_used_rounded.save(recipes_out_rounded_file, ignore_value=0)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        'optimal_production_config',
        help='Path to an OptimalProductionConfig'
    )
    parser.add_argument(
        '--out',
        required=False,
        default=None,
        help='Output path to the production plan, i.e. recipe amounts by recipe name',
    )
    parser.add_argument(
        '--debug',
        required=False,
        action='store_true',
        help='If the optimization fails with status infeasible, run checks on the problem configuration',
    )
    parser.add_argument(
        '--store-rounded',
        required=False,
        action='store_true',
        help='Additionally, store the production plan rounded to ROUND_NDIGITS digits'
    )
    args = parser.parse_args()

    optimal_production_config = OptimalProductionProblemUserConfig.load_from_file(
        args.optimal_production_config
    )
    out_file = None if args.out is None else Path(args.out)
    main(optimal_production_config, out_file, args.debug, args.store_rounded)
