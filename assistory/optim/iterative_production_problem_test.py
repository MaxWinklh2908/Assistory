import unittest
import sys, os

print('Add', os.getcwd(), 'to path')
sys.path.append(os.getcwd())
from assistory import game
from assistory.game import ItemValues, ItemFlags, RecipeFlags
from assistory.optim.static_flow_problem import ReturnCode
from assistory.optim.iterative_production_problem import IterativeProductionData, IterativeProductionProblem
from assistory.optim.iterative_production_problem_config import IterativeProductionProblemConfig


class IterativeProductionDataTest(unittest.TestCase):

    def test_empty(self):
        data_conf = IterativeProductionData(
            ItemFlags(),
            RecipeFlags()
        )
        self.assertEqual(0, len(data_conf.recipes_automated))
        self.assertEqual(0, len(data_conf.recipes_handcraft))
        self.assertEqual(0, len(data_conf.items))

    def test_sample_configuration(self):
        items_involved = ItemFlags({
            'Desc_OreIron_C',
            'Desc_IronIngot_C',
            'Desc_IronPlate_C',
            'Desc_IronRod_C',
            'Desc_Wire_C',
        })
        recipes_involved = RecipeFlags({
            'Recipe_HandcraftOreIron_C',
            'Recipe_IngotIron_C',
            'Recipe_IronPlate_C',
            'Recipe_IronRod_C',
        })
        data_conf = IterativeProductionData(
            items_involved, recipes_involved
        )
        self.assertEqual(3, len(data_conf.recipes_automated))
        self.assertEqual(4, len(data_conf.recipes_handcraft))
        self.assertEqual(5, len(data_conf.items))
        self.assertEqual(
            (len(items_involved), len(game.RECIPE_NAMES_AUTOMATED & recipes_involved)),
            data_conf.get_recipe_automated_production_matrix().shape
        )
        self.assertEqual(
            (len(items_involved), len(game.RECIPE_NAMES_HANDCRAFTED & recipes_involved)),
            data_conf.get_recipe_handcrafted_production_matrix().shape
        )
        self.assertEqual(
            (len(items_involved), len(game.RECIPE_NAMES_AUTOMATED & recipes_involved)),
            data_conf.get_recipe_automated_cost_matrix().shape
        )


# Create a test case class
class IterativeProductionTest(unittest.TestCase):

    def setUp(self):
        self.unlocked_recipes = RecipeFlags({
                'Recipe_HandcraftOreIron_C',
                'Recipe_IngotIron_C',
                'Recipe_IronPlate_C',
                'Recipe_IronRod_C',
            })
        return super().setUp()
    
    def test_involved_items_dont_ignore_target(self):
        problem_conf = IterativeProductionProblemConfig(
            step_count=1,
            step_duration=1,
            S = ItemValues({
                'Desc_OreIron_C': 10,
                'Desc_IronIngot_C': 0,
            }),
            G = ItemValues({
                'Desc_OreIron_C': 10,
                'Desc_IronIngot_C': 10,
            }),
            unlocked_recipes=RecipeFlags({
                'Recipe_IngotIron_C',
                'Recipe_HandcraftOreIron_C'
            }),
        )
        problem = IterativeProductionProblem(problem_conf)
        code = problem.optimize()
        self.assertEqual(code, ReturnCode.OPTIMAL)
        self.assertAlmostEqual(problem.objective_value, 0.25)

    def test_locked_recipes(self):
        problem_conf = IterativeProductionProblemConfig(
            S = ItemValues({
                'Desc_IronRod_C': 5,
                'Desc_Wire_C': 8
            }),
            G = ItemValues({
                'Desc_IronIngot_C': 10
            }),
            step_count=1,
            unlocked_recipes=RecipeFlags({
                'Recipe_IngotIron_C',
                'Recipe_HandcraftOreIron_C'
            }),
        )
        problem = IterativeProductionProblem(problem_conf)
        code = problem.optimize()
        self.assertEqual(code, ReturnCode.OPTIMAL)
        recipes_handcraft = problem.get_rapid_plan().steps_recipes_handcraft[0]
        self.assertAlmostEqual(problem.objective_value, 0.05)
        self.assertAlmostEqual(recipes_handcraft['Recipe_HandcraftOreIron_C'], 0.025)
        self.assertAlmostEqual(recipes_handcraft['Recipe_IngotIron_C'], 0.025)

        problem_conf = IterativeProductionProblemConfig(
            S = ItemValues({
                'Desc_IronRod_C': 5,
                'Desc_Wire_C': 8
            }),
            G = ItemValues({
                'Desc_IronIngot_C': 10
            }),
            step_count=1,
            unlocked_recipes=RecipeFlags({
                'Recipe_IngotIron_C',
            }),
        )
        problem = IterativeProductionProblem(problem_conf)
        code = problem.optimize()
        self.assertEqual(code, ReturnCode.INFEASIBLE_OR_UNBOUNDED)

    def test_goal_reachable_by_unlocked_recipes(self):
        problem_conf = IterativeProductionProblemConfig(
            S = ItemValues({
                'Desc_IronRod_C': 5,
                'Desc_Wire_C': 8
            }),
            G = ItemValues({
                'Desc_IronIngot_C': 10
            }),
            step_count=1,
            unlocked_recipes=RecipeFlags(),
        )
        with self.assertRaises(ValueError):
            IterativeProductionProblem(problem_conf)

    def test_infeasible_production(self):
        problem_conf = IterativeProductionProblemConfig(
            S=ItemValues(),
            G=ItemValues({
                'Desc_IronIngot_C': 1000
            }),
            step_count=1,
            unlocked_recipes=RecipeFlags({
                'Recipe_IngotIron_C',
                'Recipe_HandcraftOreIron_C'
            }),
        )
        problem = IterativeProductionProblem(problem_conf)
        code = problem.optimize()
        self.assertEqual(ReturnCode.INFEASIBLE_OR_UNBOUNDED, code)
        self.assertEqual(problem.objective_value, None)
        with self.assertRaises(RuntimeError):
            problem.get_rapid_plan()

    def test_fix_balance(self):
        # There are imbalances in the item production that the optimization need to fix
        problem_conf = IterativeProductionProblemConfig(
            S=ItemValues({
                'Desc_Cement_C': 20,
                'Desc_Cable_C': 8,
                'Desc_IronPlate_C': 20,
                'Desc_IronPlateReinforced_C': 2
            }),
            G=ItemValues({
                'Desc_OreIron_C': 30
            }),
            E=ItemValues({
                'Desc_Cement_C': 11.25,
                'Desc_Stone_C': -33.75
            }),
            step_count=3,
            step_duration=1.0,
            unlocked_recipes=RecipeFlags({
                'Recipe_HandcraftStone_C',
                'Recipe_HandcraftOreIron_C',
                'Recipe_IngotIron_C',
                'Recipe_Concrete_C',
            }),
        )
        problem = IterativeProductionProblem(problem_conf)
        code = problem.optimize()
        self.assertEqual(ReturnCode.OPTIMAL, code)
        self.assertAlmostEqual(1.64, problem.objective_value, places=2)

    def test_start_from_zero(self):
        problem_conf = IterativeProductionProblemConfig(
            S=ItemValues({
                'BP_ItemDescriptorPortableMiner_C': 1,
                'Desc_IronPlateReinforced_C': 100,
                'Desc_Cement_C': 100,
                'Desc_IronPlate_C': 100,
            }),
            G=ItemValues({
                'Desc_IronRod_C': 90
            }),
            step_count=10,
            step_duration=1.0,
            unlocked_recipes=RecipeFlags({
                recipe_name for recipe_name in game.RECIPES
                if '_MinerMk1' in recipe_name or 'Iron' in recipe_name
            }),
        )
        problem = IterativeProductionProblem(problem_conf)
        code = problem.optimize()
        self.assertEqual(ReturnCode.OPTIMAL, code)
        self.assertAlmostEqual(2.62, problem.objective_value, places=2)

    def test_disallow_dismantling(self):
        problem_conf = IterativeProductionProblemConfig(
            S=ItemValues({
                # ingredients
                'Desc_ModularFrame_C': 3.75,
                'Desc_Rubber_C': 30.0,
                'Desc_SteelPlate_C': 22.5,
                # building costs
                'Desc_Cable_C': 50,
                'Desc_ModularFrame_C': 20,
                'Desc_Motor_C': 10,
                'Desc_Plastic_C': 50,
            }),
            G=ItemValues({
                # products
                'Desc_SpaceElevatorPart_2_C': 7.5,
                # building costs
                'Desc_Cable_C': 50,
                'Desc_ModularFrame_C': 20,
                'Desc_Motor_C': 10,
                'Desc_Plastic_C': 50,
            }),
            step_count=1,
            step_duration=1.0,
            unlocked_recipes=RecipeFlags({
                'Recipe_Alternate_FlexibleFramework_C',
            }),
        )
        problem = IterativeProductionProblem(problem_conf)
        code = problem.optimize()
        self.assertEqual(ReturnCode.INFEASIBLE_OR_UNBOUNDED, code)
        self.assertEqual(None, problem.objective_value)

    def test_produce_required_amount_only(self):
        problem_conf = IterativeProductionProblemConfig(
            S=ItemValues(),
            G=ItemValues({'Desc_Stone_C': 1.0}),
            step_count=1,
            step_duration=1.0,
            unlocked_recipes=RecipeFlags({'Recipe_HandcraftStone_C'}),
        )
        problem = IterativeProductionProblem(problem_conf)
        code = problem.optimize()
        self.assertEqual(ReturnCode.OPTIMAL, code)
        final_items = problem.get_items_in_stock(1)
        self.assertAlmostEqual(1.0, final_items['Desc_Stone_C'])


# Run the tests
if __name__ == '__main__':
    unittest.main()
