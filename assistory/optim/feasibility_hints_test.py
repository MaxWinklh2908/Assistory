import unittest
import sys, os

print('Add', os.getcwd(), 'to path')
sys.path.append(os.getcwd())
from assistory.game import ItemValues, RecipeValues, ResourceNodeValues
from assistory.optim import feasibility_hints
from assistory import game


class TestProducableItems(unittest.TestCase):

    def test_unbound(self):
        with self.assertRaises(RuntimeError):
            recipe_count_upper_limits = RecipeValues(omega=game.RECIPE_NAMES_AUTOMATED)
            recipe_count_upper_limits.set_values(float('inf'))
            feasibility_hints.get_producable_items(
                recipe_count_upper_limits=recipe_count_upper_limits,
                recipe_group_count_upper_limits={}
            )

    def test_nothing_producable(self):
        """
        Nothing can be produced if any of these conditions hold (sufficient condition)
         - A: no recipes are available
         - B: no resource nodes are available AND the circular recipes are disabled
        """
        # A
        producable_items = feasibility_hints.get_producable_items(
            recipe_count_upper_limits=RecipeValues(omega=game.RECIPE_NAMES_AUTOMATED)
        )
        self.assertEqual(len(producable_items), 0)
        
        # B
        recipe_group_count_upper_limits = dict()
        for resource_node in game.RESOURCE_NODES.values():
            extraction_recipes = resource_node['extraction_recipes']
            recipe_group_count_upper_limits[extraction_recipes] = 0
        recipe_group_count_upper_limits[('Recipe_WaterPumpWater_C',)] = 0
        recipe_group_count_upper_limits[('Recipe_QuantumEnergy_C',)] = 0
        recipe_count_upper_limits=RecipeValues(omega=game.RECIPE_NAMES_AUTOMATED)
        for recipe_name in game.RECIPE_NAMES_AUTOMATED:
            if not '_Unpackage' in recipe_name:
                recipe_count_upper_limits[recipe_name] = 1.0
        producable_items = feasibility_hints.get_producable_items(
            recipe_count_upper_limits=recipe_count_upper_limits,
            recipe_group_count_upper_limits = recipe_group_count_upper_limits,
        )
        self.assertEqual(len(producable_items), 0)

    def test_single(self):
        recipe_count_upper_limits = RecipeValues(omega=game.RECIPE_NAMES_AUTOMATED)
        recipe_count_upper_limits['Recipe_MinerMk1OreIron_C'] = 1
        producable_items = feasibility_hints.get_producable_items(
            recipe_count_upper_limits=recipe_count_upper_limits,
        )
        self.assertEqual(len(producable_items), 1)

    def test_single_base_rate(self):
        recipe_count_upper_limits = RecipeValues(omega=game.RECIPE_NAMES_AUTOMATED)
        recipe_count_upper_limits['Recipe_Protein_Crab_C'] = 1
        producable_items = feasibility_hints.get_producable_items(
            base_item_rate=ItemValues({
                'Desc_HatcherParts_C': 1,
                'Desc_OreCopper_C': 1
            }),
            recipe_count_upper_limits=recipe_count_upper_limits,
        )
        self.assertEqual(len(producable_items), 1)

    def test_all_producable(self):
        """
        All fully automatically producable items can be produced if all of
        these conditions hold (sufficient condition):
        - A: all ressource nodes are available
        - B: all recipes are available
        """
        # A
        recipe_group_count_upper_limits = dict()
        for resource_node_name, resource_node in game.RESOURCE_NODES.items():
            extraction_recipes = resource_node['extraction_recipes']
            amount = game.NODE_RECIPES_AVAILABLE[resource_node_name]
            recipe_group_count_upper_limits[extraction_recipes] = amount
        # B
        recipe_count_upper_limits = RecipeValues(omega=game.RECIPE_NAMES_AUTOMATED)
        recipe_count_upper_limits.set_values(100.0)
        producable_items = feasibility_hints.get_producable_items(
            recipe_group_count_upper_limits=recipe_group_count_upper_limits,
            recipe_count_upper_limits=recipe_count_upper_limits,
        )
        # Some items can not be produced automatically
        # Note: Items and recipes might change. Then, this test can fail
        self.assertEqual(len(producable_items), 135)


class TestPowerProducable(unittest.TestCase):

    def test_no_automatic_power_available(self):
        producation_chain_incomplete, resources_missing = feasibility_hints.is_power_producable(
            unlocked_recipes={}
        )
        self.assertTrue(producation_chain_incomplete)
        self.assertFalse(resources_missing)

    def test_automatic_power_available(self):
        producation_chain_incomplete, resources_missing = feasibility_hints.is_power_producable(
            unlocked_recipes = {
                'Recipe_WaterPumpWater_C',
                'Recipe_MinerMk2Coal_C',
                'Recipe_GeneratorCoalCoal_C'
            },
        )
        self.assertFalse(producation_chain_incomplete)
        self.assertFalse(resources_missing)

    def test_missing_resources(self):
        producation_chain_incomplete, resources_missing = feasibility_hints.is_power_producable(
            available_resource_nodes=ResourceNodeValues(),
            unlocked_recipes = {
                'Recipe_WaterPumpWater_C',
                'Recipe_MinerMk2Coal_C',
                'Recipe_GeneratorCoalCoal_C'
            },
        )
        self.assertFalse(producation_chain_incomplete)
        self.assertTrue(resources_missing)


# Run the tests
if __name__ == '__main__':
    unittest.main()
