import json

with open('data.json', 'r') as fp:
    data = json.load(fp)

def get_bare_item_name(name: str) -> str:
    # remove _C
    name = name[:-2]
    # remove prefix
    name = '_'.join(name.split('_')[1:])
    return name


def define_production_facilities():
    facilities = {
        building_name: -values['metadata']['powerConsumption']
        for building_name, values in data['buildings'].items()
        if 'SC_Smelters_C' in values['categories'] or
        'SC_Manufacturers_C' in values['categories']
    }

    # Biomass burner is not automatable
    facilities['Desc_GeneratorCoal_C'] = 75
    facilities['Desc_GeneratorFuel_C'] = 150
    # Geisirs are implemented as free energy
    facilities['Desc_GeneratorNuclear_C'] = 2500

    facilities['Desc_MinerMk1_C'] = -5
    facilities['Desc_MinerMk2_C'] = -12
    facilities['Desc_MinerMk3_C'] = -30
    facilities['Desc_WaterExtractor_C'] = -20
    facilities['Desc_OilExtractor_C'] = -40
    # TODO: correctly estimate pressurizer power
    facilities['Desc_ResourceWellPressurizer_C'] = -10
    
    return facilities
# Mapping of production facility to power production/consumption
PRODUCTION_FACILITIES = define_production_facilities()
# Note: over/underclocking would make the problem non-linear

MINING_FACILITIES = [
    'Desc_MinerMk1_C',
    'Desc_MinerMk2_C',
    'Desc_MinerMk3_C',
    'Desc_WaterExtractor_C',
    'Desc_OilExtractor_C',
    'Desc_ResourceWellPressurizer_C'
]

# Geothermal power production is not consuming resources, therefore free
FREE_POWER = 3*100 + 9*200 + 6*400


def define_items() -> dict:
    return {
        item_name:v for item_name,v in data['items'].items()
        if (
            not 'special__' in item_name and
            type(v['sinkPoints']) == int
        )    
    }
ITEMS = define_items()

def define_non_sellable_items() -> list:
    return [
        item_name
        for item_name, item_data in ITEMS.items()
        if item_data['sinkPoints'] == 0
        or item_data['liquid']
    ]
NON_SELLABLE_ITEMS = define_non_sellable_items()

def define_radioactive_items() -> list:
    return [
        item_name
        for item_name, item_data in ITEMS.items()
        if item_data['radioactiveDecay'] > 0
    ]
RADIOACTIVE_ITEMS = define_radioactive_items()

def define_liquid_items() -> list:
    return [
        item_name
        for item_name, item_data in ITEMS.items()
        if item_data['liquid']
    ]
LIQUID_ITEMS = define_liquid_items()

# mining, resource wells and oil and water extractor
ITEMS_FROM_MINING = [
    'Desc_LiquidOil_C',
    'Desc_Stone_C',
    'Desc_OreIron_C',
    'Desc_OreCopper_C',
    'Desc_OreGold_C',
    'Desc_Coal_C',
    'Desc_Sulfur_C',
    'Desc_OreBauxite_C',
    'Desc_RawQuartz_C',
    'Desc_OreUranium_C',
    'Desc_NitrogenGas_C',
]

# pure nodes have double rate, impure nodes have half rate
NODES_AVAILABLE = dict()
NODES_AVAILABLE['Recipe_MinerMk3Stone_C'] =                       (2 * 27 + 47 + 0.5 * 12)
NODES_AVAILABLE['Recipe_MinerMk3OreIron_C'] =                     (2 * 46 + 41 + 0.5 * 33)
NODES_AVAILABLE['Recipe_MinerMk3OreCopper_C'] =                   (2 * 12 + 28 + 0.5 * 9)
NODES_AVAILABLE['Recipe_MinerMk3OreGold_C'] =                     (2 * 8 + 8 + 0.5 * 0)
NODES_AVAILABLE['Recipe_MinerMk3Coal_C'] =                        (2 * 14 + 29 + 0.5 * 6)
NODES_AVAILABLE['Recipe_MinerMk3Sulfur_C'] =                      (2 * 3 + 7 + 0.5 * 1)
NODES_AVAILABLE['Recipe_MinerMk3OreBauxite_C'] =                  (2 * 6 + 6 + 0.5 * 5)
NODES_AVAILABLE['Recipe_MinerMk3RawQuartz_C'] =                   (2 * 5 + 11 + 0.5 * 0)
NODES_AVAILABLE['Recipe_MinerMk3OreUranium_C'] =                  (2 * 0 + 3 + 0.5 * 1)
NODES_AVAILABLE['Recipe_OilExtractorLiquidOil_C'] =               (2 * 8 + 12 + 0.5 * 10)
NODES_AVAILABLE['Recipe_ResourceWellPressurizerNitrogenGas_C'] =  (2 * 36 + 7 + 0.5 * 2)
NODES_AVAILABLE['Recipe_ResourceWellPressurizerLiquidOil_C'] =    (2 * 3 + 3 + 0.5 * 6)

def define_recipes():
    def transform_to_dict(items: list):
        return {
            d['item']: d['amount']
            for d in items
        }
    recipes = dict()
    for recipe_name, v in data['recipes'].items():
        
        if not set(v['producedIn']).intersection(set(PRODUCTION_FACILITIES)):
            if v['inWorkshop'] or v['inHand']:
                print('WARNING Skip handcrafted:', recipe_name)
            continue
        if len(v['producedIn']) != 1:
            raise ValueError('Invalid number of production facilities: ' + recipe_name)
        ingredients = {
            item_name: amount
            for item_name, amount in transform_to_dict(v['ingredients']).items()
            if item_name in ITEMS
        }
        products = {
            item_name: amount
            for item_name, amount in transform_to_dict(v['products']).items()
            if item_name in ITEMS
        }
        if not ingredients or not products:
            print('WARNING Skip unavailable:', recipe_name)
            continue
        if len(ingredients) != len(v['ingredients']) or len(products) != len(v['products']):
            print('WARNING Reduced:', recipe_name)
        recipes[recipe_name] = {
            'ingredients': ingredients,
            'products': products,
            'producedIn': v['producedIn'][0],
            'time': v['time'],
        }
    # Nuclear production chain
    recipes['Recipe_GeneratorNuclearUranium_C'] = {
        'ingredients': {'Desc_NuclearFuelRod_C': 1, 'Desc_Water_C': 240*5},
        'products': {'Desc_NuclearWaste_C': 50},
        'producedIn': 'Desc_GeneratorNuclear_C',
        'time': 300,
    }
    recipes['Recipe_GeneratorNuclearPlutonium_C'] = {
        'ingredients': {'Desc_PlutoniumFuelRod_C': 1, 'Desc_Water_C': 240*10},
        'products': {'Desc_PlutoniumWaste_C': 10},
        'producedIn': 'Desc_GeneratorNuclear_C',
        'time': 600,
    }
    # Power from coal
    recipes['Recipe_GeneratorCoalCoal_C'] = {
        
        'ingredients': {'Desc_Coal_C': 15, 'Desc_Water_C': 45},
        'products': {},
        'producedIn': 'Desc_GeneratorCoal_C',
        'time': 60,
    }
    recipes['Recipe_GeneratorCoalCompactedCoal_C'] = {
        
        'ingredients': {'Desc_CompactedCoal_C': 7.142857, 'Desc_Water_C': 45},
        'products': {},
        'producedIn': 'Desc_GeneratorCoal_C',
        'time': 60,
    }
    recipes['Recipe_GeneratorCoalPetroleumCoke_C'] = {
        
        'ingredients': {'Desc_PetroleumCoke_C': 25, 'Desc_Water_C': 45},
        'products': {},
        'producedIn': 'Desc_GeneratorCoal_C',
        'time': 60,
    }
    # Power from fuel
    recipes[f'Recipe_GeneratorFuelLiquidFuel_C'] = {
        'ingredients': {'Desc_LiquidFuel_C': 12},
        'products': {},
        'producedIn': 'Desc_GeneratorFuel_C',
        'time': 60,
    }
    recipes[f'Recipe_GeneratorFuelLiquidBiofuelFuel_C'] = {
        'ingredients': {'Desc_LiquidBiofuel_C': 12},
        'products': {},
        'producedIn': 'Desc_GeneratorFuel_C',
        'time': 60,
    }
    recipes[f'Recipe_GeneratorFuelLiquidTurboFuel_C'] = {
        'ingredients': {'Desc_LiquidTurboFuel_C': 4.5},
        'products': {},
        'producedIn': 'Desc_GeneratorFuel_C',
        'time': 60,
    }
    # Water Extractor
    recipes['Recipe_WaterExtractorWater_C'] = {
        
        'ingredients': {},
        'products': {'Desc_Water_C': 120},
        'producedIn': 'Desc_WaterExtractor_C',
        'time': 60,
    }
    # Oil extractor
    recipes['Recipe_OilExtractorLiquidOil_C'] = {
        'ingredients': {},
        'products': {'Desc_LiquidOil_C': 120},
        'producedIn': 'Desc_OilExtractor_C',
        'time': 60,
    }
    # Add miners
    # TODO: How to handle Mk1 and Mk2?
    for item_name in [
        'Desc_Stone_C',
        'Desc_OreIron_C',
        'Desc_OreCopper_C',
        'Desc_OreGold_C',
        'Desc_Coal_C',
        'Desc_Sulfur_C',
        'Desc_OreBauxite_C',
        'Desc_RawQuartz_C',
        'Desc_OreUranium_C',
    ]:
        recipes[f'Recipe_MinerMk3{get_bare_item_name(item_name)}_C'] = {
            'ingredients': {},
            'products': {item_name: 240},
            'producedIn': 'Desc_MinerMk3_C',
            'time': 60,
        }
    # Resource wells
    for item_name in [
        'Desc_NitrogenGas_C',
        'Desc_LiquidOil_C',
    ]:
        recipes[f'Recipe_ResourceWellPressurizer{get_bare_item_name(item_name)}_C'] = {
            'ingredients': {},
            'products': {item_name: 60},
            'producedIn': 'Desc_ResourceWellPressurizer_C',
            'time': 60,
        }
    return recipes
# recipies define ingredients, products, production facility and production time
RECIPES = define_recipes()

# helper structure to find recipes
def define_item_to_recipe_mappings():
    consumed_by = { item_name: [] for item_name in ITEMS}
    produced_by = { item_name: [] for item_name in ITEMS}
    for recipe_name, data in RECIPES.items():
        for item_name in data['ingredients']:
            consumed_by[item_name].append(recipe_name)
        for item_name in data['products']:
            produced_by[item_name].append(recipe_name)
    return consumed_by, produced_by
consumed_by, produced_by = define_item_to_recipe_mappings()
