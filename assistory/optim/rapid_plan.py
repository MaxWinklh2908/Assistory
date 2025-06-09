from typing import List, Optional

from assistory.game import ItemValues, RecipeValues


class RapidPlan:

    def __init__(self,
                 step_count: int,
                 step_duration: float,
                 recipes_handcraft: List[RecipeValues],
                 recipes_automated: List[RecipeValues],
                 recipe_factories: List[RecipeValues],
):
        """
        Create a rapid plan. It represents a data handle to a building plan
        of recipes over multiple steps.

        Args:
            step_count (int): Number of steps in the plan. Can be 0.
            step_duration (float): Duration of each step in minutes
            recipes_handcraft (List[RecipeValues]): Handcraft recipes at each step
            recipes_automated (List[RecipeValues]): Automated recipes at each step
            recipe_factories (List[RecipeValues]): The minimal integer number of
                buildings for each automated recipe
        """
        if len(recipes_handcraft) != step_count:
            raise ValueError(f'Length mismatch of handcraft recipes: {len(recipes_handcraft)}')
        if len(recipes_automated) != step_count:
            raise ValueError(f'Length mismatch of automated recipes: {len(recipes_automated)}')
        if len(recipe_factories) != step_count:
            raise ValueError(f'Length mismatch of recipes factories: {len(recipe_factories)}')
        if step_count < 0:
            raise ValueError(f'Invalid step count: {step_count}')
        if step_duration < 0:
            raise ValueError(f'Invalid step duration: {step_duration}')
        
        for step_i in range(step_count):
            violations = {
                    recipe_name: (recipes_automated[step_i][recipe_name], recipe_factories[step_i][recipe_name])
                    for recipe_name in recipes_automated[step_i]
                    if round(recipes_automated[step_i][recipe_name], 9) > recipe_factories[step_i][recipe_name]
                }
            if violations:
                raise ValueError(
                    'Recipe factory count must be upper limit for automated recipes'
                    f'. Violations (recipes, factories): {violations}'
                )
        
        self.step_count = step_count
        self.step_duration = step_duration
        self.steps_recipes_handcraft = recipes_handcraft
        self.steps_recipes_automated = recipes_automated
        # ceil(recipe_automated) is equal to recipe_factories. However, due to
        # floating point arithmetic, it must be passed in explicitely
        self.steps_recipe_factories = recipe_factories

    def get_item_rates(self, step_id: int) -> ItemValues:
        """
        Get the production at step. Existing production not included.

        Args:
            step_id (int): Index of the step

        Returns:
            ItemValues: Item rates
        """
        if step_id < 0 or step_id >= self.step_count:
            raise ValueError('Invlid step id: ' + str(step_id))
        
        recipes_automated = self.steps_recipes_automated[step_id]
        recipes_handcraft = self.steps_recipes_handcraft[step_id]
        rates_automated = recipes_automated.get_item_rate_balance()
        rates_handcraft = recipes_handcraft.get_item_rate_balance_handcraft()
        return rates_automated + rates_handcraft
    
    def round(self, ndigits: Optional[int]=None) -> 'RapidPlan':
        """
        Round the recipe amounts according to the digits provided.

        Args:
            ndigits (int, optional): Number of digits after rounding. Output is
                in integer format if None. Defaults to None.

        Returns:
            RapidPlan: plan with rounded values
        """
        return RapidPlan(
            self.step_count,
            self.step_duration,
            [recipes.round(ndigits) for recipes in self.steps_recipes_handcraft],
            [recipes.round(ndigits) for recipes in self.steps_recipes_automated],
            self.steps_recipe_factories,
        )

    def print_debug(self, ndigits: int=3):
        """
        Print the optimization results step by step.

        Args:
            ndigits (int): Number of digits for rounding. Defaults to 3.
        """
        print('\nProduction by step')
        plan_rounded = self.round(ndigits)
        for step_id in range(plan_rounded.step_count):
            x = plan_rounded.get_item_rates(step_id)
            print(step_id, x.round(ndigits).as_dict_ignoring(0))

        print('\nRecipes handcraft by step')
        for step_id in range(plan_rounded.step_count):
            x = plan_rounded.steps_recipes_handcraft[step_id]
            print(step_id, x.as_dict_ignoring(0))

        print('\nRecipes automated by step')
        for step_id in range(plan_rounded.step_count):
            x = plan_rounded.steps_recipes_automated[step_id]
            print(step_id, x.as_dict_ignoring(0))

        print('\nBuildings by step')
        for step_id in range(plan_rounded.step_count):
            x = plan_rounded.steps_recipe_factories[step_id].get_buildings()
            print(step_id, x.round(ndigits).as_dict_ignoring(0))

    def to_dict(self) -> dict:
        """
        Get plan as dictionary

        Returns:
            dict: Mapping of step idx starting from 0 to step_count-1 to step
            description containing recipe amounts by keys handcraft and
            automated
        """
        return {
            'step_count': self.step_count,
            'recipes': {
                step_id: {
                    'handcraft': self.steps_recipes_handcraft[step_id].as_dict_ignoring(0),
                    'automated': self.steps_recipes_automated[step_id].as_dict_ignoring(0),
                    'factories': self.steps_recipe_factories[step_id].as_dict_ignoring(0),
                }
                for step_id in range(self.step_count)
            },
            'step_duration': self.step_duration,
        }

    @staticmethod
    def from_dict(data: dict) -> 'RapidPlan':
        recipes_automated = []
        recipes_handcraft = []
        recipe_factories = []

        for step_id in range(data['step_count']):
            recipe_data = data['recipes'][step_id]
            recipes_automated.append(RecipeValues(recipe_data['automated']))
            recipes_handcraft.append(RecipeValues(recipe_data['handcraft']))
            recipe_factories.append(RecipeValues(recipe_data['factories']))

        return RapidPlan(
            step_count=data['step_count'],
            step_duration=data['step_duration'],
            recipes_handcraft=recipes_handcraft,
            recipes_automated=recipes_automated,
            recipe_factories=recipe_factories,
        )
