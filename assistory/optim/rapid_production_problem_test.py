import unittest
import sys, os

print('Add', os.getcwd(), 'to path')
sys.path.append(os.getcwd())
from assistory.game import ItemValues, RecipeFlags
from assistory.optim.static_flow_problem import ReturnCode
from assistory.optim.rapid_production_problem import RapidProductionProblem
from assistory.optim.rapid_production_problem_config import RapidProductionProblemConfig


# Create a test case class
class RapidProductionTest(unittest.TestCase):

    def setUp(self):
        self.unlocked_recipes = RecipeFlags({
                'Recipe_HandcraftOreIron_C',
                'Recipe_IngotIron_C',
                'Recipe_IronPlate_C',
                'Recipe_IronRod_C',
            })
        return super().setUp()

    def test_no_action_needed(self):
        problem_conf = RapidProductionProblemConfig(
            S=ItemValues({
                'Desc_OreIron_C': 10
            }),
            G=ItemValues({
                'Desc_OreIron_C': 10
            }),
            maximal_step_count=1,
            unlocked_recipes=self.unlocked_recipes,
        )
        problem = RapidProductionProblem(problem_conf)
        code = problem.optimize()
        self.assertEqual(code, ReturnCode.OPTIMAL)
        self.assertEqual(problem.objective_value, 0)
        problem.get_rapid_plan()

    def test_grow_production(self):
        problem_conf = RapidProductionProblemConfig(
            S = ItemValues({
                'Desc_OreIron_C': 10,
                'Desc_IronRod_C': 5,
                'Desc_Wire_C': 8
            }),
            G = ItemValues({
                'Desc_IronIngot_C': 10
            }),
            maximal_step_count=1,
            unlocked_recipes=self.unlocked_recipes,
        )
        problem = RapidProductionProblem(problem_conf)
        code = problem.optimize()
        self.assertEqual(code, ReturnCode.OPTIMAL)
        self.assertEqual(problem.objective_value, 1)
        problem.get_rapid_plan()


# Run the tests
if __name__ == '__main__':
    unittest.main()
