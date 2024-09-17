from typing import Dict, List

from data_types import *
import game


COMPONENT_TYPE = 0
ACTOR_TYPE = 1


############################### Buildable #####################################


def get_args_for_buildable(obj: dict, components: Dict[str,dict]) -> dict:
    kwargs = dict()
    transform = (
        obj["pos_x"],
        obj["pos_y"],
        obj["pos_z"],
        obj["rot_x"],
        obj["rot_y"],
        obj["rot_z"],
        obj["rot_w"],
    )
    kwargs['instance_name'] = obj['instance_name']
    kwargs['type_path'] = obj['type_path']
    kwargs['transform'] = transform
    if 'mBuiltWithRecipe' in obj['properties']:
        kwargs['build_with_recipe'] = obj['properties']['mBuiltWithRecipe']['path_name'],
    # TODO: swatch_slot=obj['properties']['mCustomizationData']['payload']
    return kwargs


def create_buildable(obj: dict, components: Dict[str,dict]) -> Buildable:
    if obj['object_type'] != ACTOR_TYPE:
        raise ValueError('Expect actor')
    return Buildable(**get_args_for_buildable(obj, components))


############################### Factory #######################################


def get_args_for_factory(obj: dict, components: Dict[str,dict]) -> dict:
    kwargs = get_args_for_buildable(obj, components)
    prop = obj['properties']
    if 'mProductivityMonitorEnabled' in prop:
        kwargs['is_productivity_monitor_enabled'] = prop['mProductivityMonitorEnabled']['value']
        if kwargs['is_productivity_monitor_enabled']:
        # TODO: only if enabled=True?
            kwargs['current_productivity_measurement_duration'] = prop['mCurrentProductivityMeasurementDuration']['value']
            kwargs['current_productivity_measurement_produce_duration'] = prop['mCurrentProductivityMeasurementProduceDuration']['value']
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
    return kwargs


def create_fracking_building(obj: dict, components: Dict[str,dict]
                             ) -> FrackingBuilding:
    if obj['object_type'] != ACTOR_TYPE:
        raise ValueError('Expect actor')
    kwargs = get_args_for_fracking_building(obj, components)
    return FrackingBuilding(**kwargs)


############################### main ##########################################


BUILDABLE_INSTANTIATION_FUNCTION = {
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
        if o['object_type'] == ACTOR_TYPE:
            if not o['type_path'] in BUILDABLE_INSTANTIATION_FUNCTION:
                missed_types.add(o['type_path'])
                continue
            actor_components = {
                component_ref['path_name']: components[component_ref['path_name']]
                for component_ref in o['components']
            }
            func = BUILDABLE_INSTANTIATION_FUNCTION[o['type_path']]
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

    return World(buildables=actors)
