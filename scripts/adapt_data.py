from argparse import ArgumentParser
import json
import os

DATA_PATH_EXPORT = os.path.join(os.path.dirname(__file__), '../data/data.json')

# exclude fracking smasher (simplify using fracking extractor only)
BUILDINGS_WHITELIST = [
    'Desc_AssemblerMk1_C',
    'Desc_Blender_C',
    'Desc_ConstructorMk1_C',
    'Desc_Converter_C',
    'Desc_FoundryMk1_C',
    'Desc_FrackingExtractor_C',
    'Desc_GeneratorBiomass_Automated_C',
    'Desc_GeneratorCoal_C',
    'Desc_GeneratorFuel_C',
    'Desc_GeneratorGeoThermal_C',
    'Desc_GeneratorNuclear_C',
    'Desc_HadronCollider_C',
    'Desc_ManufacturerMk1_C',
    'Desc_MinerMk1_C',
    'Desc_MinerMk2_C',
    'Desc_MinerMk3_C',
    'Desc_OilPump_C',
    'Desc_OilRefinery_C',
    'Desc_Packager_C',
    'Desc_QuantumEncoder_C',
    'Desc_SmelterMk1_C',
    'Desc_WaterPump_C'
]

parser = ArgumentParser()
parser.add_argument('data_path_import', help='')
args = parser.parse_args()
data_path_import = args.data_path_import

with open(data_path_import, 'r') as fp:
    data = json.load(fp)

# Extend data with manually defined entries
with open('data/extension_data.json', 'r') as fp:
    extension_data = json.load(fp)
for group_key, extension_group in extension_data.items():
    for extension_key, extension in extension_group.items():
        data[group_key][extension_key] = extension


# Simplification: required energy for smasher is integrated into extractors to
# simplify modelling
# calculated manually using satisfactory-calculator.com
average_number_satellites_per_smasher = 6.941
fracking_smasher = data['buildings']['Desc_FrackingSmasher_C']
power_fracking_smasher = fracking_smasher['metadata']['powerConsumption']
fracking_extractor = data['buildings']['Desc_FrackingExtractor_C']
# TODO: Additional resources for smasher
fracking_extractor['metadata']['powerConsumption'] += (
    power_fracking_smasher/average_number_satellites_per_smasher)

# overwrite generators with negative power consumption
for building_name, generator in data['generators'].items():
    building = data['buildings'][building_name]
    building['metadata']['powerConsumption'] = -generator['powerProduction']

# ignore all buildings not on the white list
for building_name in set(data['buildings']):
    if not building_name in BUILDINGS_WHITELIST:
        data['buildings'].pop(building_name)

# move ingredients for buildings from recipes to building costs
single_product2recipe_name = {
    recipe['products'][0]['item']: recipe
    for recipe in data['recipes'].values()
    if len(recipe['products']) == 1
}
for building_name in data['buildings']:
    building = data['buildings'][building_name]
    ingredients = single_product2recipe_name[building_name]['ingredients']
    building['costs'] = ingredients

# reject all recipes for buildings
for recipe_name in set(data['recipes']):
    if data['recipes'][recipe_name]['forBuilding']:
        data['recipes'].pop(recipe_name)

def get_bare_item_name(name: str) -> str:
    # remove _C
    name = name[:-2]
    # remove prefix
    name = '_'.join(name.split('_')[1:])
    return name

def create_machine_recipe(recipe_name: str, ingredients: list,
                          products: list, time: float, building_name: str):
    return {
        'name': get_bare_item_name(recipe_name),
        'className': recipe_name,
        'alternate': False,
        'time': time,
        'ingredients': ingredients,
        'forBuilding': False,
        'inMachine': True,
        'inHand': False,
        'inWorkshop': False,
        'products': products,
        'producedIn': [building_name],
        'isVariablePower': False,
    }

# calculate required ingregients based on item energy value
def calc_input_rate(generator: dict, fuel_name: dict) -> float:
    fuel = data['items'][fuel_name]
    power_production = generator['powerProduction']
    energy_value = fuel['energyValue']
    if energy_value == 0:
        raise ValueError('Fuel has no energy: ' + fuel['className'])
    # TODO: consistent use of liquid unit (recipes: m^3, item stack: liters)
    if fuel['liquid']:
        energy_value *= 1000
    # calculate required ingregients based on item energy value
    return power_production / energy_value * 60
# Power: For every generator and fuel add a recipe
for generator_name, generator in data['generators'].items():
    if generator_name == 'Desc_GeneratorGeoThermal_C':
        # empty recipe enables usage in parsing and sink point optim
        recipe_name = (f'Recipe_{get_bare_item_name(generator_name)}Power_C')
        data['recipes'][recipe_name] = create_machine_recipe(recipe_name, [], [],
                                                             60, generator_name)
        continue
    water_consumption = generator['waterToPowerRatio'] * generator['powerProduction']
    for fuel in generator['fuels']:
        fuel_name = fuel['item']
        input_rate = calc_input_rate(generator, fuel_name)
        ingredients = [{'item': fuel_name,
                       'amount': input_rate}]

        if fuel['supplementalItem']:
            ingredients.append({
                'item': fuel['supplementalItem'],
                'amount': water_consumption})

        byproduct_name = fuel['byproduct']
        if byproduct_name:
            products = [{'item': byproduct_name,
                        'amount': fuel['byproductAmount']}]
        else:
            products = dict()

        recipe_name = (f'Recipe_{get_bare_item_name(generator_name)}'
                        f'{get_bare_item_name(fuel_name)}_C')
        data['recipes'][recipe_name] = create_machine_recipe(recipe_name,
                                                             ingredients,
                                                             products,
                                                             60, generator_name)

# Extraction: For every building and every resource add a recipe
for extractor_build_name, extractor in data['miners'].items():
    
    for item_name in extractor['allowedResources']:
        recipe_name = ('Recipe_' + get_bare_item_name(extractor_build_name)
                       + get_bare_item_name(item_name) + '_C')
        products = [{'item': item_name,
                    'amount': extractor['itemsPerCycle']}]
        cycle_time = extractor['extractCycleTime']
        
        building_name = extractor_build_name.replace('Build_', 'Desc_')
        data['recipes'][recipe_name] = create_machine_recipe(recipe_name, [], products,
                                                             cycle_time, building_name)

def create_handcraft_recipe(recipe_name: str, ingredients: list,
                          products: list, time: float):
    return {
        'name': get_bare_item_name(recipe_name),
        'className': recipe_name,
        'alternate': False,
        'time': time,
        'ingredients': ingredients,
        'forBuilding': False,
        'inMachine': False,
        'inHand': True,
        'inWorkshop': False,
        'products': products,
        'producedIn': [],
        'isVariablePower': False,
    }

# Handcraft extraction: Every solid resource can be collected or mined manually
for item_name, resource in data['resources'].items():
    if data['items'][item_name]['liquid']:
        continue
    recipe_name = f'Recipe_Handcraft{get_bare_item_name(item_name)}_C'
    products = [{'item': item_name, 'amount': 1}]
    data['recipes'][recipe_name] = create_handcraft_recipe(
        recipe_name, [], products, resource['speed'])


with open(DATA_PATH_EXPORT, 'w') as fp:
    json.dump(data, fp, indent='\t')
