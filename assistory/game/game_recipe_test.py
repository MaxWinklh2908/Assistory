import unittest
import sys, os

print('Add', os.getcwd(), 'to path')
sys.path.append(os.getcwd())
from assistory.game.game_recipe import (
    RecipeValues, RecipeFlags, RECIPES, RECIPE_NAMES_HANDCRAFTED,
    consumed_by, produced_by, produced_in, get_extracted_resource_name
)
from assistory.game.game_item import ItemFlags, ITEMS
from assistory.game.game_building import BuildingFlags, BUILDINGS
from assistory.game.game_resource_node import ResourceNodeValues, get_resource_node_name


class TestRecipeModule(unittest.TestCase):

    def test_get_extracted_resource_name(self):
        self.assertEqual(
            get_extracted_resource_name('Recipe_PackagedAlumina_C'),
            None
        )
        self.assertEqual(
            get_extracted_resource_name('Recipe_HandcraftOreCopper_C'),
            'Desc_OreCopper_C'
        )
        self.assertEqual(
            get_extracted_resource_name('Recipe_HandcraftOreCopper_C'),
            'Desc_OreCopper_C'
        )
        self.assertEqual(
            get_extracted_resource_name('Recipe_MinerMk1OreCopper_C'),
            'Desc_OreCopper_C'
        )
        self.assertEqual(
            get_extracted_resource_name('Recipe_WaterPumpWater_C'),
            'Desc_Water_C'
        )


class TestRecipeValues(unittest.TestCase):

    def test_item_balance_single(self):
        recipe_amounts = RecipeValues({'Recipe_PackagedAlumina_C': 0.5})
        item_balance = recipe_amounts.get_item_rate_balance()
        self.assertAlmostEqual(-60, item_balance['Desc_AluminaSolution_C'])
        self.assertAlmostEqual(-60, item_balance['Desc_FluidCanister_C'])
        self.assertAlmostEqual( 60, item_balance['Desc_PackagedAlumina_C'])

    def test_item_balance_neutral(self):
        recipe_amounts = RecipeValues({
            'Recipe_PackagedAlumina_C': 1,
            'Recipe_UnpackageAlumina_C': 1
        })
        item_balance = recipe_amounts.get_item_rate_balance()
        for value in item_balance.values():
            self.assertAlmostEqual(0, value)

    def test_item_balance_handcraft(self):
        recipe_amounts = RecipeValues({
            'Recipe_IngotIron_C': 3,
            'Recipe_IronRod_C': 1
        }, omega=RECIPE_NAMES_HANDCRAFTED)
        item_balance = recipe_amounts.get_item_rate_balance_handcraft()
        self.assertAlmostEqual(-240, item_balance['Desc_OreIron_C'])
        self.assertAlmostEqual(240, item_balance['Desc_IronRod_C'])
        self.assertEqual(
            {'Desc_OreIron_C', 'Desc_IronRod_C'},
            set(item_balance.as_dict_ignoring(0))
        )

    def test_item_balance_handcraft_limited_to_handcrafted_recipes(self):
        recipe_amounts = RecipeValues({
            'Recipe_IngotIron_C': 3,
        }, omega=RECIPES)
        recipe_amounts.get_item_rate_balance_handcraft()
        
        with self.assertRaises(ValueError):
            recipe_amounts = RecipeValues({
                'Recipe_IngotIron_C': 3,
                'Recipe_UnpackageAlumina_C': 0.1,
            }, omega=RECIPES)
            recipe_amounts.get_item_rate_balance_handcraft()

    def test_buildings(self):
        recipe_amounts = RecipeValues({
            'Recipe_PackagedAlumina_C': 0.5,
            'Recipe_UnpackageAlumina_C': 1.5
        })
        buildings = recipe_amounts.get_buildings()
        self.assertAlmostEqual(2, buildings['Desc_Packager_C'])

    def test_resource_nodes_used(self):
        recipes = RecipeValues()
        self.assertEqual(
            recipes.get_resource_nodes_used(),
            ResourceNodeValues()
        )

        recipes = RecipeValues({
            'Recipe_MinerMk2OreCopper_C': 1.0,
        })
        self.assertEqual(
            recipes.get_resource_nodes_used(),
            ResourceNodeValues(
                {get_resource_node_name('Desc_OreCopper_C', False): 1}
            )
        )

        recipes = RecipeValues({
            'Recipe_MinerMk2OreCopper_C': 1.0,
            'Recipe_HandcraftOreCopper_C': 1.0
        })
        self.assertEqual(
            recipes.get_resource_nodes_used(),
            ResourceNodeValues(
                {get_resource_node_name('Desc_OreCopper_C', False): 1}
            )
        )


class TestRecipeFlags(unittest.TestCase):

    def test_items_involved(self):
        # no recipe
        recipe_amounts = RecipeFlags()
        self.assertEqual(ItemFlags(), recipe_amounts.get_items_consumed())
        self.assertEqual(ItemFlags(), recipe_amounts.get_items_produced())

        # single recipe
        recipe_amounts = RecipeFlags({'Recipe_CartridgeChaos_Packaged_C'})
        self.assertEqual(ItemFlags({
            'Desc_CartridgeStandard_C',
            'Desc_AluminumCasing_C',
            'Desc_TurboFuel_C',
        }), recipe_amounts.get_items_consumed())
        self.assertEqual(ItemFlags({
            'Desc_CartridgeChaos_C',
        }), recipe_amounts.get_items_produced())

        # all recipes
        recipe_amounts = RecipeFlags(RECIPES)
        items_involved = recipe_amounts.get_items_consumed() | recipe_amounts.get_items_produced()
        for item_name in ITEMS:
            if not consumed_by[item_name] and not produced_by[item_name]:
                self.assertNotIn(item_name, items_involved)

    def test_buildings_involved(self):
        # no recipe
        recipe_amounts = RecipeFlags()
        self.assertEqual(BuildingFlags(), recipe_amounts.get_buildings_involved())

        # single recipe
        recipe_amounts = RecipeFlags({'Recipe_CartridgeChaos_Packaged_C'})
        self.assertEqual(BuildingFlags({
            'Desc_ManufacturerMk1_C',
        }), recipe_amounts.get_buildings_involved())

        # all recipes
        recipe_amounts = RecipeFlags(RECIPES)
        buildings_involved = recipe_amounts.get_buildings_involved()
        for building_name in BUILDINGS:
            if not produced_in[building_name]:
                self.assertNotIn(building_name, buildings_involved)

    
# Run the tests
if __name__ == '__main__':
    unittest.main()
