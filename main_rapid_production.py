from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
from pprint import pprint
import yaml

from assistory.game import RecipeFlags, ItemValues
from assistory import game
from assistory.optim import rapid_production_problem
from assistory.optim.static_flow_problem import ReturnCode
from assistory.optim.rapid_production_problem_config import RapidProductionProblemConfig


ROUND_NDIGITS = 4


@dataclass
class RapidProductionProblemUserConfig():

    # File containing an amount of items to reach
    target_item_file: str

    # File containing item amounts of the inventory
    inventory_items_file: str = ''

    # File containing unlocked recipes
    unlocked_recipes_file: str = ''
    
    # file containing the amounts of existing production as item rates
    base_item_rate_file: str = ''

    # # File containing numbers of available resource nodes. Use game.Resource_nodes_available if ''.
    # available_resource_nodes_file: str = ''

    # # file containing occupied resource nodes
    # occupied_resource_nodes_file: str = ''

    # maximal steps in the plan. The higher the number of steps, the closer the
    # result will approach optimality.
    steps: int = 10

    # duration of each step in minutes
    step_duration: float = 1.0

    # handcraft efficiency reduced by item logistics and recipe change.
    # Value of 0 disables handcrafting
    handcraft_efficiency: float = 0.75

    @staticmethod
    def load_from_file(file_path: str) -> 'RapidProductionProblemUserConfig':
        with open(file_path, 'r') as fp:
            config_data = yaml.safe_load(fp)
        return RapidProductionProblemUserConfig(**config_data)
    
    def load_unlocked_recipes(self) -> RecipeFlags:
        if len(self.unlocked_recipes_file) == 0:
            raise RuntimeError(f'unlocked_recipes_file not defined')
        return RecipeFlags.load(self.unlocked_recipes_file)

    def load_target_items(self) -> ItemValues:
        if len(self.target_item_file) == 0:
            raise RuntimeError(f'target_item_file not defined')
        target_items = ItemValues.load(self.target_item_file)
        for item_name, amount in target_items.items():
            if amount < 0:
                raise ValueError('Negative target amount:', item_name, amount)
        return target_items
    
    def load_inventory_items(self) -> ItemValues:
        if len(self.inventory_items_file) == 0:
            raise RuntimeError(f'inventory_items_file not defined')
        inventory_items = ItemValues.load(self.inventory_items_file)
        for item_name, amount in inventory_items.items():
            if amount < 0:
                raise ValueError('Negative inventory:', item_name, amount)
        return inventory_items

    def load_base_item_rate(self) -> ItemValues:
        if len(self.base_item_rate_file) == 0:
            raise RuntimeError(f'base_item_rate_file not defined')
        return ItemValues.load(self.base_item_rate_file)

    # def load_available_resource_nodes(self) -> ResourceNodeValues:
    #     if len(self.available_resource_nodes_file) == 0:
    #         raise RuntimeError(f'available_resource_nodes_file not defined')
    #     return ResourceNodeValues.load(self.available_resource_nodes_file)

    # def load_occupied_resource_nodes(self) -> ResourceNodeValues:
    #     if len(self.occupied_resource_nodes_file) == 0:
    #         raise RuntimeError(f'occupied_resource_nodes_file not defined')
    #     return ResourceNodeValues.load(self.occupied_resource_nodes_file)
    
    def get_problem_configuration(self) -> RapidProductionProblemConfig:
        G_items = self.load_target_items()

        if self.inventory_items_file:
            S_items = self.load_inventory_items()
        else:
            S_items = ItemValues()

        if self.base_item_rate_file:
            E_item_rates = self.load_base_item_rate()
        else:
            E_item_rates = ItemValues(omega=game.RECIPE_NAMES_AUTOMATED)

        if self.unlocked_recipes_file:
            unlocked_recipes = self.load_unlocked_recipes()
        else:
            unlocked_recipes = RecipeFlags(game.RECIPES)

        problem_config = RapidProductionProblemConfig(
            S=S_items,
            G=G_items,
            E=E_item_rates,
            unlocked_recipes=unlocked_recipes,
            maximal_step_count=self.steps,
            step_duration=self.step_duration,
            handcraft_efficiency=self.handcraft_efficiency,
        )
        return problem_config


def main(
        rapid_production_config: RapidProductionProblemUserConfig,
        plan_out_file: Path=None, 
        debug: bool=False,
        store_rounded: bool=False
):
    problem_conf = rapid_production_config.get_problem_configuration()
    
    problem = rapid_production_problem.RapidProductionProblem(problem_conf)
    status = problem.optimize(verbose=True)
    
    if status == ReturnCode.INFEASIBLE_OR_UNBOUNDED:
        print('Problem infeasible')
        return
    elif status == ReturnCode.OPTIMAL:
        print(f'Minimal number of steps: {problem.objective_value}')
    else:
        raise RuntimeError('Unexpected return code:' + str(status))

    plan = problem.get_rapid_plan()

    if debug:
        plan.print_debug()

    if not plan_out_file is None:
        with plan_out_file.open('w') as fp:
            yaml.dump(plan.to_dict(), fp, indent=4)
        if store_rounded:
            plan_rounded = plan.round(ROUND_NDIGITS)
            plan_out_rounded_file = (
                plan_out_file.parent
                / (plan_out_file.stem + '_rounded' + plan_out_file.suffix)
            )
            with plan_out_rounded_file.open('w') as fp:
                yaml.dump(plan_rounded.to_dict(), fp, indent=4)
        
    else:
        pprint(plan.round(ROUND_NDIGITS).to_dict())


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        'rapid_production_config',
        help='Path to an RapidProductionConfig'
    )
    parser.add_argument(
        '--out',
        required=False,
        default=None,
        help='A JSON file to store the results',
    )
    parser.add_argument(
        '--debug',
        required=False,
        action='store_true',
        help='Print additional details',
    )
    parser.add_argument(
        '--store-rounded',
        required=False,
        action='store_true',
        help='Additionally, store the production plan rounded to ROUND_NDIGITS digits'
    )
    args = parser.parse_args()

    rapid_production_config = RapidProductionProblemUserConfig.load_from_file(
        args.rapid_production_config
    )
    out_file = None if args.out is None else Path(args.out)
    main(rapid_production_config, out_file, args.debug, args.store_rounded)
