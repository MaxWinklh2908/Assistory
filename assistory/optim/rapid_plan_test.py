import unittest
import sys, os

print('Add', os.getcwd(), 'to path')
sys.path.append(os.getcwd())
from assistory.game import ItemValues, BuildingValues, RecipeValues
from assistory.optim.rapid_plan import RapidPlan


class TestRapidPlan(unittest.TestCase):

    def setUp(self):
        # Prepare mock data for one step
        self.step_count = 1
        self.step_duration = 60.0
        self.recipes_automated = RecipeValues({'Recipe_IronPlate_C': 1.5})
        self.recipes_handcraft = RecipeValues({'Recipe_Cable_C': 0.5})
        self.recipe_factories = RecipeValues({'Recipe_IronPlate_C': 2.0})

        self.rapid_plan = RapidPlan(
            step_count=self.step_count,
            step_duration=self.step_duration,
            recipes_automated=[self.recipes_automated],
            recipes_handcraft=[self.recipes_handcraft],
            recipe_factories=[self.recipe_factories]
        )

    def test_to_dict_from_dict_identity(self):
        plan_dict = self.rapid_plan.to_dict()
        new_plan = RapidPlan.from_dict(plan_dict)
        self.assertEqual(plan_dict, new_plan.to_dict())

    def test_get_item_rates(self):
        rates = self.rapid_plan.get_item_rates(0)
        self.assertIsInstance(rates, ItemValues)
        expected = ItemValues({
            'Desc_Cable_C': 120.0,
            'Desc_IronIngot_C': -45.0,
            'Desc_IronPlate_C': 30.0,
            'Desc_Wire_C': -240.0
        })
        self.assertEqual(rates, expected)

    def test_recipe_factories(self):
        buildings = self.rapid_plan.steps_recipe_factories[0].get_buildings()
        self.assertIsInstance(buildings, BuildingValues)
        expected = BuildingValues({'Desc_ConstructorMk1_C': 2.0})
        self.assertEqual(buildings, expected)

    def test_invalid_step_index(self):
        with self.assertRaises(ValueError):
            self.rapid_plan.get_item_rates(-1)
        with self.assertRaises(ValueError):
            self.rapid_plan.get_item_rates(10)


if __name__ == '__main__':
    unittest.main()