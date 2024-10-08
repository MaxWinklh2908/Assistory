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
        optim_conf = rapid_production.OptimizationConfiguration(n=1)
        solver, values, minimal_steps = rapid_production.solve_with_binary_search(
            data_conf, start_conf, optim_conf)
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
        optim_conf = rapid_production.OptimizationConfiguration(n=1)
        solver, values, minimal_steps = rapid_production.solve_with_binary_search(
            data_conf, start_conf, optim_conf)
        self.assertEqual(minimal_steps, 1)

    def test_fix_balance(self):
        # Possibly there are imbalances in the item production that to optimization need to fix
        data_conf = rapid_production.GameDataConfiguration()
        S_items = {'Desc_Cement_C': 20,
                   'Desc_Cable_C': 8,
                   'Desc_IronPlate_C': 20,
                   'Desc_IronPlateReinforced_C': 2}
        G_items = {'Desc_OreIron_C': 30}
        E_recipes = {'Recipe_Concrete_C': 1.0}
        start_conf = rapid_production.StartConfiguration(
            data_conf,
            S = np.array(utils.vectorize(S_items, game.ITEMS)),
            G = np.array(utils.vectorize(G_items, game.ITEMS)),
            E = np.array(utils.vectorize(E_recipes, game.RECIPES)))
        start_conf.validate() # assert no exception
        optim_conf = rapid_production.OptimizationConfiguration(n=1)
        solver, values, minimal_steps = rapid_production.solve_with_binary_search(
            data_conf, start_conf, optim_conf)
        self.assertEqual(minimal_steps, 1)


class TestStartConfiguration(unittest.TestCase):

    def test_validation_goal_items(self):
        data_conf = rapid_production.GameDataConfiguration()
        S_items = {'Desc_OreIron_C': 10, 'Desc_IronRod_C': 5, 'Desc_Wire_C': 8}
        G_items = {'Desc_GenericBiomass_C': 1}
        E_recipes = {}
        start_conf = rapid_production.StartConfiguration(
            data_conf,
            S = np.array(utils.vectorize(S_items, game.ITEMS)),
            G = np.array(utils.vectorize(G_items, game.ITEMS)),
            E = np.array(utils.vectorize(E_recipes, game.RECIPES)))
        self.assertRaises(RuntimeError, start_conf.validate)

        data_conf = rapid_production.GameDataConfiguration()
        S_items = {'Desc_OreIron_C': 10, 'Desc_IronRod_C': 5, 'Desc_Wire_C': 8}
        G_items = {'Desc_IronRod_C': 10}
        E_recipes = {}
        start_conf = rapid_production.StartConfiguration(
            data_conf,
            S = np.array(utils.vectorize(S_items, game.ITEMS)),
            G = np.array(utils.vectorize(G_items, game.ITEMS)),
            E = np.array(utils.vectorize(E_recipes, game.RECIPES)))
        start_conf.validate() # assert no exception

    def test_validation_recipes(self):
        data_conf = rapid_production.GameDataConfiguration()
        S_items = {'Desc_OreIron_C': 10, 'Desc_IronRod_C': 5, 'Desc_Wire_C': 8}
        G_items = {'Desc_IronRod_C': 10}
        E_recipes = {'Recipe_Biofuel_C': 1}
        start_conf = rapid_production.StartConfiguration(
            data_conf,
            S = np.array(utils.vectorize(S_items, game.ITEMS)),
            G = np.array(utils.vectorize(G_items, game.ITEMS)),
            E = np.array(utils.vectorize(E_recipes, game.RECIPES)))
        self.assertRaises(RuntimeError, start_conf.validate)


# Run the tests
if __name__ == '__main__':
    unittest.main()
