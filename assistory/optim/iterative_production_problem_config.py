from dataclasses import dataclass, field

from assistory import game
from assistory.game import ItemValues, ItemFlags, RecipeFlags, BuildingValues


DEFAULT_STEP_DURATION = 5.0 # minutes
DEFAULT_HANDCRAFT_EFFICIENCY = 0.75


@dataclass
class IterativeProductionProblemConfig:
    # Number of iterations. Must be at least 1. Defaults to DEFAULT_STEP_COUNT.
    step_count: int

    # goal amount of items
    G: ItemValues 
    
    # start amount of items    
    S: ItemValues = field(
        default_factory=ItemValues
    )

    # existing item rate/production
    E: ItemValues = field(
        default_factory=ItemValues 
    )

    # recipes that can be used
    unlocked_recipes: RecipeFlags = field(
        default_factory=lambda: RecipeFlags(game.RECIPES)
    )

    # Amount of minutes an iteration takes. Defaults to DEFAULT_STEP_DURATION.
    step_duration: float = DEFAULT_STEP_DURATION

    # handcraft efficiency reduced by item logistics and recipe change.
    # Value of 0 disables handcrafting. Default to DEFAULT_HANDCRAFT_EFFICIENCY.
    handcraft_efficiency: float = DEFAULT_HANDCRAFT_EFFICIENCY

    # objective (always): reduce number of handcraft recipes plus rounded up
    # number of automated recipes

    def get_items_involved(self) -> ItemFlags:
        """
        Get the item names that are involved in the optimization

        Returns:
            ItemFlags: Item names
        """
        involved_processing_item_names = (
            self.unlocked_recipes.get_items_consumed()
            | self.unlocked_recipes.get_items_produced()
        )
        involved_cost_item_names = set(BuildingValues(
            {
                building_name: 1
                for building_name in self.unlocked_recipes.get_buildings_involved()
            }
        ).get_costs().as_dict_ignoring(0))
        return ItemFlags(involved_cost_item_names | involved_processing_item_names)
