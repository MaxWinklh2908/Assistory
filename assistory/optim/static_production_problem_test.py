import unittest
import sys, os

print('Add', os.getcwd(), 'to path')
sys.path.append(os.getcwd())
from assistory import game
from assistory.game import ItemValues, ResourceNodeValues
from assistory.optim import static_production_problem
from assistory.optim.static_flow_problem import ReturnCode
from assistory.optim.static_production_problem_config import StaticProductionLPConfig


# Create a test case class
class TestStaticFlowLP(unittest.TestCase):
    
    def test_max_sink_points_single_recipe(self):
        lp_config = StaticProductionLPConfig(
            unlocked_recipes={'Recipe_MinerMk1Coal_C'},
            base_power=5.0, # 1 MinerMk1 needs 5 MW
            maximize_sink_points=True,
        )
        lp = static_production_problem.StaticProductionLP(lp_config)
        code = lp.optimize()
        self.assertEqual(code, ReturnCode.OPTIMAL)
        self.assertAlmostEqual(
            lp.get_recipes_used()['Recipe_MinerMk1Coal_C'],
            1.0
        )

    def test_max_sink_points_full(self):
        lp_config = StaticProductionLPConfig(
            maximize_sink_points=True,
        )
        lp = static_production_problem.StaticProductionLP(lp_config)
        code = lp.optimize()
        self.assertEqual(code, ReturnCode.OPTIMAL)
        self.assertGreater(lp.objective_value, 1000.0)

    def test_max_item_rate_single_recipe(self):
        lp_config = StaticProductionLPConfig(
            unlocked_recipes={'Recipe_MinerMk1Coal_C'},
            base_power=5.0, # 1 MinerMk1 needs 5 MW
            maximize_sell_rate=True,
            weights_sell_rate=ItemValues({'Desc_Coal_C': 1}),
        )
        lp = static_production_problem.StaticProductionLP(lp_config)
        code = lp.optimize()
        self.assertEqual(code, ReturnCode.OPTIMAL)
        self.assertAlmostEqual(lp.objective_value, 60.0)

    def test_constraint_item_ratio(self):
        lp_config = StaticProductionLPConfig(
            unlocked_recipes={
                'Recipe_MinerMk1Coal_C',
                'Recipe_MinerMk1OreIron_C'
            },
            available_resource_nodes=ResourceNodeValues({
                game.get_resource_node_name('Desc_Coal_C', False): 1.0,
                game.get_resource_node_name('Desc_OreIron_C', False): 2.0,
            }),
            base_power=100.0,
            sell_rate_lower_limits=ItemValues({
                'Desc_Coal_C': 60.0,
                'Desc_OreIron_C': 60.0,
            }),
            maximize_sell_rate=True,
            weights_sell_rate=ItemValues({'Desc_Coal_C': 1}),
        )
        lp = static_production_problem.StaticProductionLP(lp_config)
        code = lp.optimize()
        self.assertEqual(code, ReturnCode.OPTIMAL)
        production = lp.get_recipes_used()
        self.assertAlmostEqual(production['Recipe_MinerMk1Coal_C'], 1.0)
        self.assertAlmostEqual(production['Recipe_MinerMk1OreIron_C'], 1.0)

    def test_min_resources_spent(self):
        lp_config = StaticProductionLPConfig(
            unlocked_recipes={
                'Recipe_MinerMk1OreIron_C',
                'Recipe_IngotIron_C',
                'Recipe_Alternate_PureIronIngot_C',
                'Recipe_WaterPumpWater_C',
            },
            available_resource_nodes=ResourceNodeValues({
                game.get_resource_node_name('Desc_OreIron_C', False): 1.0,
            }),
            base_power=1000.0,
            sell_rate_lower_limits=ItemValues({'Desc_IronIngot_C': 60}),
            minimize_resource_node_usage=True,
        )
        lp = static_production_problem.StaticProductionLP(lp_config)
        code = lp.optimize()
        self.assertEqual(code, ReturnCode.OPTIMAL)
        production = lp.get_recipes_used()
        self.assertAlmostEqual(production['Recipe_IngotIron_C'], 0.0)
        self.assertGreater(production['Recipe_Alternate_PureIronIngot_C'], 0.1)

        lp_config = StaticProductionLPConfig(
            unlocked_recipes={
                'Recipe_MinerMk1OreIron_C',
                'Recipe_IngotIron_C',
                'Recipe_Alternate_PureIronIngot_C',
                'Recipe_WaterPumpWater_C',
            },
            available_resource_nodes=ResourceNodeValues({
                game.get_resource_node_name('Desc_OreIron_C', False): 1.0,
            }),
            base_power=10.0,
            maximize_sell_rate=True,
            weights_sell_rate=ItemValues({'Desc_IronIngot_C': 1}),
        )
        lp = static_production_problem.StaticProductionLP(lp_config)
        code = lp.optimize()
        self.assertEqual(code, ReturnCode.OPTIMAL)
        production = lp.get_recipes_used()
        self.assertAlmostEqual(production['Recipe_Alternate_PureIronIngot_C'], 0.0)
        self.assertGreater(production['Recipe_IngotIron_C'], 0.1)

    # TODO: fuse with min resources (that is a special case)
    def test_min_recipes(self):
        lp_config = StaticProductionLPConfig(
            unlocked_recipes={
                'Recipe_MinerMk1OreIron_C',
                'Recipe_IngotIron_C',
                'Recipe_Alternate_PureIronIngot_C',
                'Recipe_WaterPumpWater_C',
            },
            available_resource_nodes=ResourceNodeValues({
                game.get_resource_node_name('Desc_OreIron_C', False): 1.0,
            }),
            base_power=1000.0,
            sell_rate_lower_limits=ItemValues({'Desc_IronIngot_C': 60}),
            minimize_recipe_count=True,
        )
        lp = static_production_problem.StaticProductionLP(lp_config)
        code = lp.optimize()
        self.assertEqual(code, ReturnCode.OPTIMAL)
        production = lp.get_recipes_used()
        self.assertAlmostEqual(production['Recipe_IngotIron_C'], 0.0)
        self.assertGreater(production['Recipe_Alternate_PureIronIngot_C'], 0.1)

        lp_config = StaticProductionLPConfig(
            unlocked_recipes={
                'Recipe_MinerMk1OreIron_C',
                'Recipe_IngotIron_C',
                'Recipe_Alternate_PureIronIngot_C',
                'Recipe_WaterPumpWater_C',
            },
            available_resource_nodes=ResourceNodeValues({
                game.get_resource_node_name('Desc_OreIron_C', False): 1.0,
            }),
            base_power=10.0,
            maximize_sell_rate=True,
            weights_sell_rate=ItemValues({'Desc_IronIngot_C': 1}),
        )
        lp = static_production_problem.StaticProductionLP(lp_config)
        code = lp.optimize()
        self.assertEqual(code, ReturnCode.OPTIMAL)
        production = lp.get_recipes_used()
        self.assertAlmostEqual(production['Recipe_Alternate_PureIronIngot_C'], 0.0)
        self.assertGreater(production['Recipe_IngotIron_C'], 0.1)


# Run the tests
if __name__ == '__main__':
    unittest.main()
