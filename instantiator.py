from typing import Dict, List

from data_types import *
import game


COMPONENT_TYPE = 0
ACTOR_TYPE = 1


############################### Buildable #####################################


def get_args_for_actor(obj: dict, components: Dict[str,dict]) -> dict:
    if obj['object_type'] != ACTOR_TYPE:
        raise ValueError('Expect actor')
    kwargs = dict()
    kwargs['instance_name'] = obj['instance_name']
    kwargs['type_path'] = obj['type_path']
    return kwargs


def create_actor(obj: dict, components: Dict[str,dict]) -> Actor:
    return Actor(**get_args_for_actor(obj, components))


############################### Buildable #####################################


def get_args_for_buildable(obj: dict, components: Dict[str,dict]) -> dict:
    kwargs = get_args_for_actor(obj, components)
    transform = (
        obj["pos_x"],
        obj["pos_y"],
        obj["pos_z"],
        obj["rot_x"],
        obj["rot_y"],
        obj["rot_z"],
        obj["rot_w"],
    )
    kwargs['transform'] = transform
    if 'mBuiltWithRecipe' in obj['properties']:
        kwargs['build_with_recipe'] = obj['properties']['mBuiltWithRecipe']['path_name'],
    # TODO: swatch_slot=obj['properties']['mCustomizationData']['payload']
    return kwargs


def create_buildable(obj: dict, components: Dict[str,dict]) -> Buildable:
    kwargs = get_args_for_buildable(obj, components)
    return Buildable(**kwargs)


############################### Factory #######################################


def get_args_for_factory(obj: dict, components: Dict[str,dict]) -> dict:
    kwargs = get_args_for_buildable(obj, components)
    prop = obj['properties']
    if 'mProductivityMonitorEnabled' in prop:
        kwargs['is_productivity_monitor_enabled'] = prop['mProductivityMonitorEnabled']['value']
        if kwargs['is_productivity_monitor_enabled']:
        # TODO: only if enabled=True?
            kwargs['current_productivity_measurement_duration'] = prop['mCurrentProductivityMeasurementDuration']['value']
            if 'mCurrentProductivityMeasurementProduceDuration' in prop:
                kwargs['current_productivity_measurement_produce_duration'] = prop['mCurrentProductivityMeasurementProduceDuration']['value']
            else:
                # in case the power is shutdown TODO: check otherwise
                kwargs['current_productivity_measurement_produce_duration'] = 0

    if 'mPendingPotential' in prop:
        kwargs['pending_potential'] = prop['mPendingPotential']['value']
    if 'mIsProducing' in prop:
        kwargs['is_producing'] = prop['mIsProducing']['value']
    if 'mIsProductionPaused' in prop:
        kwargs['is_production_paused'] = prop['mIsProductionPaused']['value']
    if 'mCurrentManufacturingProgress' in prop:
        kwargs['current_manufacturing_progress'] = prop['mCurrentManufacturingProgress']
    elif 'mCurrentExtractProgress' in prop:
        kwargs['current_manufacturing_progress'] = prop['mCurrentExtractProgress']['value']
    # power_info = components[prop['mPowerInfo']['path_name']]
    # if 'mTargetConsumption' in power_info['properties']:
    #     kwargs['power_consumption'] = power_info['properties']['mTargetConsumption']['value']
    # elif 'mDynamicProductionCapacity' in power_info['properties']:
    #     kwargs['power_consumption'] = -power_info['properties']['mDynamicProductionCapacity']['value']
    return kwargs
       

def create_factory(obj: dict, components: Dict[str,dict]) -> Factory:
    if obj['object_type'] != ACTOR_TYPE:
        raise ValueError('Expect actor')
    kwargs = get_args_for_factory(obj, components)
    return Factory(**kwargs)


############################### ManufacturingBuilding #########################


def create_inventory_stack(item_desc: dict, stack: dict) -> ItemStack:
    if item_desc['path_name'] == '': # when 
        return ItemStack('', 0, 0)
    item_name = item_desc['path_name'].split('.')[-1]
    if not item_name in game.ITEMS:
        print('WARNING Skip unknown item:',  item_name)
        return ItemStack('', 0, 0)
    amount = stack['properties']['NumItems']['value']
    capacity = game.ITEMS[item_name]['stackSize']
    return ItemStack(item_name=item_name, amount=amount, capacity=capacity)


def create_inventory_stacks(component: dict) -> List[ItemStack]:
    if component['object_type'] != COMPONENT_TYPE:
        raise ValueError('Expect component')
    prop = component['properties']
    item_descriptors = prop['mAllowedItemDescriptors']['elements']
    if not 'mInventoryStacks' in component['properties']:
        # TODO: Why does Miner not have mInventoryStacks member?
        stacks = [{'properties': {'NumItems': {'value': 0}}}] * len(item_descriptors)
    else:
        stacks = component['properties']['mInventoryStacks']['elements']
        if len(item_descriptors) != len(stacks):
            raise ValueError
    # TODO: Why does OutputInventory have extra FGItemDesciptor stack?
    return [
        create_inventory_stack(item_desc, stack)
        for item_desc, stack in zip(item_descriptors, stacks)
        if not 'FGItemDescriptor' in item_desc['path_name']
    ]


def get_args_for_manufacturing_building(obj: dict, components: Dict[str,dict]
                                        ) -> dict:
    kwargs = get_args_for_factory(obj, components)
    prop = obj['properties']
    if 'mCurrentRecipe' in prop:
        kwargs['current_recipe_name'] = prop['mCurrentRecipe']['path_name'].split('.')[-1]
    input_inventory_component = components[prop['mInputInventory']['path_name']]
    kwargs['input_inventory_stacks'] = create_inventory_stacks(input_inventory_component)
    output_inventory_component = components[prop['mOutputInventory']['path_name']]
    kwargs['output_inventory_stacks'] = create_inventory_stacks(output_inventory_component)
    return kwargs


def create_manufacturing_building(obj: dict, components: Dict[str,dict]
                                  ) -> ManufacturingBuilding:
    if obj['object_type'] != ACTOR_TYPE:
        raise ValueError('Expect actor')
    kwargs = get_args_for_manufacturing_building(obj, components)
    return ManufacturingBuilding(**kwargs)


############################### FrackingBuilding ##############################


def get_args_for_fracking_building(obj: dict, components: Dict[str,dict]
                                   ) -> dict:
    kwargs = get_args_for_factory(obj, components)
    prop = obj['properties']
    output_inventory_component = components[prop['mOutputInventory']['path_name']]
    kwargs['output_inventory_stacks'] = create_inventory_stacks(output_inventory_component)
    if not any(len(item_stack.item_name) > 0 for item_stack in kwargs['output_inventory_stacks']):
        raise ValueError('Could not detect resource from output intentory. Data: ' + str(obj['properties']))
    # TODO: Get resource from lookup table
    # kwargs['resource_name'] = prop['mExtractableResource']['path_name'] # e.g. "....BP_ResourceNode115"
    kwargs['resource_name'] = [
        item_stack
        for item_stack in kwargs['output_inventory_stacks']
        if len(item_stack.item_name) > 0][0].item_name
    factory_build_recipe = obj['properties']['mBuiltWithRecipe']['path_name'].split('.')[-1]
    if 'Miner' in factory_build_recipe:
        insert_idx = factory_build_recipe.find('Miner') + len('MinerMkX')
        recipe_name = (factory_build_recipe[:insert_idx]
                       + game.get_bare_item_name(kwargs['resource_name'])
                       + factory_build_recipe[insert_idx:])
    elif factory_build_recipe.endswith('Recipe_WaterPump_C'):
        recipe_name = 'Recipe_WaterPumpWater_C'
    elif factory_build_recipe.endswith('Recipe_OilPump_C'):
        recipe_name = 'Recipe_OilPumpLiquidOil_C'
    else:
        raise NotImplementedError(str(factory_build_recipe))
    kwargs['current_recipe_name'] = recipe_name
    return kwargs


def create_fracking_building(obj: dict, components: Dict[str,dict]
                             ) -> FrackingBuilding:
    if obj['object_type'] != ACTOR_TYPE:
        raise ValueError('Expect actor')
    kwargs = get_args_for_fracking_building(obj, components)
    return FrackingBuilding(**kwargs)


############################## Game Progression ###############################


def extract_item_amounts(item_amount_elems: List[dict]) -> Dict[str, int]:
    item_amounts = dict()
    for item in item_amount_elems:
        item_name = item['prop']['path_name'].split('.')[-1]
        amount = item['properties']['Amount']['value']
        item_amounts[item_name] = amount
    return item_amounts


def extract_paid_off_schematics(paid_offs: List[dict]) -> Dict[str, Dict[str, int]]:
    payoffs = dict()
    for elem in paid_offs:
        schematic_name = elem['prop']['path_name'].split('.')[-1]
        item_amounts = extract_item_amounts(elem['properties']['ItemCost']['elements'])
        payoffs[schematic_name] = item_amounts
    return payoffs


def get_args_for_schematic_manager(obj: dict, components: Dict[str,dict]
                                   ) -> dict:
    kwargs = get_args_for_actor(obj, components)
    prop = obj['properties'] 
    if 'mPurchasedSchematics' in prop:
        kwargs['purchased_schematics'] = [
            elem['path_name'].split('.')[-1]
            for elem in prop['mPurchasedSchematics']['elements']
        ]
    if 'mPaidOffSchematic' in prop:
        paid_offs = prop['mPaidOffSchematic']['elements']
        kwargs['costs_paid_off'] = extract_paid_off_schematics(paid_offs)
    if 'mActiveSchematic' in prop:
        kwargs['active_schematic'] = prop['mActiveSchematic']['path_name'].split('.')[-1]
    return kwargs


def create_schematic_manager(obj: dict, components: Dict[str,dict]
                             ) -> SchematicManager:
    kwargs = get_args_for_schematic_manager(obj, components)
    return SchematicManager(**kwargs)


def get_args_for_game_phase_manager(obj: dict, components: Dict[str,dict]
                                    ) -> dict:
    kwargs = get_args_for_actor(obj, components)
    prop = obj['properties']
    if 'mTargetGamePhase' in prop:
        active_phase_name = prop['mTargetGamePhase']['path_name'].split('.')[-1]
        if not active_phase_name.endswith('_C'):
            active_phase_name = active_phase_name + '_C'
        kwargs['active_phase'] = active_phase_name
    if 'mTargetGamePhasePaidOffCosts' in prop:
        item_amount_elems = prop['mTargetGamePhasePaidOffCosts']['elements']
        kwargs['costs_paid_off'] = extract_item_amounts(item_amount_elems)
    return kwargs


def create_game_phase_manager(obj: dict, components: Dict[str,dict]
                              ) -> GamePhaseManager:
    kwargs = get_args_for_game_phase_manager(obj, components)
    return GamePhaseManager(**kwargs)


############################### main ##########################################


INSTANTIATION_FUNCTION = {
    # Fracking
    '/Game/FactoryGame/Buildable/Factory/MinerMK1/Build_MinerMk1.Build_MinerMk1_C': 
        create_fracking_building,
    '/Game/FactoryGame/Buildable/Factory/MinerMK2/Build_MinerMk2.Build_MinerMk2_C':
        create_fracking_building,
    '/Game/FactoryGame/Buildable/Factory/MinerMK3/Build_MinerMk2.Build_MinerMk3_C':
        create_fracking_building,
    '/Game/FactoryGame/Buildable/Factory/OilPump/Build_OilPump.Build_OilPump_C':
        create_fracking_building,
    '/Game/FactoryGame/Buildable/Factory/WaterPump/Build_WaterPump.Build_WaterPump_C':
        create_fracking_building,
    # TODO: ResourceWellPressurizer

    # Manufacturing
    '/Game/FactoryGame/Buildable/Factory/SmelterMk1/Build_SmelterMk1.Build_SmelterMk1_C':
        create_manufacturing_building,
    '/Game/FactoryGame/Buildable/Factory/FoundryMk1/Build_FoundryMk1.Build_FoundryMk1_C':
        create_manufacturing_building,
    '/Game/FactoryGame/Buildable/Factory/ConstructorMk1/Build_ConstructorMk1.Build_ConstructorMk1_C':
        create_manufacturing_building,
    '/Game/FactoryGame/Buildable/Factory/AssemblerMk1/Build_AssemblerMk1.Build_AssemblerMk1_C':
        create_manufacturing_building,
    '/Game/FactoryGame/Buildable/Factory/ManufacturerMk1/Build_ManufacturerMk1.Build_ManufacturerMk1_C':
        create_manufacturing_building,
    '/Game/FactoryGame/Buildable/Factory/OilRefinery/Build_OilRefinery.Build_OilRefinery_C':
        create_manufacturing_building,
    '/Game/FactoryGame/Buildable/Factory/Blender/Build_Blender.Build_Blender_C':
        create_manufacturing_building,
    '/Game/FactoryGame/Buildable/Factory/Packager/Build_Packager.Build_Packager_C':
        create_manufacturing_building,
    '/Game/FactoryGame/Buildable/Factory/HadronCollider/Build_HadronCollider.Build_HadronCollider_C':
        create_manufacturing_building,
    # TODO: Release update

    '/Game/FactoryGame/Schematics/Progression/BP_SchematicManager.BP_SchematicManager_C':
        create_schematic_manager,
    '/Game/FactoryGame/Schematics/Progression/BP_GamePhaseManager.BP_GamePhaseManager_C':
        create_game_phase_manager,
}


def instantiate_world(objects: List[dict]) -> World:
    # assign components
    components = dict()
    for o in objects:
        if o['object_type'] == COMPONENT_TYPE:
            components[o['instance_name']] = o
    
    # create actors
    actors = []
    missed_types = set()
    for o in objects:
        if not o['type_path'] in INSTANTIATION_FUNCTION:
            missed_types.add(o['type_path'])
            continue
        actor_components = {
            component_ref['path_name']: components[component_ref['path_name']]
            for component_ref in o['components']
        }
        func = INSTANTIATION_FUNCTION[o['type_path']]
        try:
            actor = func(o, actor_components)
        except Exception as e:
            from pprint import pprint
            pprint(o)
            raise e
        actors.append(actor)

    # guide implementation
    missed_facilities = {t.split('.')[-1]: t for t in missed_types}
    for facility_name in set(missed_facilities).intersection(set(game.PRODUCTION_FACILITIES)):
        print('WARNING Missed types:', missed_facilities[facility_name])

    return World(actors=actors)
