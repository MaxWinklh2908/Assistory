import unittest
import sys, os

print('Add', os.getcwd(), 'to path')
sys.path.append(os.getcwd())
from assistory.game import ItemValues, RecipeValues
from assistory import game
from assistory.optim import static_flow_problem
from assistory.optim.static_flow_problem_config import StaticFlowLPConfig


class TestStaticFlowLPConfig(unittest.TestCase):
    
    def test_invalid_limits(self):
        valid_flow_conf = StaticFlowLPConfig(
            minimize_recipe_count=True,
            item_rate_balance_lower_limits=ItemValues({
                'Desc_Water_C': 1.0
            }),
            item_rate_balance_upper_limits=ItemValues({
                'Desc_Water_C': 2.0
            }),
        )
        invalid_flow_conf = StaticFlowLPConfig(
            minimize_recipe_count=True,
            item_rate_balance_lower_limits=ItemValues({
                'Desc_Water_C': 2.0
            }),
            item_rate_balance_upper_limits=ItemValues({
                'Desc_Water_C': 1.0
            }),
        )
        valid_flow_conf.check()
        with self.assertRaises(ValueError):
            invalid_flow_conf.check()


# Create a test case class
class TestStaticFlowLP(unittest.TestCase):
    
    def test_limited_recipe_count_optim_item_rate(self):
        all_recipes_zero = RecipeValues(omega=game.RECIPE_NAMES_AUTOMATED)
        # maximize
        flow_conf = StaticFlowLPConfig(
            maximize_item_rate_balance=True,
            recipe_count_upper_limits=all_recipes_zero,
            recipe_count_lower_limits=all_recipes_zero,
        )
        lp = static_flow_problem.StaticFlowLP(flow_conf)
        code = lp.optimize()
        self.assertEqual(static_flow_problem.ReturnCode.OPTIMAL, code)
        self.assertAlmostEqual(lp.objective_value, 0)

        # minimize
        flow_conf = StaticFlowLPConfig(
            minimize_item_rate_balance=True,
            recipe_count_upper_limits=all_recipes_zero,
            recipe_count_lower_limits=all_recipes_zero,
        )
        lp = static_flow_problem.StaticFlowLP(flow_conf)
        code = lp.optimize()
        self.assertEqual(static_flow_problem.ReturnCode.OPTIMAL, code)
        self.assertAlmostEqual(lp.objective_value, 0)

    def test_limited_recipe_count_max_recipe_count(self):
        recipe_count_limit = RecipeValues(omega=game.RECIPE_NAMES_AUTOMATED)
        recipe_count_limit['Recipe_AILimiter_C'] = 1.23
        base_item_rate = ItemValues({
            "Desc_CopperSheet_C": 500,
			"Desc_HighSpeedWire_C": 2000,
        })
        flow_conf = StaticFlowLPConfig(
            maximize_recipe_count=True,
            base_item_rate=base_item_rate,
            recipe_count_upper_limits=recipe_count_limit,
            recipe_count_lower_limits=recipe_count_limit,
        )
        lp = static_flow_problem.StaticFlowLP(flow_conf)
        code = lp.optimize()
        self.assertEqual(static_flow_problem.ReturnCode.OPTIMAL, code)
        self.assertAlmostEqual(lp.objective_value, 1.23)
        self.assertAlmostEqual(
            lp.get_recipes_used()['Recipe_AILimiter_C'],
            1.23
        )

    def test_limited_item_rate_max_item_rate(self):
        item_rate_balance_limit = ItemValues()
        item_rate_balance_limit['Desc_Water_C'] = 1.23
        flow_conf = StaticFlowLPConfig(
            maximize_item_rate_balance=True,
            item_rate_balance_lower_limits=item_rate_balance_limit,
            item_rate_balance_upper_limits=item_rate_balance_limit,
        )
        lp = static_flow_problem.StaticFlowLP(flow_conf)
        code = lp.optimize()
        self.assertEqual(static_flow_problem.ReturnCode.OPTIMAL, code)
        self.assertAlmostEqual(lp.objective_value, 1.23)
        self.assertAlmostEqual(
            lp.get_item_rate_balance()['Desc_Water_C'],
            1.23
        )

    def test_limited_item_rate_max_recipe_count_unbound(self):
        items_one = ItemValues()
        items_one.set_values(1)
        flow_conf = StaticFlowLPConfig(
            maximize_recipe_count=True,
            item_rate_balance_upper_limits=items_one,
        )
        lp = static_flow_problem.StaticFlowLP(flow_conf)
        code = lp.optimize()
        # for example packager can create zero balance production
        self.assertEqual(static_flow_problem.ReturnCode.INFEASIBLE_OR_UNBOUNDED, code)

    def test_limited_item_rate_optim_recipe_count(self):
        recipe_count_limit = RecipeValues(omega=game.RECIPE_NAMES_AUTOMATED)
        recipe_count_limit.set_values(1.23)
        flow_conf = StaticFlowLPConfig(
            maximize_recipe_count=True,
            item_rate_balance_upper_limits=ItemValues(),
            recipe_count_upper_limits=recipe_count_limit,
        )
        lp = static_flow_problem.StaticFlowLP(flow_conf)
        code = lp.optimize()
        self.assertEqual(static_flow_problem.ReturnCode.OPTIMAL, code)


# Run the tests
if __name__ == '__main__':
    unittest.main()
