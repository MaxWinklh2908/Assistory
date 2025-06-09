from argparse import ArgumentParser
import json
import os

DATA_PATH_EXPORT = os.path.join(os.path.dirname(__file__), '../data/data.json')

# exclude fracking smasher (simplify using fracking extractor only)
# Handle Desc_GeneratorIntegratedBiomass_C as Desc_GeneratorBiomass_Automated_C
BUILDINGS_WHITELIST = [
    'Desc_AssemblerMk1_C',
    'Desc_AlienPowerBuilding_C',
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
BUILDINGS_EXTRACTION = [
    'Desc_MinerMk1_C',
    'Desc_MinerMk2_C',
    'Desc_MinerMk3_C',
    'Desc_WaterPump_C',
    'Desc_OilPump_C',
    'Desc_FrackingExtractor_C'
]
BUILDINGS_GENERATOR = [
    'Desc_GeneratorBiomass_Automated_C',
    'Desc_GeneratorCoal_C',
    'Desc_GeneratorFuel_C',
    'Desc_GeneratorGeoThermal_C',
    'Desc_GeneratorNuclear_C'
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

# drop description data
for item_name in data['items']:
    data['items'][item_name].pop('description', None)
for building_name in data['buildings']:
    data['buildings'][building_name].pop('description', None)

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
buildings_ignored = 0
for building_name in set(data['buildings']):
    if not building_name in BUILDINGS_WHITELIST:
        data['buildings'].pop(building_name)
        buildings_ignored += 1
print('Ignored buildings:', buildings_ignored)

# copy ingredients for buildings from recipes to building costs
single_product2recipe_name = {
    recipe['products'][0]['item']: recipe
    for recipe in data['recipes'].values()
    if len(recipe['products']) == 1
}
for building_name in data['buildings']:
    building = data['buildings'][building_name]
    ingredients = single_product2recipe_name[building_name]['ingredients']
    building['costs'] = ingredients

# reject all recipes for buildings except from buildings for production
PRODUCTION_BUILDING_RECIPES = dict()
for recipe_name in set(data['recipes']):
    recipe = data['recipes'][recipe_name]
    if recipe['forBuilding']:
        recipe = data['recipes'].pop(recipe_name)
        if len(recipe['products']) != 1:
            raise ValueError('Expect exactly 1 building as product')
        building_name = recipe['products'][0]['item']
        if building_name in BUILDINGS_WHITELIST:
            PRODUCTION_BUILDING_RECIPES[recipe_name] = building_name

# Filter unknown items
known_items = set(data['items'])
def filter_item_amounts(item_amounts: list) -> list:
    return [
        vals
        for vals in item_amounts
        if vals['item'] in known_items
    ]
for schematics_name, schematic in data['schematics'].items():
    # filter schematic costs
    costs = filter_item_amounts(schematic['cost'])
    if len(costs) != len(schematic['cost']):
        print(f'INFO Removed unknown item(s) in costs of schematic {schematics_name}')
    schematic['cost'] = costs
    # filter schematic given items
    given_items = filter_item_amounts(schematic['unlock']['giveItems'])
    if len(given_items) != len(schematic['unlock']['giveItems']):
        print(f'INFO Removed unknown item(s) in given items of schematic {schematics_name}')
    schematic['unlock']['giveItems'] = given_items
for recipe_name, recipe in data['recipes'].items():
    # filter recipe ingredients
    ingredients = filter_item_amounts(recipe['ingredients'])
    if len(ingredients) != len(recipe['ingredients']):
        print(f'INFO Removed unknown item(s) in ingredients of recipe {recipe_name}')
    recipe['ingredients'] = ingredients
    # filter recipe products
    products = filter_item_amounts(recipe['products'])
    if len(products) != len(recipe['products']):
        print(f'INFO Removed unknown item(s) in products of recipe {recipe_name}')
    recipe['products'] = products
for building_name, building in data['buildings'].items():
    # filter building costs
    costs = filter_item_amounts(building['costs'])
    if len(costs) != len(building['costs']):
        print(f'INFO Removed unknown item(s) in costs of building {building_name}')
    building['costs'] = costs

def get_bare_name(name: str) -> str:
    # remove _C
    name = name[:-2]
    # remove prefix
    name = '_'.join(name.split('_')[1:])
    return name

def create_machine_recipe(recipe_name: str, ingredients: list,
                          products: list, time: float, building_name: str):
    return {
        'name': get_bare_name(recipe_name),
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
        'manualTimeMultiplier': 1,
    }

# calculate required ingregients based on item energy value
def calc_input_rate(generator: dict, fuel_name: dict) -> float:
    fuel = data['items'][fuel_name]
    power_production = generator['powerProduction']
    energy_value_fuel = fuel['energyValue']
    # items are in liters but recipes use cubic meters
    if fuel['liquid']:
        energy_value_fuel *= 1000
    if energy_value_fuel == 0:
        raise ValueError('Fuel has no energy: ' + fuel['className'])
    # consumption per minute
    fuel_consumption = (
        power_production # MW/sec
        / energy_value_fuel # MW
        * 60 # sec
    )
    return fuel_consumption
# Power: For every generator and fuel add a recipe
for generator_name, generator in data['generators'].items():
    if generator_name == 'Desc_GeneratorGeoThermal_C':
        # empty recipe enables usage in parsing and sink point optim
        recipe_name = (f'Recipe_{get_bare_name(generator_name)}Power_C')
        data['recipes'][recipe_name] = create_machine_recipe(recipe_name, [], [],
                                                             60, generator_name)
        continue
    # consumption per minute
    water_consumption = (
        60 # unit: sec
        * generator['waterToPowerRatio'] # unit: liters/(sec * MW)
        * generator['powerProduction'] # unit: MW
    ) / 1000 # unit: cubic meters
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

        recipe_name = (f'Recipe_{get_bare_name(generator_name)}'
                        f'{get_bare_name(fuel_name)}_C')
        data['recipes'][recipe_name] = create_machine_recipe(recipe_name,
                                                             ingredients,
                                                             products,
                                                             60, generator_name)

# Extraction: For every building and every resource add a recipe
for extractor_build_name, extractor in data['miners'].items():
    
    for item_name in extractor['allowedResources']:
        recipe_name = ('Recipe_' + get_bare_name(extractor_build_name)
                       + get_bare_name(item_name) + '_C')
        amount = extractor['itemsPerCycle']
        # Liquid recipes are given in cubic meters
        if extractor['allowLiquids']:
            amount /= 1000
        products = [{'item': item_name,
                    'amount': amount}]
        cycle_time = extractor['extractCycleTime']
        
        building_name = extractor_build_name.replace('Build_', 'Desc_')
        data['recipes'][recipe_name] = create_machine_recipe(recipe_name, [], products,
                                                             cycle_time, building_name)

def create_handcraft_recipe(recipe_name: str, ingredients: list,
                          products: list, time: float):
    return {
        'name': get_bare_name(recipe_name),
        'className': recipe_name,
        'alternate': False,
        'time': time,
        'ingredients': ingredients,
        'forBuilding': False,
        'inMachine': False,
        'inHand': True, # abstract manual mining of resources to happen at the craft bench
        'inWorkshop': False,
        'products': products,
        'producedIn': [],
        'isVariablePower': False,
        'manualTimeMultiplier': 8, # neutralize the HANDCRAFT_CYCLE_MULTIPLIER
    }

# Handcraft extraction: Every solid resource can be collected or mined manually
for item_name, resource in data['resources'].items():
    if data['items'][item_name]['liquid']:
        continue
    recipe_name = f'Recipe_Handcraft{get_bare_name(item_name)}_C'
    products = [{'item': item_name, 'amount': 1}]
    data['recipes'][recipe_name] = create_handcraft_recipe(
        recipe_name,
        [],
        products,
        resource['speed'] # represents cycle time of manual action (digging, picking, hunting)
    )
    
# In schematics, filter unlocked recipes and unlocked buildings
for schematics_name, schematics in data['schematics'].items():
    schematics['unlock']['buildings'] = [
        PRODUCTION_BUILDING_RECIPES[recipe_name]
        for recipe_name in schematics['unlock']['recipes']
        if recipe_name in PRODUCTION_BUILDING_RECIPES
    ]
    schematics['unlock']['recipes'] = [
        recipe_name
        for recipe_name in schematics['unlock']['recipes']
        if recipe_name in data['recipes']
    ]

# Add recipes that only need unlocked building
for schematics_name, schematics in data['schematics'].items():
    # handcraft resources (TODO: Schematic_StartingRecipes_C is unlocked together with Schematic_Tutorial1_C. Why?)
    if schematics_name == 'Schematic_StartingRecipes_C':
        schematics['unlock']['recipes'].extend([
            f'Recipe_Handcraft{get_bare_name(item_name)}_C'
            for item_name in data['resources']
            if not data['items'][item_name]['liquid']
            ])
    # extractors
    for extractor_name in BUILDINGS_EXTRACTION:
        if extractor_name in schematics['unlock']['buildings']:
            schematics['unlock']['recipes'].extend([
                recipe_name
                for recipe_name, recipe in data['recipes'].items()
                if extractor_name in recipe['producedIn']
            ])
    # generators
    for generator_name in BUILDINGS_GENERATOR:
        if generator_name in schematics['unlock']['buildings']:
            schematics['unlock']['recipes'].extend([
                recipe_name
                for recipe_name, recipe in data['recipes'].items()
                if generator_name in recipe['producedIn']
            ])
    # alien power augmenter
    if 'Desc_AlienPowerBuilding_C' in schematics['unlock']['buildings']:
        schematics['unlock']['recipes'].append(
            'Recipe_AlienPowerBuildingAlienPowerFuel_C'
        )
    # converter
    if 'Desc_Converter_C' in schematics['unlock']['buildings']:
        schematics['unlock']['recipes'].extend([
            recipe_name
            for recipe_name, recipe in data['recipes'].items()
            if 'Desc_Converter_C' in recipe['producedIn']
        ])
    # Refinery
    if 'Desc_OilRefinery_C' in schematics['unlock']['buildings']:
        schematics['unlock']['recipes'].extend([
            'Recipe_ResidualFuel_C',
            'Recipe_ResidualPlastic_C',
            'Recipe_ResidualRubber_C'
        ])
    # Blender
    if 'Desc_Blender_C' in schematics['unlock']['buildings']:
        schematics['unlock']['recipes'].append(
            'Recipe_Alternate_Silica_Distilled_C'
        )
    # Packager
    if 'Desc_Packager_C' in schematics['unlock']['buildings']:
        schematics['unlock']['recipes'].extend([
            'Recipe_UnpackageAlumina_C',
            'Recipe_UnpackageBioFuel_C',
            'Recipe_UnpackageFuel_C',
            'Recipe_UnpackageNitricAcid_C',
            'Recipe_UnpackageNitrogen_C',
            'Recipe_UnpackageOilResidue_C',
            'Recipe_UnpackageOil_C',
            'Recipe_UnpackageSulfuricAcid_C',
            'Recipe_UnpackageWater_C'
        ])
    # Fix hidden research
    if schematics_name == 'Research_Sulfur_5_2_C':
        schematics['unlock']['recipes'].append('Recipe_CartridgeChaos_Packaged_C')

with open(DATA_PATH_EXPORT, 'w') as fp:
    json.dump(data, fp, indent='\t')
