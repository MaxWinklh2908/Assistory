from argparse import ArgumentParser


from assistory.game import game
from assistory.utils import utils
from assistory.optim.sink_point_optim import SatisfactoryLP

def main(recipe_export_path: str):

    ################# recipes ######################
    # recipes=game.RECIPES

    recipes = {
        recipe_name: recipe for
        recipe_name, recipe in game.RECIPES.items()
        if not recipe_name in game.RECIPES_ALTERNATE
    }

    # recipes=dict()
    # recipes['Recipe_IngotIron_C'] = game.RECIPES['Recipe_IngotIron_C']
    # recipes['Recipe_IngotCopper_C'] = game.RECIPES['Recipe_IngotCopper_C']
    # recipes['Recipe_WaterExtractorWater_C'] = game.RECIPES['Recipe_WaterExtractorWater_C']
    # recipes['Recipe_Alternate_SteamedCopperSheet_C'] = game.RECIPES['Recipe_Alternate_SteamedCopperSheet_C']

    ################# items available ######################
    items_available = dict()

    # # custom
    # items_available['Desc_OreIron_C'] = 240
    # items_available['Desc_OreCopper_C'] = 120
    # # items_available['Desc_Coal_C'] = 240
    # items_available['Desc_Stone_C'] = 120
    
    # current production (state: rework black lake oil)
    # items_available = {
    #     item_name: amount
    #     for item_name, amount
    #     in utils.parse_items('data/Autonation4.0_production_state.csv').items()
    # }

    ################# resource nodes available ######################
    resource_nodes_available = {item_name: 0 for item_name in game.NODE_RECIPES_AVAILABLE}
    resource_nodes_available['Recipe_MinerMk1OreIron_C'] = 4
    resource_nodes_available['Recipe_MinerMk1OreCopper_C'] = 2
    resource_nodes_available['Recipe_MinerMk1Stone_C'] = 2
    resource_nodes_available['Recipe_GeneratorGeoThermalPower_C'] = 2

    # resource_nodes_available = game.NODE_RECIPES_AVAILABLE
    
    # Current coverage (state: CO2-Neutral)
    # resource_nodes_available = utils.read_resource_nodes(
    #   'data/available_nodes_autonation.json',
    #   set(game.NODE_RECIPES_AVAILABLE))
    # resource_nodes_available = utils.read_resource_nodes(
    #   'data/available_nodes_black_lake_oil.json',
    #   set(game.NODE_RECIPES_AVAILABLE))

    # TODO: read resource nodes available (including geotermal (former free power))
    # from safe file

    ################# define problem ######################

    problem = SatisfactoryLP(recipes=recipes,
                             items_available=items_available,
                             resource_nodes_available=resource_nodes_available,
                             free_power=0)

    ################# constraints ######################
    # sell_rates = dict()

    # Goal: Produce at least 1 item of every kind (except impractical items)
    # sell_rates = {
    #     item_name: 1 for item_name in problem.get_producable_items()
    #     if not item_name in game.ITEMS_NON_SELLABLE
    #     and not item_name in game.ITEMS_RADIOACTIVE
    #     and not item_name in game.ITEMS_EXTRACTION
    #     and not 'Ingot' in item_name
    # }

    # Goal: Make black lake oil more efficient
    # sell_rates['Desc_CircuitBoard_C'] = 68 # 50 + 4 + 5 + 3.4643
    # sell_rates['Desc_Fabric_C'] = 1.85 + 3.15
    # sell_rates['Desc_Fuel_C'] = 1
    # sell_rates['Desc_Plastic_C'] = 210 - 18 + 4 + 25.46
    # sell_rates['Desc_PolymerResin_C'] = 2.5 + 48.9
    # sell_rates['Desc_Rubber_C'] = 160 + 50 # 48.17
    
    # problem.define_sell_rates(sell_rates)

    problem._define_non_sellable_items()

    ################# objective ######################

    # problem.set_objective_max_sink_points()
    # problem.set_objective_min_resources_spent(weighted=True)
    # problem.set_objective_min_recipes()
    problem.set_objective_max_item_rate('Desc_SpaceElevatorPart_1_C')
    
    ################# Solve ######################

    print("Number of variables =", problem.solver.NumVariables())
    print("Number of constraints =", problem.solver.NumConstraints())

    status = problem.optimize()
    if status != 0: # pywraplp.Solver.OPTIMAL
        print("The problem does not have an optimal solution:", status)
        exit(1)

    problem.report()
    # problem.report_shadow_prices()

    utils.write_result(problem.get_recipes_used(),
                       problem.get_items_sold(),
                       items_available,
                       recipe_export_path)
    

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('recipe_export_path', help='Output path to the production plan'
                        ', i.e. recipe amounts by recipe name')
    args = parser.parse_args()

    main(args.recipe_export_path)
