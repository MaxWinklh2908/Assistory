import json
import itertools

with open('data/data.json', 'r') as fp:
    data = json.load(fp)
with open('data/resource_nodes.json', 'r') as fp:
    resource_node_data = json.load(fp)

def get_bare_item_name(name: str) -> str:
    # remove _C
    name = name[:-2]
    # remove prefix
    name = '_'.join(name.split('_')[1:])
    return name


def transform_to_dict(items: list):
        return {
            d['item']: d['amount']
            for d in items
        }

def define_buildings():
    facilities = {
        building_name: {
            'power_consumption': vals['metadata']['powerConsumption'],
            'costs': transform_to_dict(vals['costs'])
        }
        for building_name, vals in data['buildings'].items()
    }
    # check negative power of generators
    for building_name, vals in data['buildings'].items():
        power = vals['metadata']['powerConsumption']
        if 'Generator' in building_name and power >= 0:
            raise ValueError(f'There is probably a mistake, as {building_name}'
                             f' has powerConsumption {power} (should be < 0)')
    return facilities
# Mapping of building name to power consumption and costs
# Buildings consume and produce power and items
BUILDINGS = define_buildings()
# Note: over/underclocking would make the problem non-linear

BUILDINGS_EXTRACTION = [
    'Desc_MinerMk1_C',
    'Desc_MinerMk2_C',
    'Desc_MinerMk3_C',
    'Desc_WaterPump_C',
    'Desc_OilPump_C',
    'Desc_FrackingExtractor_C'
]

def define_items() -> dict:
    return {
        item_name:v for item_name,v in data['items'].items()
    }
ITEMS = define_items()

def define_non_sellable_items() -> list:
    return [
        item_name
        for item_name, item_data in ITEMS.items()
        if item_data['sinkPoints'] == 0
        or item_data['liquid']
    ]
ITEMS_NON_SELLABLE = define_non_sellable_items()

def define_radioactive_items() -> list:
    return [
        item_name
        for item_name, item_data in ITEMS.items()
        if item_data['radioactiveDecay'] > 0
    ]
ITEMS_RADIOACTIVE = define_radioactive_items()

def define_liquid_items() -> list:
    return [
        item_name
        for item_name, item_data in ITEMS.items()
        if item_data['liquid']
    ]
ITEMS_LIQUID = define_liquid_items()

def define_items_extraction():
    return list(data['resources'].keys())
ITEMS_EXTRACTION = define_items_extraction()

def define_node_recipes_available():
    node_recipes_available = dict()

    # initialize by 0
    def item_mining_to_node_name(item_name, level):
        return f'Recipe_MinerMk{level}{get_bare_item_name(item_name)}_C'
    items_mining = [
            'Desc_Stone_C',
            'Desc_OreIron_C',
            'Desc_OreCopper_C',
            'Desc_OreGold_C',
            'Desc_Coal_C',
            'Desc_Sulfur_C',
            'Desc_OreBauxite_C',
            'Desc_RawQuartz_C',
            'Desc_OreUranium_C',
            'Desc_SAM_C'
        ]
    for item_name, level in itertools.product(items_mining, (1, 2, 3)):
        node_name = item_mining_to_node_name(item_name, level)
        node_recipes_available[node_name] = 0
    # Water can be produced without limits and is therefore excluded
    node_recipes_available['Recipe_GeneratorGeoThermalPower_C'] = 0
    node_recipes_available['Recipe_OilPumpLiquidOil_C'] = 0
    node_recipes_available['Recipe_FrackingExtractorNitrogenGas_C'] = 0
    node_recipes_available['Recipe_FrackingExtractorLiquidOil_C'] = 0

    # fill from data
    def item_name_to_node_name(node: dict):
        if node['resource'] in items_mining:
            # By default use only MinerMk3
            return item_mining_to_node_name(node['resource'], 3)
        elif node['resource'] == 'Desc_NitrogenGas_C':
            return 'Recipe_FrackingExtractorNitrogenGas_C'
        elif node['resource'] == 'Desc_LiquidOil_C':
            if node['fracking']:
                return 'Recipe_FrackingExtractorLiquidOil_C'
            else:
                return 'Recipe_OilPumpLiquidOil_C'
        elif node['resource'] == 'special__power':
            return 'Recipe_GeneratorGeoThermalPower_C'
        else:
            raise ValueError('Unknown mapping ' + str(node['resource']))
    for node in resource_node_data.values():
        node_name = item_name_to_node_name(node)
        # pure nodes have double rate, impure nodes have half rate
        if node['purity'] == 'impure':
            node_recipes_available[node_name] += 0.5
        elif node['purity'] == 'normal':
            node_recipes_available[node_name] += 1
        elif node['purity'] == 'pure':
            node_recipes_available[node_name] += 2
        else:
            raise ValueError('Unknown purity: ' + node['purity'])

    return node_recipes_available
NODE_RECIPES_AVAILABLE = define_node_recipes_available()

# recipes in buildings
def define_recipes():
    recipes = dict()
    for recipe_name, v in data['recipes'].items():
        if len(v['producedIn']) == 0:
            continue
        elif len(v['producedIn']) > 1:
            raise ValueError('Expect at most one production facilities. Got: ' + recipe_name)
        produced_in = v['producedIn'][0]
        if not produced_in in BUILDINGS:
            raise ValueError('Unknown building:', produced_in)
        
        ingredients = {
            item_name: amount
            for item_name, amount in transform_to_dict(v['ingredients']).items()
        }
        if not all(item_name in ITEMS for item_name in ingredients):
            raise ValueError('Unknown items in ' + str(ingredients.keys()))
        
        products = {
            item_name: amount
            for item_name, amount in transform_to_dict(v['products']).items()
        }
        if not all(item_name in ITEMS for item_name in products):
            raise ValueError('Unknown items in ' + str(products.keys()))

        recipes[recipe_name] = {
            'ingredients': ingredients,
            'products': products,
            'producedIn': produced_in,
            'time': v['time'],
        }

    return recipes
# recipies define ingredients, products, production facility and production time
RECIPES = define_recipes()

def define_recipes_alternate() -> list:
    return [
        recipe_name
        for recipe_name in RECIPES
        if data['recipes'][recipe_name]['alternate']
    ]
RECIPES_ALTERNATE = define_recipes_alternate()

def define_recipes_handcraft():
    recipes = dict()
    for recipe_name, v in data['recipes'].items():
        if not v['inWorkshop'] and not v['inHand']:
            continue
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
        if len(ingredients) != len(v['ingredients']) or len(products) != len(v['products']):
            print('WARNING Reduced:', recipe_name)
        recipes[recipe_name] = {
            'ingredients': ingredients,
            'products': products,
            'time': v['time'],
        }

    return recipes
# recipies define ingredients, products, production facility and production time
RECIPES_HANDCRAFT = define_recipes_handcraft()

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

def define_schematics():
    schematics = dict()
    for schematic_name, v in data['schematics'].items():
        cost = {
            item_name: amount
            for item_name, amount in transform_to_dict(v['cost']).items()
            if item_name in ITEMS
        }
        schematics[schematic_name] = {
            'className': v['className'],
            'name': v['name'],
            'cost': cost,
        }
    return schematics
SCHEMATICS = define_schematics()
