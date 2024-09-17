import unittest

import numpy as np

import rapid_production, utils, game

# Define the function to be tested
def f(x):
    return x * 2

# Create a test case class
class TestRapidProduction(unittest.TestCase):

    def test_no_action_needed(self):
        data_conf = rapid_production.GameDataConfiguration()
        S_items = {'Desc_OreIron_C': 10}
        G_items = {'Desc_OreIron_C': 10}
        E_recipes = {}
        start_conf = rapid_production.StartConfiguration(
            data_conf,
            S = np.array(utils.vectorize(S_items, game.ITEMS)),
            G = np.array(utils.vectorize(G_items, game.ITEMS)),
            E = np.array(utils.vectorize(E_recipes, game.RECIPES)))
        solver, values, minimal_steps = rapid_production.solve(data_conf, start_conf)
        self.assertEqual(minimal_steps, 0)

    def test_grow_production(self):
        data_conf = rapid_production.GameDataConfiguration()
        S_items = {'Desc_OreIron_C': 10, 'Desc_IronRod_C': 5, 'Desc_Wire_C': 8}
        G_items = {'Desc_IronIngot_C': 10}
        E_recipes = {}
        start_conf = rapid_production.StartConfiguration(
            data_conf,
            S = np.array(utils.vectorize(S_items, game.ITEMS)),
            G = np.array(utils.vectorize(G_items, game.ITEMS)),
            E = np.array(utils.vectorize(E_recipes, game.RECIPES)))
        solver, values, minimal_steps = rapid_production.solve(data_conf, start_conf)
        self.assertEqual(minimal_steps, 1)

# Run the tests
if __name__ == '__main__':
    unittest.main()
