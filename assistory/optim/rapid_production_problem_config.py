from dataclasses import dataclass, field

from assistory import game
from assistory.game import ItemValues, RecipeFlags

from assistory.optim.iterative_production_problem_config import IterativeProductionProblemConfig


DEFAULT_MAX_STEPS = 5 # steps
DEFAULT_STEP_DURATION = 5.0 # minutes
DEFAULT_HANDCRAFT_EFFICIENCY = 0.75


@dataclass
class RapidProductionProblemConfig:
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

    # Number of iterations. Must be at least 1. Defaults to DEFAULT_STEP_COUNT.
    maximal_step_count: int = DEFAULT_MAX_STEPS

    # Amount of minutes an iteration takes. Defaults to DEFAULT_STEP_DURATION.
    step_duration: float = DEFAULT_STEP_DURATION

    # handcraft efficiency reduced by item logistics and recipe change.
    # Value of 0 disables handcrafting. Default to DEFAULT_HANDCRAFT_EFFICIENCY.
    handcraft_efficiency: float = DEFAULT_HANDCRAFT_EFFICIENCY

    # objective (always): Find minimal number of steps to produce goal items

    def get_iterative_production_problem_config(self, step_count: int) -> IterativeProductionProblemConfig:
        if step_count <= 0 or step_count > self.maximal_step_count:
            raise ValueError(f'Invalid number of steps: {step_count}')
        
        return IterativeProductionProblemConfig(
            G=self.G,
            S=self.S,
            E=self.E,
            unlocked_recipes=self.unlocked_recipes,
            step_count=step_count,
            step_duration=self.step_duration,
            handcraft_efficiency=self.handcraft_efficiency,
        )
