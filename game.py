import json

with open('data.json', 'r') as fp:
    data = json.load(fp)

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
    'Desc_Wood_C'
    }
    return {
        item_name:v for item_name,v in data['items'].items()
        if (
            'Desc_' in item_name and
            type(v['sinkPoints']) == int and # allow products with 0 sink points to not discard intermediate products
            not 'Packaged' in item_name and
            item_name in item_names and
            not item_name in manual_items
        )    
    }
ITEMS = define_items()


def transform_to_dict(items: list):
    return {
        d['item']: d['amount']
        for d in items
    }

# Make water available unlimited
def remove_water(items: dict):
    if 'Desc_Water_C' in items:
        items.pop('Desc_Water_C')
    return items

# recipes are limited to available items
# note that water is removed from recipe as unlimited availability
def define_recipes():
    recipes = {
        recipe_name: (
            remove_water(transform_to_dict(v['ingredients'])),
            remove_water(transform_to_dict(v['products'])),
        )
        for recipe_name, v in data['recipes'].items()
        if (
            all(d['item'] in ITEMS for d in v['ingredients']) and
            all(d['item'] in ITEMS for d in v['products'])
        )
    }
    # hard coded fix to enable nuclear production chain
    recipes['Desc_GeneratorNuclearUranium_C'] = (
        {'Desc_NuclearFuelRod_C': 1}, {'Desc_NuclearWaste_C': 250}
    )
    recipes['Desc_GeneratorNuclearPlutonium_C'] = (
        {'Desc_PlutoniumFuelRod_C': 1}, {'Desc_PlutoniumWaste_C': 100}
    )
    return recipes
RECIPES = define_recipes()

# resources are items that can not be produced by recipes
def get_resources():
    items_produced = set()
    items_ingredients = set()
    for ingredients, products in RECIPES.values():
        items_produced = items_produced.union(products.keys())
        items_ingredients = items_ingredients.union(ingredients.keys())
    return set(ITEMS.keys()) - items_produced
NON_PRODUCABLE_ITEMS = get_resources()

# resources that are available by building extractors
RESOURCES_AVAILABLE = dict()
RESOURCES_AVAILABLE['Desc_Stone_C'] = 480*27 + 240*47 + 120*12
RESOURCES_AVAILABLE['Desc_OreIron_C'] = 480*46 + 240*41 + 120*33
RESOURCES_AVAILABLE['Desc_OreCopper_C'] = 480*12 + 240*28 + 120*9
RESOURCES_AVAILABLE['Desc_OreGold_C'] = 480*8 + 240*8
RESOURCES_AVAILABLE['Desc_Coal_C'] = 480*14 + 240*29 + 120*6
RESOURCES_AVAILABLE['Desc_LiquidOil_C'] = 240*8 + 120*12 + 60*10
RESOURCES_AVAILABLE['Desc_Sulfur_C'] = 480*3 + 240*7 + 120*1
RESOURCES_AVAILABLE['Desc_OreBauxite_C'] = 480*6 + 240*6 + 120*5
RESOURCES_AVAILABLE['Desc_RawQuartz_C'] = 480*5 + 240*11
RESOURCES_AVAILABLE['Desc_OreUranium_C'] = 240*3 + 120*1
RESOURCES_AVAILABLE['Desc_NitrogenGas_C'] = 2*30 + 7*60 + 36*120
RESOURCES_AVAILABLE['Desc_LiquidOil_C'] = 6*60 + 3*120 + 3*240

# helper structure to find recipes
def define_item_to_recipe_mappings():
    consumed_by = { item_name: [] for item_name in ITEMS}
    produced_by = { item_name: [] for item_name in ITEMS}
    for recipe_name, data in RECIPES.items():
        items_in, items_out = data
        for item_name in items_in:
            consumed_by[item_name].append(recipe_name)
        for item_name in items_out:
            produced_by[item_name].append(recipe_name)
    return consumed_by, produced_by
consumed_by, produced_by = define_item_to_recipe_mappings()
