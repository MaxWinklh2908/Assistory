import json

with open('data.json', 'r') as fp:
    data = json.load(fp)

def get_bare_item_name(name: str) -> str:
    # remove _C
    name = name[:-2]
    # remove prefix
    name = '_'.join(name.split('_')[1:])
    return name

def define_items():
    item_names = {
    "Desc_AluminaSolution_C",
    "Desc_AluminumCasing_C",
    "Desc_AluminumIngot_C",
    "Desc_AluminumPlateReinforced_C",
    "Desc_AluminumPlate_C",
    "Desc_AluminumScrap_C",
    "Desc_Battery_C",
    "Desc_Berry_C",
    "Desc_Biofuel_C",
    "Desc_Cable_C",
    "Desc_CartridgeStandard_C",
    "Desc_Cement_C",
    "Desc_Chainsaw_C",
    "Desc_CircuitBoardHighSpeed_C",
    "Desc_CircuitBoard_C",
    "Desc_Coal_C",
    "Desc_ColorCartridge_C",
    "Desc_CompactedCoal_C",
    "Desc_ComputerSuper_C",
    "Desc_Computer_C",
    "Desc_CoolingSystem_C",
    "Desc_CopperDust_C",
    "Desc_CopperIngot_C",
    "Desc_CopperSheet_C",
    "Desc_CrystalOscillator_C",
    "Desc_CrystalShard_C",
    "Desc_Crystal_C",
    "Desc_Crystal_mk2_C",
    "Desc_Crystal_mk3_C",
    "Desc_ElectromagneticControlRod_C",
    "Desc_Fabric_C",
    "Desc_Filter_C",
    "Desc_Fireworks_Projectile_01_C",
    "Desc_Fireworks_Projectile_02_C",
    "Desc_Fireworks_Projectile_03_C",
    "Desc_FlowerPetals_C",
    "Desc_FluidCanister_C",
    "Desc_Fuel_C",
    "Desc_GasTank_C",
    "Desc_GenericBiomass_C",
    "Desc_GoldIngot_C",
    "Desc_GolfCartGold_C",
    "Desc_GolfCart_C",
    "Desc_Gunpowder_C",
    "Desc_HUBParts_C",
    "Desc_HazmatFilter_C",
    "Desc_HeavyOilResidue_C",
    "Desc_HighSpeedConnector_C",
    "Desc_HighSpeedWire_C",
    "Desc_HogParts_C",
    "Desc_IronIngot_C",
    "Desc_IronPlateReinforced_C",
    "Desc_IronPlate_C",
    "Desc_IronRod_C",
    "Desc_IronScrew_C",
    "Desc_Leaves_C",
    "Desc_LiquidBiofuel_C",
    "Desc_LiquidFuel_C",
    "Desc_LiquidOil_C",
    "Desc_LiquidTurboFuel_C",
    "Desc_Medkit_C",
    "Desc_ModularFrameFused_C",
    "Desc_ModularFrameHeavy_C",
    "Desc_ModularFrameLightweight_C",
    "Desc_ModularFrame_C",
    "Desc_MotorLightweight_C",
    "Desc_Motor_C",
    "Desc_Mycelia_C",
    "Desc_NitricAcid_C",
    "Desc_NitrogenGas_C",
    "Desc_NobeliskExplosive_C",
    "Desc_NonFissibleUranium_C",
    "Desc_NuclearFuelRod_C",
    "Desc_NuclearWaste_C",
    "Desc_Nut_C",
    "Desc_OreBauxite_C",
    "Desc_OreCopper_C",
    "Desc_OreGold_C",
    "Desc_OreIron_C",
    "Desc_OreUranium_C",
    "Desc_PackagedAlumina_C",
    "Desc_PackagedBiofuel_C",
    "Desc_PackagedNitricAcid_C",
    "Desc_PackagedNitrogenGas_C",
    "Desc_PackagedOilResidue_C",
    "Desc_PackagedOil_C",
    "Desc_PackagedSulfuricAcid_C",
    "Desc_PackagedWater_C",
    "Desc_Parachute_C",
    "Desc_PetroleumCoke_C",
    "Desc_Plastic_C",
    "Desc_PlutoniumCell_C",
    "Desc_PlutoniumFuelRod_C",
    "Desc_PlutoniumPellet_C",
    "Desc_PlutoniumWaste_C",
    "Desc_PolymerResin_C",
    "Desc_PressureConversionCube_C",
    "Desc_QuartzCrystal_C",
    "Desc_RawQuartz_C",
    "Desc_RebarGunProjectile_C",
    "Desc_ResourceSinkCoupon_C",
    "Desc_Rotor_C",
    "Desc_Rubber_C",
    "Desc_Shroom_C",
    "Desc_Silica_C",
    "Desc_SpaceElevatorPart_1_C",
    "Desc_SpaceElevatorPart_2_C",
    "Desc_SpaceElevatorPart_3_C",
    "Desc_SpaceElevatorPart_4_C",
    "Desc_SpaceElevatorPart_5_C",
    "Desc_SpaceElevatorPart_6_C",
    "Desc_SpaceElevatorPart_7_C",
    "Desc_SpaceElevatorPart_8_C",
    "Desc_SpaceElevatorPart_9_C",
    "Desc_SpikedRebar_C",
    "Desc_SpitterParts_C",
    "Desc_Stator_C",
    "Desc_SteelIngot_C",
    "Desc_SteelPipe_C",
    "Desc_SteelPlateReinforced_C",
    "Desc_SteelPlate_C",
    "Desc_Stone_C",
    "Desc_Sulfur_C",
    "Desc_SulfuricAcid_C",
    "Desc_TurboFuel_C",
    "Desc_UraniumCell_C",
    "Desc_Water_C",
    "Desc_Wire_C",
    "Desc_Wood_C",
    }
    manual_items = {
    'Desc_Berry_C',
    'Desc_CartridgeStandard_C',
    'Desc_Crystal_C',
    'Desc_Crystal_mk2_C',
    'Desc_Crystal_mk3_C',
    'Desc_FlowerPetals_C',
    'Desc_HUBParts_C',
    'Desc_HogParts_C',
    'Desc_Leaves_C',
    'Desc_Mycelia_C',
    'Desc_Nut_C',
    'Desc_ResourceSinkCoupon_C',
    'Desc_Shroom_C',
    'Desc_SpitterParts_C',
    'Desc_Wood_C',
    'Desc_Chainsaw_C',
    # 'Desc_Water_C', # removed as unlimited availability
    'Desc_Medkit_C',
    'Desc_Biofuel_C',
    'Desc_GolfCartGold_C',
    'Desc_GolfCart_C',
    'Desc_LiquidBiofuel_C',
    }
    return {
        item_name:v for item_name,v in data['items'].items()
        if (
            item_name in item_names and not item_name in manual_items and
            type(v['sinkPoints']) == int # allow products with 0 sink points to not discard intermediate products
        )    
    }
ITEMS = define_items()

def define_non_sellable_items():
    return {
        item_name: item_data
        for item_name, item_data in ITEMS.items()
        if item_data['sinkPoints'] == 0
    }
NON_SELLABLE_ITEMS = define_non_sellable_items()

# # resources that are available by building extractors
# RESOURCES_AVAILABLE = dict()
# RESOURCES_AVAILABLE['Desc_LiquidOil_C'] =      (240, 8, 120, 12, 60, 10 )
# RESOURCES_AVAILABLE['Desc_Stone_C'] =          (480, 27, 240, 47, 120,12)
# RESOURCES_AVAILABLE['Desc_OreIron_C'] =        (480, 46, 240, 41, 120, 33)
# RESOURCES_AVAILABLE['Desc_OreCopper_C'] =      (480, 12, 240, 28, 120, 9)
# RESOURCES_AVAILABLE['Desc_OreGold_C'] =        (480, 8, 240, 8, 120, 0)
# RESOURCES_AVAILABLE['Desc_Coal_C'] =           (480, 14, 240, 29, 120, 6)
# RESOURCES_AVAILABLE['Desc_Sulfur_C'] =         (480, 3, 240, 7, 120, 1)
# RESOURCES_AVAILABLE['Desc_OreBauxite_C'] =     (480, 6, 240, 6, 120, 5)
# RESOURCES_AVAILABLE['Desc_RawQuartz_C'] =      (480, 5, 240, 11, 120, 0)
# RESOURCES_AVAILABLE['Desc_OreUranium_C'] =     (480, 0, 240, 3, 120,1)
# RESOURCES_AVAILABLE['Desc_NitrogenGas_C'] =    (30, 2, 60, 7, 120, 36)
# RESOURCES_AVAILABLE['Desc_LiquidOil_C'] =      (60, 6, 120, 3, 240, 3)

NODES_AVAILABLE = dict()
NODES_AVAILABLE['Desc_MinerMk3Stone_C'] =                       (2 * 27 + 47 + 0.5 * 12)
NODES_AVAILABLE['Desc_MinerMk3OreIron_C'] =                     (2 * 46 + 41 + 0.5 * 33)
NODES_AVAILABLE['Desc_MinerMk3OreCopper_C'] =                   (2 * 12 + 28 + 0.5 * 9)
NODES_AVAILABLE['Desc_MinerMk3OreGold_C'] =                     (2 * 8 + 8 + 0.5 * 0)
NODES_AVAILABLE['Desc_MinerMk3Coal_C'] =                        (2 * 14 + 29 + 0.5 * 6)
NODES_AVAILABLE['Desc_MinerMk3Sulfur_C'] =                      (2 * 3 + 7 + 0.5 * 1)
NODES_AVAILABLE['Desc_MinerMk3OreBauxite_C'] =                  (2 * 6 + 6 + 0.5 * 5)
NODES_AVAILABLE['Desc_MinerMk3RawQuartz_C'] =                   (2 * 5 + 11 + 0.5 * 0)
NODES_AVAILABLE['Desc_MinerMk3OreUranium_C'] =                  (2 * 0 + 3 + 0.5 * 1)
NODES_AVAILABLE['Desc_OilExtractorLiquidOil_C'] =               (2 * 8 + 12 + 0.5 * 10)
NODES_AVAILABLE['Desc_ResourceWellPressurizerNitrogenGas_C'] =  (2 * 36 + 7 + 0.5 * 2)
NODES_AVAILABLE['Desc_ResourceWellPressurizerLiquidOil_C'] =    (2 * 63 + 3 + 0.5 * 6)

# recipes are limited to available items
def define_recipes():
    def transform_to_dict(items: list):
        return {
            d['item']: d['amount']
            for d in items
        }
    recipes = dict()
    for recipe_name, v in data['recipes'].items():
        if len(v['producedIn']) != 1:
            # print('WARNING Skip handcrafted:', recipe_name)
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
        if not ingredients or not products:
            print('WARNING Skip unavailable:', recipe_name)
            continue
        recipes[recipe_name] = {
            'ingredients': ingredients,
            'products': products,
            'producedIn': v['producedIn'][0]
        }
    # hard coded fix to enable nuclear production chain
    recipes['Desc_GeneratorNuclearUranium_C'] = {
        'ingredients': {'Desc_NuclearFuelRod_C': 0.2},
        'products': {'Desc_NuclearWaste_C': 50},
        'producedIn': 'Desc_GeneratorNuclear_C',
    }
    recipes['Desc_GeneratorNuclearPlutonium_C'] = {
        'ingredients': {'Desc_PlutoniumFuelRod_C': 0.1},
        'products': {'Desc_PlutoniumWaste_C': 10},
        'producedIn': 'Desc_GeneratorNuclear_C',
    }
    # enable power from coal
    recipes['Desc_GeneratorCoalCoal_C'] = {
        
        'ingredients': {'Desc_Coal_C': 15},
        'products': {},
        'producedIn': 'Desc_GeneratorCoal_C',
    }
    recipes['Desc_GeneratorCoalCompactedCoal_C'] = {
        
        'ingredients': {'Desc_CompactedCoal_C': 7.142857},
        'products': {},
        'producedIn': 'Desc_GeneratorCoal_C',
    }
    recipes['Desc_GeneratorCoalPetroleumCoke_C'] = {
        
        'ingredients': {'Desc_PetroleumCoke_C': 25},
        'products': {},
        'producedIn': 'Desc_GeneratorCoal_C',
    }
    # enable power from fuel
    recipes[f'Desc_GeneratorFuelLiquidFuel_C'] = {
        'ingredients': {'Desc_LiquidFuel_C': 12},
        'products': {},
        'producedIn': 'Desc_GeneratorFuel_C',
    }
    recipes[f'Desc_GeneratorFuelLiquidTurboFuel_C'] = {
        'ingredients': {'Desc_LiquidTurboFuel_C': 4.5},
        'products': {},
        'producedIn': 'Desc_GeneratorFuel_C',
    }
    # Water Extractor
    recipes['Desc_WaterExtractorWater_C'] = {
        
        'ingredients': {},
        'products': {'Desc_Water_C': 120},
        'producedIn': 'Desc_WaterExtractor_C',
    }
    # Oil extractor
    recipes[f'Desc_OilExtractorLiquidOil_C'] = {
        'ingredients': {},
        'products': {'Desc_LiquidOil_C': 120},
        'producedIn': 'Desc_OilExtractor_C',
    }
    # Add miners
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
        recipes[f'Desc_MinerMk3{get_bare_item_name(item_name)}_C'] = {
            'ingredients': {},
            'products': {item_name: 240},
            'producedIn': 'Desc_MinerMk3_C',
        }
    # Resource wells
    for item_name in [
        'Desc_NitrogenGas_C',
        'Desc_LiquidOil_C',
    ]:
        recipes[f'Desc_ResourceWellPressurizer{get_bare_item_name(item_name)}_C'] = {
            'ingredients': {},
            'products': {item_name: 60},
            'producedIn': 'Desc_ResourceWellPressurizer_C',
        }
    return recipes
RECIPES = define_recipes()
# TODO: Flip-Flop remove items and recipes that can't be automatically produced


# resources are items that can not be produced by recipes
def get_non_producable():
    items_produced = set()
    for data in RECIPES.values():
        items_produced = items_produced.union(data['products'].keys())
    return set(ITEMS.keys()) - items_produced
NON_PRODUCABLE_ITEMS = get_non_producable()


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
PRODUCTION_FACILITIES = define_production_facilities()

FREE_POWER = 3*100 + 9*200 + 6*400
